import requests
import json
import pathlib

import message_store
import llm
import utils

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
        timestamp_str = message_store.fmt_now()
        prefill = {
                "role": "assistant",
                "content": f"[{timestamp_str}] ",
        }
        messages = [system_message, goals_message] + context_messages + [prefill]
        reply = llm.query(messages)
        # reply is a StreamingChoice object. Need to do some munging.
        msg = reply['message']
        assert msg['role'] == 'assistant'
        text = msg['content']
        self.messages.add_message(text, 'assistant')
        self.messages.flush()
        return text

if __name__ == '__main__':
    # For testing/debugging
    jules = Jules()
    #re = jules.emit_reply("I'm thinking about going to scroll Reddit. What do you think?")
    re = jules.emit_wakeup_message()
    print(re)
    #jules.messages.flush()
