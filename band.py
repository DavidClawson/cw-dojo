"""Simulated HF band with CW stations for the waterfall display."""

import random
import time
from dataclasses import dataclass, field
from morse import CHAR_TO_MORSE


# 40m CW band segment
BAND_START = 7000.0    # kHz
BAND_END = 7040.0      # kHz
BAND_WIDTH = BAND_END - BAND_START  # 40 kHz

# Band plan segments (kHz)
BAND_PLAN = [
    (7000, 7025, 'Extra CW', (60, 60, 120)),
    (7025, 7040, 'General CW', (40, 100, 60)),
]

# Realistic callsign prefixes by region
CALLSIGN_PREFIXES = [
    'W', 'K', 'N', 'WA', 'WB', 'KC', 'KD', 'KE', 'KF',
    'AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG',
]

# Common QSO phrases
CQ_TEMPLATES = [
    'CQ CQ CQ DE {call} {call} K',
    'CQ CQ DE {call} {call} {call} K',
    'CQ DX CQ DX DE {call} K',
]

QSO_EXCHANGES = [
    '{other} DE {call} TNX FER CALL UR RST {rst} {rst} NAME {name} QTH {qth} BK',
    '{other} DE {call} R R TNX {name} UR RST {rst} HW CPY? BK',
    '{call} DE {other} TU 73 DE {other} SK',
    'CQ CQ CQ DE {call} {call} K',
]

NAMES = ['BOB', 'JIM', 'TOM', 'DAVE', 'MIKE', 'JOHN', 'BILL', 'ED',
         'AL', 'DAN', 'RON', 'JOE', 'KEN', 'PAT', 'ART', 'RAY']

QTHS = ['CA', 'TX', 'FL', 'NY', 'OH', 'PA', 'IL', 'GA', 'NC', 'MI',
        'VA', 'WA', 'AZ', 'CO', 'OR', 'MN', 'WI', 'MO', 'IN', 'TN']


def random_callsign():
    prefix = random.choice(CALLSIGN_PREFIXES)
    digit = str(random.randint(0, 9))
    suffix_len = random.randint(1, 3)
    suffix = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                     for _ in range(suffix_len))
    return f'{prefix}{digit}{suffix}'


def random_rst():
    """Generate realistic RST report."""
    r = random.choice([3, 4, 5, 5, 5, 5])
    s = random.choice([5, 6, 7, 7, 8, 8, 9, 9, 9])
    return f'{r}{s}9'


@dataclass
class Station:
    """A simulated CW station on the band."""
    callsign: str
    freq: float              # kHz
    wpm: int
    strength: float          # 0.0 - 1.0 (signal strength)
    name: str
    qth: str

    # Transmission state
    message_queue: list = field(default_factory=list)
    current_message: str = ''
    char_index: int = 0
    element_index: int = 0    # index into current char's morse pattern
    transmitting: bool = False
    tx_start_time: float = 0
    next_event_time: float = 0
    idle_until: float = 0

    def generate_activity(self, now: float):
        """Generate new messages if idle."""
        if self.current_message or self.message_queue:
            return
        if now < self.idle_until:
            return

        # Pick an activity
        if random.random() < 0.6:
            # Call CQ
            template = random.choice(CQ_TEMPLATES)
            msg = template.format(call=self.callsign)
        else:
            # Simulated QSO exchange
            other_call = random_callsign()
            template = random.choice(QSO_EXCHANGES)
            msg = template.format(
                call=self.callsign,
                other=other_call,
                rst=random_rst(),
                name=self.name,
                qth=self.qth,
            )

        self.message_queue.append(msg)
        # Pause between transmissions
        self.idle_until = now + random.uniform(3.0, 8.0)

    def get_current_element(self, now: float):
        """Returns (is_tone, freq_offset) for the current moment.

        Call this at frame rate to determine if the station is currently
        sending a tone (dit or dah) or is in a gap.
        """
        if now < self.next_event_time:
            return self.transmitting, 0.0

        dit_s = 1.2 / self.wpm

        # Need next character?
        if self.char_index >= len(self.current_message):
            if self.message_queue:
                self.current_message = self.message_queue.pop(0)
                self.char_index = 0
                self.element_index = 0
                self.transmitting = False
                self.next_event_time = now + random.uniform(0.5, 1.5)
                return False, 0.0
            else:
                self.current_message = ''
                self.transmitting = False
                return False, 0.0

        char = self.current_message[self.char_index]

        if char == ' ':
            # Word space
            self.transmitting = False
            self.next_event_time = now + 7 * dit_s
            self.char_index += 1
            self.element_index = 0
            return False, 0.0

        pattern = CHAR_TO_MORSE.get(char)
        if pattern is None:
            self.char_index += 1
            self.element_index = 0
            return False, 0.0

        if self.element_index >= len(pattern):
            # Done with this character, inter-character gap
            self.transmitting = False
            self.next_event_time = now + 3 * dit_s
            self.char_index += 1
            self.element_index = 0
            return False, 0.0

        if self.transmitting:
            # Was sending a tone, now gap between elements
            self.transmitting = False
            self.next_event_time = now + dit_s  # intra-character gap
            self.element_index += 1
            return False, 0.0
        else:
            # Start a new element
            element = pattern[self.element_index]
            duration = dit_s if element == '.' else 3 * dit_s
            self.transmitting = True
            self.next_event_time = now + duration
            return True, 0.0


class Band:
    """Manages a simulated CW band with multiple stations."""

    def __init__(self, num_stations=5):
        self.stations = []
        self._create_stations(num_stations)

    def _create_stations(self, n):
        """Place stations across the band."""
        for _ in range(n):
            freq = random.uniform(BAND_START + 2, BAND_END - 2)
            wpm = random.choice([12, 15, 15, 18, 18, 20, 22, 25])
            strength = random.uniform(0.3, 1.0)
            station = Station(
                callsign=random_callsign(),
                freq=round(freq, 1),
                wpm=wpm,
                strength=strength,
                name=random.choice(NAMES),
                qth=random.choice(QTHS),
            )
            self.stations.append(station)

    def update(self, now: float):
        """Update all stations. Call each frame."""
        for station in self.stations:
            station.generate_activity(now)
            station.get_current_element(now)

    def get_signal_at(self, freq: float, bandwidth: float = 0.5):
        """Get the combined signal strength at a frequency.

        Returns list of (station, strength, freq_offset) for stations
        within bandwidth of freq.
        """
        results = []
        for station in self.stations:
            offset = abs(station.freq - freq)
            if offset <= bandwidth and station.transmitting:
                # Signal drops off with distance from center
                atten = max(0, 1.0 - (offset / bandwidth))
                results.append((station, station.strength * atten, station.freq - freq))
        return results
