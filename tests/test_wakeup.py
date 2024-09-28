"""Script for debugging server <-> LLM API flow locally.
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import jules as juleslib

jules = juleslib.Jules(canned=False)
jules.messages.reset()

m = jules.emit_wakeup_message()
print(m)
