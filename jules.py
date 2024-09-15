import requests
import json

import message_store

with open('SYSTEM_PROMPT.txt') as f:
    SYSTEM_PROMPT = f.read()

class Jules(object):

    def __init__(self):
        self.messages = message_store.MessageHistory()

    def emit_wakeup_message(self):
        # For now let's just add a dummy system message to set the context
        # for this task
        # (Actually, this problem won't work, since it seems these models
        # are trained on convos that strictly alternate between user and assistant
        # messages? Maybe can do something with prefill here?)
        preamble = "It's 9am. Time for user's morning wakeup message. I will encourage him to start the day in a healthy way and suggest a task from the goals document for him to work on today. We might have to do some negotiation to come up with a plan for the day."
        self.messages.add_message(preamble, 'assistant')
        msg = self.query_llm()
        return msg

    def emit_reply(self, user_message):
        """user_message: telegram Message object
        see https://core.telegram.org/bots/api#message
        """
        timestamp = user_message.date
        self.messages.add_message(user_message.text, 'user', timestamp)
        msg = self.query_llm()
        return msg

    def query_llm(self):
        """Return the text of the message returned by the LLM conditioned
        on the current message history, system prompt, and goals doc.
        """
        pass

