"""Persistent settings for the Morse trainer."""

import json
import os
from dataclasses import asdict, dataclass, field

SETTINGS_FILE = 'settings.json'


def _headphones_plugged():
    """Check if headphones are plugged in via kernel input device."""
    import subprocess
    try:
        result = subprocess.run(
            ['evtest', '--query', '/dev/input/event1', 'EV_SW', 'SW_HEADPHONE_INSERT'],
            capture_output=True, timeout=1
        )
        return result.returncode == 10  # 10 = switch active
    except Exception:
        return False


@dataclass
class Settings:
    sidetone_freq: int = 650        # Hz
    char_wpm: int = 20              # character speed (Koch sends at this speed)
    eff_wpm: int = 10               # effective/Farnsworth speed
    speaker_vol: float = 0.8        # speaker volume (0.05-1.0)
    headphone_vol: float = 0.10     # headphone volume (0.01-0.20)
    key_sound: int = 1              # 0=none, 1=wood block, 2=soft tap
    key_mode: int = 0               # 0=straight, 1=iambic A, 2=iambic B
    callsign: str = ''              # user's ham callsign

    @property
    def volume(self):
        """Return the active volume based on headphone jack state."""
        if _headphones_plugged():
            return self.headphone_vol
        return self.speaker_vol

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
            # Migrate old single 'volume' to split volumes
            if 'volume' in data and 'speaker_vol' not in data:
                old_vol = data.pop('volume')
                data['speaker_vol'] = old_vol
                data['headphone_vol'] = min(old_vol, 0.3)
            elif 'volume' in data:
                data.pop('volume')  # drop stale key
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except (json.JSONDecodeError, TypeError, ValueError):
            return cls()  # corrupted file, start fresh
