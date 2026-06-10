"""Scripted QSO conversations for the procedure trainer."""

import random
from band import random_callsign, NAMES, QTHS


# Each step: (speaker, description, cw_text)
#   speaker: 'them' or 'you'
#   description: what's happening (shown on screen)
#   cw_text: the CW text with {template} variables

QSO_SCRIPTS = [
    {
        'name': 'Answer a CQ',
        'description': 'A station calls CQ. Answer and complete a short QSO.',
        'steps': [
            ('them', 'Station calls CQ',
             'CQ CQ CQ DE {other} {other} K'),
            ('you', 'Answer their CQ',
             '{other} DE {call} {call} K'),
            ('them', 'They come back to you',
             '{call} DE {other} TNX FER CALL UR RST {rst} NAME {name_them} QTH {qth_them} BK'),
            ('you', 'Send your info',
             'R {name_them} UR RST 599 NAME {name} QTH {qth} BK'),
            ('them', 'They sign off',
             'R TNX FER QSO 73 DE {other} SK'),
            ('you', 'Sign off',
             '73 DE {call} SK'),
        ],
    },
    {
        'name': 'Call CQ',
        'description': 'You call CQ and work a station that answers.',
        'steps': [
            ('you', 'Call CQ',
             'CQ CQ CQ DE {call} {call} K'),
            ('them', 'Someone answers!',
             '{call} DE {other} {other} K'),
            ('you', 'Send your exchange',
             '{other} DE {call} TNX FER CALL UR RST 599 NAME {name} QTH {qth} BK'),
            ('them', 'They send their info',
             'R {name} UR RST {rst} NAME {name_them} QTH {qth_them} BK'),
            ('you', 'Sign off',
             'R TNX FER QSO 73 DE {call} SK'),
            ('them', 'They sign off',
             'TU 73 DE {other} SK'),
        ],
    },
    {
        'name': 'Quick Signal Report',
        'description': 'Short exchange — just signal reports and 73.',
        'steps': [
            ('them', 'Station calls CQ',
             'CQ CQ DE {other} K'),
            ('you', 'Answer',
             '{other} DE {call} K'),
            ('them', 'Signal report',
             '{call} UR RST {rst} BK'),
            ('you', 'Your report back',
             'R UR RST 599 73 DE {call} SK'),
            ('them', 'They sign off',
             'TU 73 SK'),
        ],
    },
]


class ScriptRunner:
    """Manages a single QSO script playthrough."""

    def __init__(self, script, user_callsign='N0CALL'):
        self.script = script
        self.step_idx = 0
        self.steps = []
        self._fill_templates(script['steps'], user_callsign)

    def _fill_templates(self, steps, user_callsign):
        """Fill template variables with randomized data."""
        other = random_callsign()
        name_them = random.choice(NAMES)
        qth_them = random.choice(QTHS)
        rst = random.choice(['599', '579', '589', '569'])

        # User's name/qth — use first part of callsign area as QTH stand-in
        user_name = 'OP'
        user_qth = 'QTH'

        for speaker, desc, template in steps:
            text = template.format(
                call=user_callsign,
                other=other,
                name=user_name,
                name_them=name_them,
                qth=user_qth,
                qth_them=qth_them,
                rst=rst,
            )
            self.steps.append((speaker, desc, text))

    @property
    def current_step(self):
        if self.step_idx < len(self.steps):
            return self.steps[self.step_idx]
        return None

    @property
    def is_complete(self):
        return self.step_idx >= len(self.steps)

    @property
    def total_steps(self):
        return len(self.steps)

    def advance(self):
        self.step_idx += 1
