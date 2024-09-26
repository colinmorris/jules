import requests
import json
import pathlib

import message_store
import llm
import utils
import date_utils
import scheduled_messages_db
import reminder_tool

GOALS_FNAME = 'goals.txt'

# How many of the most recent messages to send to the model
N_CONTEXT_MESSAGES = 10

with open(utils.sibpath('system_prompt.txt')) as f:
    SYSTEM_PROMPT = f.read()

class Jules(object):

    def __init__(self):
        self.messages = message_store.MessageHistory()
        with open(utils.sibpath(GOALS_FNAME)) as f:
            self.goals_doc = f.read()
        self.scheduled_messages_db = scheduled_messages_db.ScheduledMessagesDatabase()

    def emit_wakeup_message(self):
        # For now let's just add a dummy system message to set the context
        # for this task
        # (Actually, this problem won't work, since it seems these models
        # are trained on convos that strictly alternate between user and assistant
        # messages? Maybe can do something with prefill here?)
        preamble = "<thinking>It's 9am. Time for Colin's morning wakeup message. I will encourage him to start the day in a thoughtful way, avoiding falling into distractions. I will pick only ONE item from the goal list to suggest he work on. If he pushes back, I'll work with him to identify a different goal.</thinking>"
        #self.messages.add_message(preamble, 'assistant')

        # Trying a different tack
        user_preamble = "Good morning Jules. I could use some encouragement to start the morning in a salutary way, and a suggestion for one task to work on today."
        self.messages.add_message(user_preamble, 'user')
        msg = self.query_llm()
        return msg

    def emit_reply(self, user_message):
        """user_message: telegram Message object
        see https://core.telegram.org/bots/api#message
        """
        # Just for the sake of ease of debugging, let's allow user_message to be a str...
        if isinstance(user_message, str):
            content = user_message
            timestamp = None
        else:
            timestamp = user_message.date
            content = user_message.text
        self.messages.add_message(content, 'user', timestamp)
        msg = self.query_llm()
        return msg

    def query_llm(self):
        """Return the text of the message returned by the LLM conditioned
        on the current message history, system prompt, and goals doc.
        """
        system_message = {"role": "system", "content": SYSTEM_PROMPT}
        goals_message = {"role": "user", "content":
                         f"The following is the latest version of a document outlining my current goals and to-do tasks. I am constantly updating it as new tasks arrive and old ones are completed:\n<goals>\n{self.goals_doc}</goals>"}
        context_messages = self.messages.last_n_messages(N_CONTEXT_MESSAGES, munge=True)
        # Finally, we insert a prefill message with a timestamp in the format of
        # the previously seen messages (so that the model doesn't insert its own
        # fake timestamp)
        timestamp_str = date_utils.fmt_now()
        prefill = {
                "role": "assistant",
                "content": f"[{timestamp_str}] ",
        }
        messages = [system_message, goals_message] + context_messages + [prefill]
        reply = llm.query(messages)
        # reply is a NonStreamingChoice object. Need to do some munging.
        msg = reply['message']
        resp = self._handle_llm_message(msg)
        return resp

    def _handle_llm_message(self, msg):
        """msg is the "message" part of a NonStreamingChoice object.
        Record it in the message db and return a corresponding string that we should
        send in the chat.
        """
        assert msg['role'] == 'assistant'
        text = msg['content']
        if 'tool_calls' in msg:
            return self._handle_tool_call(msg)
        self.messages.add_message(text, 'assistant')
        self.messages.flush()
        return text


    def _handle_tool_call(self, msg):
        """Handle any bookkeeping resulting from an LLM response that contains
        a tool call (possibly including recording a scheduled message event,
        and updating/flushing the message store) and return the user-facing
        message that should be sent to the chat as a result of this LLM response.
        msg is an OpenRouter NonStreamingChoice object.
        """
        chat_reply = msg['content'] or ''
        calls = msg['tool_calls']
        # Turns out models do actually sometimes decide to schedule multiple messages in one go!
        for call in calls:
            call_id = call['id']
            name = call['function']['name']
            assert name == reminder_tool.TOOL['name']
            argstr = call['function']['arguments']
            args = json.loads(argstr)
            assert args.keys() == {'when', 'topic'}
            # TODO: error handling for invalid when
            self.scheduled_messages_db.add_scheduled_message(
                    id=call_id,
                    when=args['when'],
                    topic=args['topic'],
            )
            # In general, it's important (at least during the testing stages) to add our own
            # text to the chat to denote when a reminder has been set, even if the message
            # content here is non-empty. Because we need to be able to distinguish cases where
            # the model hallucinates calling the tool (e.g. by sending a basic text message that
            # says "Okay, I've scheduled a message in 2 hours about X". I've even seen the model
            # output text like `api.schedule_message({'when': '09/30/24 15:00:00', 'topic': 'foo bar baz'})`
            tool_note = f"<Scheduled message at {args['when']} with topic {args['topic']}>"
            chat_reply += (' ' if chat_reply else '') + tool_note

        self.messages.add_message(msg['content'], 'assistant', tool_calls=calls)
        return chat_reply

if __name__ == '__main__':
    # For testing/debugging
    jules = Jules()
    #re = jules.emit_reply("I'm thinking about going to scroll Reddit. What do you think?")
    re = jules.emit_wakeup_message()
    print(re)
    #jules.messages.flush()
