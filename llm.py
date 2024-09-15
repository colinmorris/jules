import os
import requests
import json

from dotenv import load_dotenv

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv('LLM_API_KEY')

MODELNAME = "nousresearch/hermes-3-llama-3.1-405b"

LOG_RESPONSES = 1
RESPONSE_LOG_FILE = 'responses.log'

def raw_query(messages):
    """Return a response object"""
    response = requests.post(
            url=API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            data=json.dumps({
                "model": MODELNAME,
                "messages": messages,
                }),
            )
    if LOG_RESPONSES:
        with open(RESPONSE_LOG_FILE, 'a') as f:
            f.write(response.text + '\n')

    return response

def query(messages):
    resp = raw_query(messages)
    dat = json.loads(response.text)
    msgs = dat['choices']
    assert len(msgs) == 1, msgs
    # Should be a StreamingChoice object
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
