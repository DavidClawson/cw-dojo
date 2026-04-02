"""Iambic keyer — automatic dit/dah timing from paddle inputs.

Supports three modes:
  STRAIGHT: A button = manual key (no auto-timing)
  IAMBIC_A: dit paddle + dah paddle, alternation stops on release
  IAMBIC_B: dit paddle + dah paddle, completes next element after release

In iambic modes, pressing the dit paddle auto-repeats dits at the set WPM.
Pressing the dah paddle auto-repeats dahs. Squeezing both alternates dit-dah.
"""

STRAIGHT = 0
IAMBIC_A = 1
IAMBIC_B = 2

MODE_NAMES = ['Straight', 'Iambic A', 'Iambic B']


class IambicKeyer:
    """State machine for iambic keying.

    Call paddle_dit_down/up and paddle_dah_down/up for paddle events.
    Call update(now_ms) each frame — it returns (tone_on, element) where
    element is '.' or '-' when a new element starts, or None.
    """

    IDLE = 0
    DIT = 1
    DAH = 2
    DIT_GAP = 3   # inter-element gap after dit
    DAH_GAP = 4   # inter-element gap after dah
    CHAR_GAP = 5  # inter-character gap

    def __init__(self, wpm=20):
        self.wpm = wpm
        self.dit_paddle = False
        self.dah_paddle = False
        self.state = self.IDLE
        self.next_time = 0  # ms when current state ends
        self.tone_on = False
        # Iambic B: remember if opposite paddle was pressed during element
        self._dit_memory = False
        self._dah_memory = False

    def set_wpm(self, wpm):
        self.wpm = wpm

    @property
    def dit_ms(self):
        """Duration of one dit in milliseconds."""
        return int(1200 / self.wpm)

    @property
    def dah_ms(self):
        return self.dit_ms * 3

    def paddle_dit_down(self):
        self.dit_paddle = True
        self._dit_memory = True

    def paddle_dit_up(self):
        self.dit_paddle = False

    def paddle_dah_down(self):
        self.dah_paddle = True
        self._dah_memory = True

    def paddle_dah_up(self):
        self.dah_paddle = False

    def update(self, now_ms, iambic_mode=IAMBIC_A):
        """Advance the keyer state machine.

        Returns (tone_on, new_element) where new_element is
        '.' or '-' at the START of a new element, None otherwise.
        """
        new_element = None

        if self.state == self.IDLE:
            # Check if a paddle is pressed
            if self.dit_paddle:
                self._start_dit(now_ms)
                new_element = '.'
            elif self.dah_paddle:
                self._start_dah(now_ms)
                new_element = '-'
            return self.tone_on, new_element

        # Still in current state?
        if now_ms < self.next_time:
            # In iambic B, remember paddle presses during element
            if iambic_mode == IAMBIC_B:
                if self.dit_paddle:
                    self._dit_memory = True
                if self.dah_paddle:
                    self._dah_memory = True
            return self.tone_on, None

        # Current state just ended — transition
        if self.state == self.DIT:
            # Dit just ended, go to gap
            self.tone_on = False
            self.state = self.DIT_GAP
            self.next_time = now_ms + self.dit_ms
            return self.tone_on, None

        elif self.state == self.DAH:
            # Dah just ended, go to gap
            self.tone_on = False
            self.state = self.DAH_GAP
            self.next_time = now_ms + self.dit_ms
            return self.tone_on, None

        elif self.state in (self.DIT_GAP, self.DAH_GAP):
            # Gap after element — decide what's next
            came_from_dit = (self.state == self.DIT_GAP)

            if iambic_mode == IAMBIC_A:
                # Iambic A: alternate only while both paddles held
                if came_from_dit and self.dah_paddle:
                    self._start_dah(now_ms)
                    new_element = '-'
                elif not came_from_dit and self.dit_paddle:
                    self._start_dit(now_ms)
                    new_element = '.'
                elif self.dit_paddle:
                    self._start_dit(now_ms)
                    new_element = '.'
                elif self.dah_paddle:
                    self._start_dah(now_ms)
                    new_element = '-'
                else:
                    self.state = self.IDLE
                    self.tone_on = False
            else:
                # Iambic B: use memory — if opposite was pressed at any
                # point during the element, send it
                if came_from_dit and (self.dah_paddle or self._dah_memory):
                    self._dah_memory = False
                    self._dit_memory = False
                    self._start_dah(now_ms)
                    new_element = '-'
                elif not came_from_dit and (self.dit_paddle or self._dit_memory):
                    self._dit_memory = False
                    self._dah_memory = False
                    self._start_dit(now_ms)
                    new_element = '.'
                elif self.dit_paddle:
                    self._start_dit(now_ms)
                    new_element = '.'
                elif self.dah_paddle:
                    self._start_dah(now_ms)
                    new_element = '-'
                else:
                    self._dit_memory = False
                    self._dah_memory = False
                    self.state = self.IDLE
                    self.tone_on = False

            return self.tone_on, new_element

        return self.tone_on, None

    def reset(self):
        self.state = self.IDLE
        self.tone_on = False
        self.dit_paddle = False
        self.dah_paddle = False
        self._dit_memory = False
        self._dah_memory = False

    def _start_dit(self, now_ms):
        self.state = self.DIT
        self.tone_on = True
        self.next_time = now_ms + self.dit_ms

    def _start_dah(self, now_ms):
        self.state = self.DAH
        self.tone_on = True
        self.next_time = now_ms + self.dah_ms
