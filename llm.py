import os
import requests
import json

from dotenv import load_dotenv

import utils
import reminder_tool

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv('LLM_API_KEY')

#MODELNAME = "nousresearch/hermes-3-llama-3.1-405b:free"
# Free model that supports tool use
MODELNAME="google/gemini-flash-1.5-exp"
# Haven't been able to get through to this one yet. Constantly get 429 "Resource has been exhausted" error messages.
#MODELNAME="google/gemini-pro-1.5-exp"
#MODELNAME="google/gemini-pro"

LOG_RESPONSES = 1
RESPONSE_LOG_FILE = utils.sibpath('responses.log')
LOG_REQUESTS = 1
REQUEST_LOG_FILE = utils.sibpath('requests.log')

def raw_query(messages):
    """Return a response object"""
    tool = {"type": "function",
            "function": reminder_tool.TOOL,
    }
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
    # For debugging
    import message_store
    history = message_store.MessageHistory()
    msgs = history.last_n_messages(5)
    resp = query(msgs)
