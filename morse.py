"""Morse code table and real-time decoder."""

# Morse code: dit = '.', dah = '-'
MORSE_TABLE = {
    '.-': 'A',     '-...': 'B',   '-.-.': 'C',   '-..': 'D',
    '.': 'E',      '..-.': 'F',   '--.': 'G',     '....': 'H',
    '..': 'I',     '.---': 'J',   '-.-': 'K',     '.-..': 'L',
    '--': 'M',     '-.': 'N',     '---': 'O',     '.--.': 'P',
    '--.-': 'Q',   '.-.': 'R',    '...': 'S',     '-': 'T',
    '..-': 'U',    '...-': 'V',   '.--': 'W',     '-..-': 'X',
    '-.--': 'Y',   '--..': 'Z',
    '-----': '0',  '.----': '1',  '..---': '2',   '...--': '3',
    '....-': '4',  '.....': '5',  '-....': '6',   '--...': '7',
    '---..': '8',  '----.': '9',
    '.-.-.-': '.',  '--..--': ',', '..--..': '?',  '-..-.': '/',
    '-....-': '-',  '.--.-.': '@',
}

# Reverse lookup: character -> morse pattern
CHAR_TO_MORSE = {v: k for k, v in MORSE_TABLE.items()}

# Koch method character order
KOCH_ORDER = [
    'K', 'M', 'R', 'S', 'U', 'A', 'P', 'T', 'L', 'O',
    'W', 'I', '.', 'N', 'J', 'E', 'F', '0', 'Y', 'V',
    ',', 'G', '5', '/', 'Q', '9', 'Z', 'H', '3', '8',
    'B', '?', '4', '2', '7', 'C', '1', 'D', '6', 'X',
]


class Decoder:
    """Decode straight-key press/release timing into characters.

    Timing rules (based on configured dit length):
      - Press < 1.5 * dit_ms → dit
      - Press >= 1.5 * dit_ms → dah
      - Silence >= 3 * dit_ms → end of character (inter-char gap)
      - Silence >= 7 * dit_ms → word space
    """

    def __init__(self, wpm=15):
        self.set_wpm(wpm)
        self.current_element = ''  # accumulates '.' and '-'
        self.decoded_text = ''
        self.key_down_time = None
        self.key_up_time = None
        self._pending_space_checked = False

    def set_wpm(self, wpm):
        """Set words per minute. PARIS standard: 1 WPM = 50 dit-lengths/min."""
        self.wpm = wpm
        self.dit_ms = 1200 / wpm  # milliseconds per dit

    def on_key_down(self, time_ms):
        """Call when the key is pressed. time_ms = current time in ms."""
        # Check gap since last key-up
        if self.key_up_time is not None:
            gap = time_ms - self.key_up_time
            if gap >= 7 * self.dit_ms:
                # Word space
                self._finish_character()
                self.decoded_text += ' '
            elif gap >= 2.5 * self.dit_ms:
                # Character space
                self._finish_character()

        self.key_down_time = time_ms
        self._pending_space_checked = False

    def on_key_up(self, time_ms):
        """Call when the key is released. Returns the element ('.' or '-')."""
        if self.key_down_time is None:
            return None

        duration = time_ms - self.key_down_time
        if duration < 1.5 * self.dit_ms:
            element = '.'
        else:
            element = '-'

        self.current_element += element
        self.key_up_time = time_ms
        self.key_down_time = None
        return element

    def check_timeout(self, time_ms):
        """Call periodically to detect character/word boundaries.
        Returns any new characters decoded since last call.
        """
        if self.key_up_time is None or self.key_down_time is not None:
            return ''

        gap = time_ms - self.key_up_time
        new_text = ''

        if gap >= 7 * self.dit_ms and not self._pending_space_checked:
            new_text = self._finish_character()
            if new_text and not self.decoded_text.endswith(' '):
                self.decoded_text += ' '
                new_text += ' '
            self._pending_space_checked = True
        elif gap >= 2.5 * self.dit_ms and self.current_element:
            new_text = self._finish_character()

        return new_text

    def _finish_character(self):
        """Decode current element buffer into a character."""
        if not self.current_element:
            return ''

        char = MORSE_TABLE.get(self.current_element, '?')
        self.decoded_text += char
        self.current_element = ''
        return char

    def reset(self):
        """Clear all state."""
        self.current_element = ''
        self.decoded_text = ''
        self.key_down_time = None
        self.key_up_time = None
        self._pending_space_checked = False
