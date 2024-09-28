import datetime
import json

import date_utils

# Tried to implement some shim that would allow me to switch between OR and Claude, but the latter
# capability hasn't been tested or scrupulously maintained, so
_API = 'OpenRouter'
assert _API in ('Anthropic', 'OpenRouter')
input_key = "input_schema" if _API == 'Anthropic' else 'parameters'

def construct_tool_call(id, when, topic):
    if isinstance(when, datetime.datetime):
        when = date_utils.fmt_dt(when)
    args = {'when': when, 'topic': topic}
    argstr = json.dumps(args)
    return {'id': id,
            'type': 'function',
            'function': {
                'name': 'schedule_message',
                'arguments': argstr,
            },
    }

TOOL = {
    'name': "schedule_message",
    "description": "Schedule an assistant message to be sent in the future.",
    "parameters": {
        "type": "object",
        'properties': {
            "when": {
                "type": "string",
                # This format is listed in the json schema docs, but I guess
                # it's not supported by OpenRouter? Or the underlying model?
                #"format": "date-time",
                "description": "The future date and time the message should be sent, e.g. 09/30/24 15:00:00"
            },
            "topic": {
                "type": "string",
                "description": "Brief summary of the intended topic of the future message, e.g. Reminder to water plants"
            }
        },
        "required": ["when", "topic"]
    }
}

if _API == 'OpenRouter':
    TOOL["type"] = "function"
