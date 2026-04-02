"""Vocabulary trainer — linear progression through CW abbreviations.

Shows each term with its meaning and history, lets you listen to it,
then has you key it out. Key it correctly a few times to advance.
Progress is saved between sessions.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from glossary import VOCAB_ORDER
from morse import CHAR_TO_MORSE

PROGRESS_FILE = 'vocab_progress.json'
REQUIRED_CORRECT = 3  # key correctly this many times to advance


@dataclass
class VocabProgress:
    """Persistent progress for the vocabulary trainer."""
    current_idx: int = 0  # index into VOCAB_ORDER
    mastered: list = field(default_factory=list)  # list of mastered abbreviations
    # Per-term stats: {"CQ": [correct, attempts], ...}
    term_stats: dict = field(default_factory=dict)

    def save(self, path=None):
        path = path or PROGRESS_FILE
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path=None):
        path = path or PROGRESS_FILE
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items()
                         if k in cls.__dataclass_fields__})
        except (json.JSONDecodeError, TypeError, ValueError):
            return cls()


class VocabTrainer:
    """Linear vocabulary trainer with keying practice."""

    def __init__(self, progress: VocabProgress):
        self.progress = progress
        self.correct_streak = 0  # consecutive correct for current term
        self.show_morse = False
        self.just_mastered = False
        self.quiz_last_correct = None  # result of last check_send

    @property
    def current_entry(self):
        """Returns (abbrev, meaning, history) for the current term."""
        idx = self.progress.current_idx
        if idx < len(VOCAB_ORDER):
            return VOCAB_ORDER[idx]
        return None

    @property
    def term(self):
        entry = self.current_entry
        return entry[0] if entry else None

    @property
    def meaning(self):
        entry = self.current_entry
        return entry[1] if entry else None

    @property
    def history(self):
        entry = self.current_entry
        return entry[2] if entry else None

    @property
    def term_number(self):
        return self.progress.current_idx + 1

    @property
    def total_terms(self):
        return len(VOCAB_ORDER)

    @property
    def is_complete(self):
        return self.progress.current_idx >= len(VOCAB_ORDER)

    def start_term(self):
        """Reset state for the current term."""
        self.correct_streak = 0
        self.show_morse = False
        self.just_mastered = False

    def check_send(self, decoded_text):
        """Check keyed text against current term.
        Returns (correct, mastered)."""
        decoded = decoded_text.strip().upper()
        target = self.term.upper() if self.term else ''
        # Strip ? from target for keying (e.g., QRZ? -> QRZ)
        target_key = target.rstrip('?')
        correct = (decoded == target_key)
        self.quiz_last_correct = correct

        # Track stats
        abbrev = self.term
        if abbrev not in self.progress.term_stats:
            self.progress.term_stats[abbrev] = [0, 0]
        self.progress.term_stats[abbrev][1] += 1

        if correct:
            self.progress.term_stats[abbrev][0] += 1
            self.correct_streak += 1
        else:
            self.correct_streak = 0

        mastered = self.correct_streak >= REQUIRED_CORRECT
        if mastered:
            self.just_mastered = True
            if abbrev not in self.progress.mastered:
                self.progress.mastered.append(abbrev)
        return correct, mastered

    def advance(self):
        """Move to the next term."""
        self.progress.current_idx += 1
        self.start_term()
        self.progress.save()

    def get_morse_pattern(self):
        """Return the dit/dah pattern for the current term."""
        if not self.term:
            return ''
        parts = []
        for ch in self.term.rstrip('?'):
            pattern = CHAR_TO_MORSE.get(ch, '?')
            spaced = ' '.join(pattern)
            parts.append(spaced)
        return '   '.join(parts)
