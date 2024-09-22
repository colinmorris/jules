_API = 'OpenRouter'
assert _API in ('Anthropic', 'OpenRouter')
input_key = "input_schema" if _API == 'Anthropic' else 'parameters'

TOOL = {
    'name': "schedule_message",
    input_key: {
        'properties': {
            "when": {
                "type": "string",
                "format": "date-time",
                "description": "The future date and time the message should be sent, e.g. 09/30 15:00:00"
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
