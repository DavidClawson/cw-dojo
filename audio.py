"""Procedural CW audio: sidetone, character playback, and noise."""

import numpy as np
import pygame

from morse import CHAR_TO_MORSE

SAMPLE_RATE = 22050  # low rate is fine for sine tones, keeps CPU light


class Sidetone:
    """Generates a continuous CW sidetone that can be keyed on/off."""

    def __init__(self, freq=650, volume=0.8):
        self.freq = freq
        self.volume = volume
        self.playing = False

        # Pre-generate a ~0.1s chunk to loop
        n_samples = SAMPLE_RATE // 10
        t = np.arange(n_samples, dtype=np.float32) / SAMPLE_RATE
        wave = np.sin(2 * np.pi * self.freq * t) * self.volume

        # Tiny attack/decay ramps to avoid clicks
        ramp_len = min(64, n_samples // 4)
        ramp = np.linspace(0, 1, ramp_len, dtype=np.float32)
        wave[:ramp_len] *= ramp
        wave[-ramp_len:] *= ramp[::-1]

        pcm = (wave * 32767).astype(np.int16)
        self.sound = pygame.sndarray.make_sound(
            np.column_stack([pcm, pcm])
        )
        self.channel = None

    def key_down(self):
        if not self.playing:
            self.channel = self.sound.play(loops=-1)
            self.playing = True

    def key_up(self):
        if self.playing:
            self.sound.stop()
            self.playing = False


class CWPlayer:
    """Plays pre-rendered CW characters/words as audio.

    Supports Farnsworth spacing: char_wpm controls the speed of individual
    characters, eff_wpm controls the overall effective speed by stretching
    the gaps between characters and words.
    """

    def __init__(self, freq=650, char_wpm=20, eff_wpm=10, volume=0.8):
        self.freq = freq
        self.char_wpm = char_wpm
        self.eff_wpm = eff_wpm
        self.volume = volume
        self._channel = pygame.mixer.Channel(1)

    def set_speed(self, char_wpm, eff_wpm):
        self.char_wpm = char_wpm
        self.eff_wpm = min(eff_wpm, char_wpm)

    def play_char(self, char: str):
        """Render and play a single character's CW."""
        pattern = CHAR_TO_MORSE.get(char.upper())
        if pattern is None:
            return
        samples = self._render_pattern(pattern)
        self._play_samples(samples)

    def play_text(self, text: str):
        """Render and play a string as CW."""
        _, char_gap, word_gap = self._timing()
        all_samples = []
        for i, ch in enumerate(text.upper()):
            if ch == ' ':
                all_samples.append(self._silence(word_gap))
                continue
            pattern = CHAR_TO_MORSE.get(ch)
            if pattern is None:
                continue
            all_samples.append(self._render_pattern(pattern))
            # Add inter-character gap (unless last char or next is space)
            if i < len(text) - 1 and text[i + 1] != ' ':
                all_samples.append(self._silence(char_gap))

        if all_samples:
            self._play_samples(np.concatenate(all_samples))

    def is_playing(self) -> bool:
        return self._channel.get_busy()

    def stop(self):
        self._channel.stop()

    def _timing(self):
        """Calculate dit/dah/gap durations in seconds."""
        dit_s = 1.2 / self.char_wpm

        if self.eff_wpm >= self.char_wpm:
            # No Farnsworth stretching
            char_gap_s = 3 * dit_s
            word_gap_s = 7 * dit_s
        else:
            # Farnsworth: stretch the 19 spacing units in PARIS
            total_word_s = 60.0 / (self.eff_wpm * 50) * 50  # seconds per word
            element_time_s = 31 * dit_s  # time for the 31 element units
            spacing_time_s = total_word_s - element_time_s
            farnsworth_unit = spacing_time_s / 19.0
            char_gap_s = 3 * farnsworth_unit
            word_gap_s = 7 * farnsworth_unit

        return dit_s, char_gap_s, word_gap_s

    def _render_pattern(self, pattern: str) -> np.ndarray:
        """Render a dit/dah pattern to audio samples."""
        dit_s, _, _ = self._timing()
        dah_s = 3 * dit_s
        intra_gap_s = dit_s  # gap between elements within a character

        segments = []
        for i, element in enumerate(pattern):
            duration = dit_s if element == '.' else dah_s
            segments.append(self._tone(duration))
            if i < len(pattern) - 1:
                segments.append(self._silence(intra_gap_s))

        return np.concatenate(segments)

    def _tone(self, duration_s: float) -> np.ndarray:
        """Generate a sine tone with raised-cosine ramps."""
        n = int(duration_s * SAMPLE_RATE)
        if n == 0:
            return np.array([], dtype=np.float32)
        t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
        wave = np.sin(2 * np.pi * self.freq * t) * self.volume

        # 5ms raised-cosine ramp on each end
        ramp_n = min(int(0.005 * SAMPLE_RATE), n // 4)
        if ramp_n > 0:
            ramp = 0.5 * (1 - np.cos(np.pi * np.arange(ramp_n) / ramp_n))
            wave[:ramp_n] *= ramp
            wave[-ramp_n:] *= ramp[::-1]

        return wave

    def _silence(self, duration_s: float) -> np.ndarray:
        n = int(duration_s * SAMPLE_RATE)
        return np.zeros(n, dtype=np.float32)

    def _play_samples(self, samples: np.ndarray):
        pcm = (samples * 32767).astype(np.int16)
        stereo = np.column_stack([pcm, pcm])
        sound = pygame.sndarray.make_sound(stereo)
        self._channel.play(sound)
