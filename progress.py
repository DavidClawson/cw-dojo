"""Koch trainer progress persistence."""

import json
import os
from dataclasses import asdict, dataclass, field

PROGRESS_FILE = 'koch_progress.json'


@dataclass
class KochProgress:
    level: int = 0                  # index into KOCH_ORDER for newest char (0 = 2 chars)
    total_correct: int = 0
    total_attempts: int = 0
    level_correct: int = 0          # correct at current level (resets on promotion)
    level_attempts: int = 0         # attempts at current level

    # Per-character stats: {"K": [correct, attempts], "M": [correct, attempts], ...}
    char_stats: dict = field(default_factory=dict)

    @property
    def level_accuracy(self):
        if self.level_attempts == 0:
            return 0.0
        return self.level_correct / self.level_attempts

    @property
    def total_accuracy(self):
        if self.total_attempts == 0:
            return 0.0
        return self.total_correct / self.total_attempts

    def char_accuracy(self, char):
        """Get accuracy for a specific character. Returns 0.5 if no data."""
        stats = self.char_stats.get(char)
        if not stats or stats[1] == 0:
            return 0.5  # assume middle ground for new chars
        return stats[0] / stats[1]

    def record(self, correct: bool, char: str = None):
        self.total_attempts += 1
        self.level_attempts += 1
        if correct:
            self.total_correct += 1
            self.level_correct += 1

        # Track per-character stats
        if char:
            if char not in self.char_stats:
                self.char_stats[char] = [0, 0]
            self.char_stats[char][1] += 1
            if correct:
                self.char_stats[char][0] += 1

    def promote(self):
        """Advance to next level. Resets level stats."""
        self.level += 1
        self.level_correct = 0
        self.level_attempts = 0

    def save(self, path=None):
        path = path or PROGRESS_FILE
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path=None):
        path = path or PROGRESS_FILE
        if not os.path.exists(path):
            return cls()
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
