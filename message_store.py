import datetime
import json

MESSAGE_HISTORY_FILENAME = 'messages.json'

class MessageHistory(object):
    """A collection of chat messages backed by a file store.
    """

    def __init__(self, message_filename=None):
        self.fname = message_filename or MESSAGE_HISTORY_FILENAME
        with open(self.fname) as f:
            self.messages = json.load(f)

    def add_message(self, text, role, timestamp=None):
        """
        text: text of message
        role: one of 'user' or 'assistant'
        timestamp: unix timestamp, or None for now
        """
        if timestamp is None:
            timestamp = int(datetime.datetime.now().timestamp())

    def last_n_messages(self, n=5):
        return self.messages[-n:]

    def flush(self):
        with open(self.fname) as f:
            json.dump(self.messages, f)


