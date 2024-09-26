"""Script for debugging server <-> LLM API flow locally.
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import jules as juleslib

jules = juleslib.Jules()
jules.messages.reset()

def say(text):
    reply = jules.emit_reply(text)
    return reply

m = "I'm going to work on investing my extra cash for a bit. Can you schedule a message in 2 hours to remind me to take a break and get some exercise?"
re = say(m)
print(re)
