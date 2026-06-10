"""Send-quality analysis — grade keyed Morse timing against a target.

The Decoder tells you *what* was sent; this module grades *how well* it
was sent: dit/dah ratio, element spacing, and letter spacing, with
human-readable tips like "Dahs too short" per the classic CW-elmer
feedback style.
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher


@dataclass
class SendReport:
    accuracy: float          # 0.0-1.0 decoded-vs-target similarity
    score: int               # 0-100 overall grade
    actual_wpm: int          # speed implied by the user's dit length
    dit_count: int
    dah_count: int
    tips: list = field(default_factory=list)


class SendRecorder:
    """Records raw key down/up timestamps during a send attempt."""

    def __init__(self):
        self.presses = []     # list of (down_ms, up_ms)
        self._down_ms = None

    def key_down(self, now_ms):
        self._down_ms = now_ms

    def key_up(self, now_ms):
        if self._down_ms is not None and now_ms > self._down_ms:
            self.presses.append((self._down_ms, now_ms))
        self._down_ms = None

    def reset(self):
        self.presses = []
        self._down_ms = None


def _median(values):
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    if n % 2:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


def _spread(values):
    """Relative spread (coefficient of variation) of a list of durations."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean <= 0:
        return 0.0
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return (var ** 0.5) / mean


def analyze(presses, wpm, decoded, target):
    """Grade a send attempt.

    presses: list of (down_ms, up_ms) from SendRecorder
    wpm: the configured character speed (decoder classification speed)
    decoded: text the Decoder produced
    target: text the user was asked to send
    """
    decoded = (decoded or '').strip().upper()
    target = (target or '').strip().upper()
    accuracy = SequenceMatcher(None, decoded, target).ratio() if target else 0.0

    unit_cfg = 1200.0 / wpm
    durations = [up - down for down, up in presses]
    # Classify with the same threshold the Decoder uses (1.5 dits)
    dits = [d for d in durations if d < 1.5 * unit_cfg]
    dahs = [d for d in durations if d >= 1.5 * unit_cfg]

    tips = []
    if not durations:
        return SendReport(accuracy=0.0, score=0, actual_wpm=0,
                          dit_count=0, dah_count=0,
                          tips=['No keying detected'])

    # Estimate the sender's own dit unit
    if dits:
        unit_est = _median(dits)
    else:
        unit_est = _median(dahs) / 3.0
    actual_wpm = int(round(1200.0 / unit_est)) if unit_est > 0 else 0

    # --- Element shape ---
    if dits and dahs:
        dah_ratio = _median(dahs) / unit_est
        if dah_ratio < 2.4:
            tips.append('Dahs too short — hold for 3 dits')
        elif dah_ratio > 3.8:
            tips.append('Dahs too long — aim for 3 dits')
    if _spread(dits) > 0.35:
        tips.append('Dit lengths uneven')
    if _spread(dahs) > 0.30:
        tips.append('Dah lengths uneven')

    # --- Spacing ---
    gaps = [presses[i + 1][0] - presses[i][1]
            for i in range(len(presses) - 1)]
    # Intra-character vs inter-character, split at 2 estimated units
    intra = [g for g in gaps if g < 2 * unit_est]
    inter = [g for g in gaps if 2 * unit_est <= g < 6.5 * unit_est]

    if intra:
        m = _median(intra) / unit_est
        if m > 1.6:
            tips.append('Gaps inside letters too wide')
        elif m < 0.5:
            tips.append('Elements running together')
    if inter:
        m = _median(inter) / unit_est
        if m < 2.2:
            tips.append('Letters running together — leave 3 dits')
        elif m > 5.0:
            tips.append('Long pauses between letters')

    timing_quality = max(0.0, 1.0 - 0.25 * len(tips))
    score = int(round(60 * accuracy + 40 * timing_quality))

    if not tips and accuracy >= 0.999:
        tips.append('Clean sending — nice rhythm!')

    return SendReport(accuracy=accuracy, score=score, actual_wpm=actual_wpm,
                      dit_count=len(dits), dah_count=len(dahs), tips=tips)
