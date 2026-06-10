"""R36S button mapping constants.

Derived from the r33s_joypad entry in ROCKNIX gamecontrollerdb.txt.
All button references across the app should import from here.
"""

# Face buttons
BTN_A = 1
BTN_B = 0
BTN_X = 2
BTN_Y = 3

# Shoulder buttons
BTN_L1 = 4
BTN_R1 = 5
BTN_L2 = 6
BTN_R2 = 7

# Menu buttons
BTN_SELECT = 8
BTN_START = 9

# Function button (index TBD — unknown presses are logged to console)
BTN_FN = 16

# D-pad (reported as buttons on the r33s_joypad, not hat/axis)
BTN_DPAD_UP = 10
BTN_DPAD_DOWN = 11
BTN_DPAD_LEFT = 12
BTN_DPAD_RIGHT = 13

# All known button indices (used to detect unmapped buttons)
ALL_KNOWN = {BTN_A, BTN_B, BTN_X, BTN_Y,
             BTN_L1, BTN_R1, BTN_L2, BTN_R2,
             BTN_SELECT, BTN_START, BTN_FN,
             BTN_DPAD_UP, BTN_DPAD_DOWN, BTN_DPAD_LEFT, BTN_DPAD_RIGHT}
