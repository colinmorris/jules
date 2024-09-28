"""Test wakeup message conditioned on canned history.
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import jules as juleslib

jules = juleslib.Jules(canned=True)

m = jules.emit_wakeup_message()
print(m)
