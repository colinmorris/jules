"""
Script with a toy example that should always result in a tool use. Useful for debugging.
"""
import os
import requests
import json
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

import utils
import reminder_tool

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv('LLM_API_KEY')

# Free model that supports tool use
MODELNAME="google/gemini-flash-1.5-exp"
#MODELNAME="google/gemini-pro"
#MODELNAME="openai/gpt-4o-mini"

LOG_RESPONSES = 1
RESPONSE_LOG_FILE = utils.sibpath('responses.log')
LOG_REQUESTS = 1
REQUEST_LOG_FILE = utils.sibpath('requests.log')

# Example taken from OpenRouter docs
TOOL = {
   "type": "function",
   "function": {
    "name": "get_current_weather",
    "description": "Get the current weather in a given location",
    "parameters": {
      "type": "object",
      "properties": {
        "location": {
          "type": "string",
          "description": "The city and state, e.g. San Francisco, CA"
        },
        "unit": {
          "type": "string",
          "enum": [
            "celsius",
            "fahrenheit"
          ]
        }
      },
      "required": [
        "location"
      ]
    }
  } 
}

def say(m):
    messages = [
            {"role": "system", "content": "You are an AI assistant."},
            {"role": "user", "content": m},
    ]
    return query(messages)

def raw_query(messages):
    """Return a response object"""
    tool = TOOL
    data=json.dumps({
        "model": MODELNAME,
        "messages": messages,
        "tools": [tool],
        })
    if LOG_REQUESTS:
        with open(REQUEST_LOG_FILE, 'a') as f:
            f.write(data+'\n')
    response = requests.post(
            url=API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            data=data,
            )
    if LOG_RESPONSES:
        with open(RESPONSE_LOG_FILE, 'a') as f:
            f.write(response.text.strip() + '\n')

    return response

def query(messages):
    """Returns an OpenRouter "NonStreamingChoice" object.
    """
    resp = raw_query(messages)
    # Check for errors
    print(f"Status code: {resp.status_code}")
    resp.raise_for_status()
    dat = json.loads(resp.text)
    msgs = dat['choices']
    assert len(msgs) == 1, msgs
    # Should be a NonStreamingChoice object
    # https://openrouter.ai/docs/responses
    msg = msgs[0]
    assert 'error' not in msg, msg
    return msg

if __name__ == '__main__':
    m = "What is the weather in Dayton, Ohio?"
    resp = say(m)
    print(resp)
