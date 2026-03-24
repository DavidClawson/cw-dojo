"""Persistent settings for the Morse trainer."""

import json
import os
from dataclasses import asdict, dataclass, field

SETTINGS_FILE = 'settings.json'


@dataclass
class Settings:
    sidetone_freq: int = 650        # Hz
    char_wpm: int = 20              # character speed (Koch sends at this speed)
    eff_wpm: int = 10               # effective/Farnsworth speed
    volume: float = 0.8             # master volume
    callsign: str = ''              # user's ham callsign

    def save(self, path=None):
        path = path or SETTINGS_FILE
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path=None):
        path = path or SETTINGS_FILE
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except (json.JSONDecodeError, TypeError, ValueError):
            return cls()  # corrupted file, start fresh
