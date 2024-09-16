import datetime
import json
import os

MESSAGE_HISTORY_FILENAME = 'messages.json'
# Whether to pretty-print content in messages.json
PPRINT_JSON = 1

def fmt_timestamp(timestamp):
    dt = datetime.datetime.fromtimestamp(timestamp)
    timestr = dt.strftime("%m/%d %H:%M:%S")
    return timestr

def fmt_now():
    return fmt_timestamp(datetime.datetime.now().timestamp())

def munge_message(m):
    timestr = fmt_timestamp(m['timestamp'])
    return dict(
            role=m['role'],
            content=f"[{timestr}] {m['content']}",
    )

class MessageHistory(object):
    """A collection of chat messages backed by a file store.

    Messages are encoded as dicts with keys:
    - role: (user/assistant/system/tool)
    - content: text
    - timestamp: unix timestamp
    """

    def __init__(self, message_filename=None, reset=False):
        self.fname = message_filename or MESSAGE_HISTORY_FILENAME
        if os.path.exists(self.fname) and not reset:
            with open(self.fname) as f:
                self.messages = json.load(f)
        else:
            self.messages = []

    def add_message(self, text, role, timestamp=None):
        """
        text: text of message
        role: one of 'user' or 'assistant'
        timestamp: unix timestamp, or None for now
        """
        if timestamp is None:
            timestamp = int(datetime.datetime.now().timestamp())
        self.messages.append(dict(
            role=role,
            content=text,
            timestamp=timestamp,
        ))

    def last_n_messages(self, n=5, munge=True):
        msgs = self.messages[-n:]
        if munge:
            msgs = [munge_message(m) for m in msgs]
        return msgs

    def flush(self):
        with open(self.fname, 'w') as f:
            json.dump(self.messages, f, indent=4 if PPRINT_JSON else None)

    def reset(self):
        """Clear the message store of all messages."""
        self.messages = []
        self.flush()


