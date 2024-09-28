import requests
import json
import datetime
import pathlib
import os
from dotenv import load_dotenv

import message_store
import llm
import utils
import date_utils
import scheduled_messages_db
import reminder_tool

load_dotenv()

USER = os.getenv('USER')

GOALS_FNAME = 'goals.txt'

# How many of the most recent messages to send to the model
N_CONTEXT_MESSAGES = 15

with open(utils.sibpath('system_prompt.txt')) as f:
    SYSTEM_PROMPT = f.read()

class Jules(object):

    def __init__(self, canned='ifcold'):
        """Canned should be one of:
            - True: force replacement of message history with canned history
                from construct_canned_message_history method
            - False: never insert canned history
            - 'ifcold': insert canned history only if the message store is empty
        """
        self.messages = message_store.MessageHistory()
        if canned:
            if canned == 'ifcold' and self.messages.is_empty():
                self.construct_canned_message_history()
            elif canned != 'ifcold':
                self.messages.reset()
                self.construct_canned_message_history()
        with open(utils.sibpath(GOALS_FNAME)) as f:
            self.goals_doc = f.read()
        self.scheduled_messages_db = scheduled_messages_db.ScheduledMessagesDatabase()

    def construct_canned_message_history(self):
        """Called from a cold start to insert fake example dialogue to guide
        the model.

        As currently written, this history comprises about 13 messages spanning
        one imagined day. (So if we actually want the model to learn from all of
        this, we better set N_CONTEXT_MESSAGES at least that high!)
        """
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        def at(timestr):
            """timestr is e.g. "17:32:00". Return a datetime object corresponding
            to yesterday at that time.
            """
            hr, minute, second = map(int, timestr.split(':'))
            return yesterday.replace(hour=hr, minute=minute, second=second)
        self._insert_wakeup_preamble(when=at('9:00:00'))
        self.messages.add_message(f"Good morning, {USER}. What are you going to work on today? May I suggest renewing your passport?", "assistant", at('9:00:01'))
        self.messages.add_message("I have an appointment to do that tomorrow. I'm going to work on my 2024 stock trades and associated bookkeeping. I'm getting a bit of a late start, so I'm going to try to keep working until 6.", "user", at('9:52:31'))
        tool1 = {'id': 'tool_0_schedule_message', 'when': at('18:00:00'), 'topic': "Check on end of day progress"}
        tooluse1 = reminder_tool.construct_tool_call(**tool1)
        self.messages.add_message("Ok", "assistant", at('9:52:35'), [tooluse1])
        self.messages.add_message("My motivation is flagging. Getting tempted to just scroll Twitter or something.", "user", at('16:10:55'))
        self.messages.add_message("Don't you fucking dare. If you're out of mental energy, you can switch to a different task for the rest of the day, like housework.", "assistant", at('16:10:58'))
        self.messages.add_message("Ok. I'm gonna start a load of laundry and do a grocery run to clear my mind.", "user", at('16:11:15'))
        self.messages.add_message('👍', 'assistant', at('16:11:17'))
        self._insert_scheduled_preamble(whensaid=at('18:00:00'), **tool1)
        self.messages.add_message("How did the day go? Did you make it to 6 without distractions?", "assistant", at('18:00:00'))
        self.messages.add_message("Yeah. I feel great. Thanks Jules. Gonna make dinner and then finally treat myself to some screen time.", "user", at('18:01:51'))
        tool2 = {'id': 'tool_1_schedule_message', 'when': at('23:00:00'), 'topic': 'Stop phone use for the night'}
        tooluse2 = reminder_tool.construct_tool_call(**tool2)
        self.messages.add_message("Nice. But you should probably put the phone down by 23:00 at the latest so you can fall asleep at a reasonable time.", "assistant", at('18:01:55'))
        self._insert_scheduled_preamble(whensaid=at('23:00:00'), **tool2)
        self.messages.add_message("Put the phone down, bro. Switch to a book or something.", "assistant", at('23:00:01'))


    def emit_wakeup_message(self):
        """Return a chat message corresponding to our recurring first-thing-in-the-morning scheduled
        message pattern. We accomplish this by first inserting a message into the history
        prompting the model to generate a wakeup message with the desired properties.
        """
        self._insert_wakeup_preamble()
        msg = self.query_llm()
        return msg

    def _insert_wakeup_preamble(self, when=None):
        preamble = f"<thinking>It's 9am. Time for {USER}'s morning wakeup message. I will encourage him to start the day in a thoughtful way, avoiding falling into distractions. I will pick only ONE item from the goal list to suggest he work on. If he pushes back, I'll work with him to identify a different goal.</thinking>"
        #self.messages.add_message(preamble, 'assistant')

        # Trying a different tack
        user_preamble = "Good morning Jules. I could use some encouragement to start the morning in a salutary way, and a suggestion for one task to work on today."
        #self.messages.add_message(user_preamble, 'user')
        system_preamble = "It is 9am. Please emit a brief wakeup message for Colin."
        self.messages.add_message(system_preamble, 'system', when)

    def _insert_scheduled_preamble(self, id, when, topic, whensaid=None):
        if isinstance(when, datetime.datetime):
            when = date_utils.fmt_dt(when)
        preamble = f"Emit message with id {id} scheduled for {when} on topic: '{topic}'"
        self.messages.add_message(preamble, 'system', whensaid)

    def emit_scheduled_message(self, id, when, topic):
        """Functions similarly to emit_wakeup_message, but for messages scheduled
        via the scheduled message tool.
        """
        self._insert_scheduled_preamble(id, when, topic)
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
