import datetime
import json
import os

import utils
import date_utils

MESSAGE_HISTORY_FILENAME = 'messages.json'
# Whether to pretty-print content in messages.json
PPRINT_JSON = 1


def munge_message(m):
    """Translate a message dictionary of the form stored in messages.json to
    the form expected by the LLM API.

    The message dictionary is expected to have keys...
        timestamp: unix timestamp
        role: user|assistant|system
        content: message text
        tool_calls: (optional) see OpenRouter docs for type defn
    """
    timestr = date_utils.fmt_timestamp(m['timestamp'])
    out = dict(
            role=m['role'],
            content=f"[{timestr}] {m['content']}",
    )
    if 'tool_calls' in m:
        out['tool_calls'] = m['tool_calls']
    return out

class MessageHistory(object):
    """A collection of chat messages backed by a file store.

    Messages are encoded as dicts with keys:
    - role: (user/assistant/system/tool)
    - content: text
    - timestamp: unix timestamp
    - tool_calls (optional): per OpenRouter schema
    """

    def __init__(self, message_filename=None, reset=False):
        self.fname = message_filename or MESSAGE_HISTORY_FILENAME
        path = utils.sibpath(self.fname)
        self.path = path
        if os.path.exists(path) and not reset:
            with open(path) as f:
                self.messages = json.load(f)
        else:
            self.messages = []

    def is_empty(self):
        return self.messages == []

    def add_message(self, text, role, timestamp=None, tool_calls=None):
        """
        text: text of message
        role: one of 'user' or 'assistant'
        timestamp: unix timestamp, or None for now (datetime okay too I guess)
        tool_calls: see https://openrouter.ai/docs/responses for ToolCall type definition
        """
        if timestamp is None:
            timestamp = int(datetime.datetime.now().timestamp())
        elif isinstance(timestamp, datetime.datetime):
            timestamp = int(timestamp.timestamp())
        msg = dict(
            role=role,
            content=text,
            timestamp=timestamp,
        )
        if tool_calls:
            msg['tool_calls'] = tool_calls
        self.messages.append(msg)

    def last_n_messages(self, n=5, munge=True):
        msgs = self.messages[-n:]
        if munge:
            msgs = [munge_message(m) for m in msgs]
        return msgs

    def flush(self):
        with open(self.path, 'w') as f:
            json.dump(self.messages, f, indent=4 if PPRINT_JSON else None)

    def reset(self):
        """Clear the message store of all messages."""
        self.messages = []
        self.flush()


