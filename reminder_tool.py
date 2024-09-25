# Tried to implement some shim that would allow me to switch between OR and Claude, but the latter
# capability hasn't been tested or scrupulously maintained, so
_API = 'OpenRouter'
assert _API in ('Anthropic', 'OpenRouter')
input_key = "input_schema" if _API == 'Anthropic' else 'parameters'

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
