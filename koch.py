"""Koch method receive trainer with spaced repetition."""

import random
from morse import KOCH_ORDER, CHAR_TO_MORSE
from progress import KochProgress

# Minimum attempts at a level before promotion check
MIN_ATTEMPTS_FOR_PROMOTION = 20
PROMOTION_ACCURACY = 0.90


class KochTrainer:
    """Manages Koch method training sessions with accuracy-based weighting.

    Characters you get wrong appear more often. The newest character still
    gets extra weight, but struggling characters won't fade away.
    """

    def __init__(self, progress: KochProgress):
        self.progress = progress
        self.current_char = None
        self.choices = []
        self.session_correct = 0
        self.session_total = 0
        self.last_correct = None
        self.show_hints = False  # D-pad up toggles this

    @property
    def active_chars(self) -> list:
        """Characters unlocked so far (first N of KOCH_ORDER)."""
        return KOCH_ORDER[:self.progress.level + 2]

    def start_round(self) -> str:
        """Pick a character using spaced repetition weighting.

        Weighting strategy:
        - Characters with lower accuracy get higher weight
        - The newest character gets a bonus
        - Minimum weight ensures every character can appear
        """
        chars = self.active_chars
        weights = []

        for i, ch in enumerate(chars):
            acc = self.progress.char_accuracy(ch)
            # Base weight: inverse of accuracy (struggle chars get more weight)
            # acc=1.0 -> weight=1, acc=0.5 -> weight=2, acc=0.0 -> weight=4
            weight = max(1.0, 4.0 - 3.0 * acc)

            # Newest character bonus (30% extra weight)
            if i == len(chars) - 1:
                weight *= 1.3

            weights.append(weight)

        # Weighted random selection
        self.current_char = random.choices(chars, weights=weights, k=1)[0]
        self.choices = self._generate_choices(self.current_char)
        self.last_correct = None
        return self.current_char

    def submit_answer(self, answer: str) -> bool:
        """User answered. Returns True if correct."""
        correct = (answer == self.current_char)
        self.last_correct = correct
        self.session_total += 1
        if correct:
            self.session_correct += 1
        self.progress.record(correct, char=self.current_char)
        return correct

    def check_promotion(self) -> bool:
        """Check if accuracy qualifies for next level."""
        if self.progress.level >= len(KOCH_ORDER) - 2:
            return False
        if self.progress.level_attempts < MIN_ATTEMPTS_FOR_PROMOTION:
            return False
        if self.progress.level_accuracy >= PROMOTION_ACCURACY:
            self.progress.promote()
            return True
        return False

    @property
    def session_accuracy(self) -> float:
        if self.session_total == 0:
            return 0.0
        return self.session_correct / self.session_total

    def get_hint(self, char: str) -> str:
        """Return the dit/dah pattern for a character."""
        pattern = CHAR_TO_MORSE.get(char, '')
        # Make it more readable: dots and dashes with spaces
        return '  '.join(pattern) if pattern else ''

    def _generate_choices(self, correct: str) -> list:
        """Return 4 choices: correct + 3 distractors from active chars."""
        chars = self.active_chars
        distractors = [c for c in chars if c != correct]
        if len(distractors) >= 3:
            picked = random.sample(distractors, 3)
        else:
            picked = distractors[:]

        choices = [correct] + picked
        random.shuffle(choices)
        return choices
