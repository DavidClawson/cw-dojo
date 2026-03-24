"""Waterfall display scene — simulated HF band explorer."""

import numpy as np
import pygame
import time

from audio import CWPlayer, SAMPLE_RATE
from band import Band, BAND_START, BAND_END, BAND_WIDTH, BAND_PLAN
from buttons import (BTN_R1, BTN_R2, BTN_SELECT,
                     BTN_DPAD_UP, BTN_DPAD_DOWN,
                     BTN_DPAD_LEFT, BTN_DPAD_RIGHT)

SCREEN_W, SCREEN_H = 640, 480

# Waterfall dimensions
WF_X = 0
WF_Y = 60
WF_W = SCREEN_W
WF_H = 300

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
AMBER = (255, 180, 0)
GRAY = (80, 80, 80)
LIGHT_GRAY = (160, 160, 160)
RED = (255, 60, 60)
GREEN = (0, 220, 80)
CURSOR_COLOR = (255, 255, 0)

# Waterfall color gradient (dark blue -> cyan -> yellow -> red)
WF_COLORS = []
for i in range(256):
    if i < 64:
        r, g, b = 0, 0, int(i * 2)
    elif i < 128:
        r, g, b = 0, int((i - 64) * 3), 128
    elif i < 192:
        r, g, b = int((i - 128) * 4), 255, int(255 - (i - 128) * 4)
    else:
        r, g, b = 255, int(255 - (i - 192) * 4), 0
    WF_COLORS.append((min(255, r), min(255, g), min(255, b)))


class WaterfallScene:
    """Simulated HF band waterfall display."""

    def __init__(self, settings=None):
        self.settings = settings
        self.band = Band(num_stations=6)
        self.vfo_freq = 7015.0  # current tuning frequency (kHz)
        self.vfo_step = 0.1     # kHz per D-pad press
        self.bandwidth = 0.5    # receiver bandwidth in kHz

        # Waterfall pixel buffer — each row is a spectral snapshot
        self.wf_buffer = np.zeros((WF_H, WF_W, 3), dtype=np.uint8)

        # Audio
        self.sidetone_channel = None
        self.noise_channel = None
        self._tone_playing = False
        self._current_tone_freq = 0

        # Tuning state
        self._hold_left = False
        self._hold_right = False
        self._tune_timer = 0
        self._tune_rate = 0.05  # seconds between tune steps when held

        # Noise
        self._noise_sound = None
        self._noise_volume = 0.15
        self._master_volume = settings.volume if settings else 0.8

        # Start time reference
        self._start_time = None

    def on_enter(self):
        self._start_time = time.time()
        self._setup_noise()
        self.band = Band(num_stations=6)

    def on_exit(self):
        if self._tone_playing:
            pygame.mixer.Channel(1).stop()
            self._tone_playing = False
        if self.noise_channel:
            self.noise_channel.stop()

    def _setup_noise(self):
        """Create realistic HF band noise.

        Real HF noise has several components:
        - Band-limited hiss (filtered white noise, not pure white)
        - Slow amplitude variations (atmospheric QRN)
        - Occasional crackles/pops (static crashes)

        We use a long buffer (8 seconds) with cross-fade at the loop
        point so there's no audible seam.
        """
        duration = 8.0  # long enough that the loop is imperceptible
        n = int(SAMPLE_RATE * duration)

        # Start with white noise
        noise = np.random.randn(n).astype(np.float32)

        # Band-limit it: simple IIR low-pass to get that "hiss" quality
        # Multiple passes of averaging = steeper rolloff
        for _ in range(5):
            noise[1:] = noise[1:] * 0.4 + noise[:-1] * 0.6

        # Add slow amplitude variation (QRN — atmospheric fading)
        # A slow sine modulation at ~0.3 Hz gives natural "breathing"
        t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
        qrn_envelope = 0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t + np.random.uniform(0, 6.28))
        # Add a second slower component
        qrn_envelope *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.08 * t + np.random.uniform(0, 6.28))
        noise *= qrn_envelope

        # Add occasional static crackles (sparse impulses)
        n_crackles = int(duration * 3)  # ~3 per second
        for _ in range(n_crackles):
            pos = np.random.randint(0, n)
            width = np.random.randint(5, 40)
            amplitude = np.random.uniform(0.5, 2.0)
            end = min(pos + width, n)
            noise[pos:end] += amplitude * np.random.randn(end - pos)

        # Cross-fade the loop point so there's no click/seam
        fade_len = int(0.5 * SAMPLE_RATE)  # 0.5s crossfade
        fade_in = np.linspace(0, 1, fade_len, dtype=np.float32)
        fade_out = 1.0 - fade_in
        noise[:fade_len] = noise[:fade_len] * fade_in + noise[-fade_len:] * fade_out

        # Apply volume (noise_volume * master_volume)
        noise *= self._noise_volume * self._master_volume * 0.3

        # Clip and convert
        noise = np.clip(noise, -1.0, 1.0)
        pcm = (noise * 32767).astype(np.int16)
        stereo = np.column_stack([pcm, pcm])
        self._noise_sound = pygame.sndarray.make_sound(stereo)
        self.noise_channel = pygame.mixer.Channel(2)
        self.noise_channel.play(self._noise_sound, loops=-1)

    def handle_event(self, event, now_ms):
        # D-pad left/right = tune
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self._hold_left = True
                self._tune(-1)
            elif event.key == pygame.K_RIGHT:
                self._hold_right = True
                self._tune(1)
            elif event.key == pygame.K_UP:
                self.vfo_step = min(1.0, self.vfo_step * 2)
            elif event.key == pygame.K_DOWN:
                self.vfo_step = max(0.05, self.vfo_step / 2)
            elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                self._adjust_noise(0.05)
            elif event.key == pygame.K_MINUS:
                self._adjust_noise(-0.05)
            elif event.key == pygame.K_ESCAPE:
                return 'menu'
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self._hold_left = False
            elif event.key == pygame.K_RIGHT:
                self._hold_right = False

        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == BTN_DPAD_LEFT:
                self._hold_left = True
                self._tune(-1)
            elif event.button == BTN_DPAD_RIGHT:
                self._hold_right = True
                self._tune(1)
            elif event.button == BTN_DPAD_UP:
                self.vfo_step = min(1.0, self.vfo_step * 2)
            elif event.button == BTN_DPAD_DOWN:
                self.vfo_step = max(0.05, self.vfo_step / 2)
            elif event.button == BTN_R1:
                self._adjust_noise(0.05)
            elif event.button == BTN_R2:
                self._adjust_noise(-0.05)
            elif event.button == BTN_SELECT:
                return 'menu'

        elif event.type == pygame.JOYBUTTONUP:
            if event.button == BTN_DPAD_LEFT:
                self._hold_left = False
            elif event.button == BTN_DPAD_RIGHT:
                self._hold_right = False

        return None

    def _tune(self, direction):
        self.vfo_freq += direction * self.vfo_step
        self.vfo_freq = max(BAND_START, min(BAND_END, self.vfo_freq))
        self._tune_timer = time.time()

    def _adjust_noise(self, delta):
        """Adjust background noise level."""
        self._noise_volume = max(0.0, min(1.0, self._noise_volume + delta))
        if self.noise_channel:
            self.noise_channel.set_volume(self._noise_volume)

    def update(self, now_ms):
        now = time.time()

        # Continuous tuning when held
        if self._hold_left or self._hold_right:
            if now - self._tune_timer >= self._tune_rate:
                direction = -1 if self._hold_left else 1
                self._tune(direction)

        # Update band simulation
        self.band.update(now)

        # Update waterfall
        self._update_waterfall(now)

        # Update audio based on what's at our VFO frequency
        self._update_audio(now)

        return None

    def _update_waterfall(self, now):
        """Scroll waterfall down one row and add new spectral line."""
        # Scroll down
        self.wf_buffer[1:] = self.wf_buffer[:-1]

        # New top row — base noise floor
        new_row = np.random.randint(5, 20, size=(WF_W, 3), dtype=np.uint8)

        # Add station signals to the waterfall
        for station in self.band.stations:
            if station.transmitting:
                # Map station freq to pixel column
                col = int((station.freq - BAND_START) / BAND_WIDTH * WF_W)
                if 0 <= col < WF_W:
                    # Signal width proportional to strength
                    width = max(2, int(station.strength * 6))
                    intensity = int(station.strength * 220) + 35
                    color_idx = min(255, intensity)
                    color = WF_COLORS[color_idx]

                    for c in range(max(0, col - width), min(WF_W, col + width + 1)):
                        dist = abs(c - col)
                        falloff = max(0, 1.0 - dist / (width + 1))
                        for ch in range(3):
                            new_row[c, ch] = min(255,
                                int(new_row[c, ch] + color[ch] * falloff))

        self.wf_buffer[0] = new_row

    def _update_audio(self, now):
        """Play tone if a station is transmitting near our VFO."""
        signals = self.band.get_signal_at(self.vfo_freq, self.bandwidth)

        if signals:
            # Pick the strongest signal
            strongest = max(signals, key=lambda s: s[1])
            station, strength, freq_offset = strongest

            # Audio frequency: 650 Hz center + offset mapped to audio Hz
            # 1 kHz RF offset = ~600 Hz audio offset
            audio_freq = 650 + freq_offset * 600
            audio_freq = max(200, min(1200, audio_freq))

            if not self._tone_playing or abs(audio_freq - self._current_tone_freq) > 5:
                self._play_tone(audio_freq, strength)
        else:
            if self._tone_playing:
                pygame.mixer.Channel(1).stop()
                self._tone_playing = False

    def _play_tone(self, freq, volume):
        """Generate and play a short tone at the given frequency."""
        n = SAMPLE_RATE // 10  # 0.1s chunk
        t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
        wave = np.sin(2 * np.pi * freq * t) * volume * self._master_volume * 0.6

        # Ramp
        ramp_n = min(64, n // 4)
        if ramp_n > 0:
            ramp = np.linspace(0, 1, ramp_n, dtype=np.float32)
            wave[:ramp_n] *= ramp
            wave[-ramp_n:] *= ramp[::-1]

        pcm = (wave * 32767).astype(np.int16)
        stereo = np.column_stack([pcm, pcm])
        sound = pygame.sndarray.make_sound(stereo)
        pygame.mixer.Channel(1).play(sound, loops=-1)
        self._tone_playing = True
        self._current_tone_freq = freq

    def draw(self, screen, display):
        screen.fill(BLACK)

        # --- Band plan bar at top ---
        bar_y = 5
        bar_h = 18
        for start_khz, end_khz, label, color in BAND_PLAN:
            x1 = int((start_khz - BAND_START) / BAND_WIDTH * SCREEN_W)
            x2 = int((end_khz - BAND_START) / BAND_WIDTH * SCREEN_W)
            rect = pygame.Rect(x1, bar_y, x2 - x1, bar_h)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, GRAY, rect, 1)
            lbl = display.font_small.render(label, True, WHITE)
            screen.blit(lbl, (x1 + 4, bar_y + 1))

        # --- Frequency readout ---
        freq_str = f'{self.vfo_freq:.1f} kHz'
        freq_surf = display.font_medium.render(freq_str, True, AMBER)
        screen.blit(freq_surf, (SCREEN_W // 2 - freq_surf.get_width() // 2, 28))

        # Step and noise indicators
        step_str = f'Step: {self.vfo_step:.2f} kHz'
        step_surf = display.font_small.render(step_str, True, GRAY)
        screen.blit(step_surf, (SCREEN_W - step_surf.get_width() - 10, 35))

        noise_str = f'Noise: {int(self._noise_volume * 100)}%'
        noise_surf = display.font_small.render(noise_str, True, GRAY)
        screen.blit(noise_surf, (10, 35))

        # --- Waterfall display ---
        wf_surface = pygame.surfarray.make_surface(
            np.transpose(self.wf_buffer, (1, 0, 2))
        )
        screen.blit(wf_surface, (WF_X, WF_Y))

        # --- VFO cursor line on waterfall ---
        cursor_x = int((self.vfo_freq - BAND_START) / BAND_WIDTH * WF_W)
        if 0 <= cursor_x < WF_W:
            pygame.draw.line(screen, CURSOR_COLOR,
                             (cursor_x, WF_Y), (cursor_x, WF_Y + WF_H), 1)
            # Small triangle at top
            pygame.draw.polygon(screen, CURSOR_COLOR, [
                (cursor_x, WF_Y),
                (cursor_x - 5, WF_Y - 8),
                (cursor_x + 5, WF_Y - 8),
            ])

        # --- Station markers below waterfall ---
        marker_y = WF_Y + WF_H + 5
        for station in self.band.stations:
            sx = int((station.freq - BAND_START) / BAND_WIDTH * WF_W)
            if 0 <= sx < WF_W:
                color = GREEN if station.transmitting else (40, 60, 40)
                pygame.draw.circle(screen, color, (sx, marker_y + 8), 4)

        # --- Station info (if tuned to one) ---
        signals = self.band.get_signal_at(self.vfo_freq, self.bandwidth)
        info_y = WF_Y + WF_H + 25
        if signals:
            strongest = max(signals, key=lambda s: s[1])
            station = strongest[0]
            # Show what the station is currently sending
            if station.current_message:
                sent = station.current_message[:station.char_index]
                # Show last 40 chars
                sent = sent[-40:]
                msg_surf = display.font_medium.render(sent, True, WHITE)
                screen.blit(msg_surf, (20, info_y))

            call_surf = display.font_small.render(
                f'{station.callsign}  {station.wpm}WPM  S{int(station.strength*9)+1}',
                True, LIGHT_GRAY
            )
            screen.blit(call_surf, (20, info_y + 35))
        else:
            no_sig = display.font_small.render('No signal', True, GRAY)
            screen.blit(no_sig, (20, info_y))

        # --- Help bar ---
        help_surf = display.font_small.render(
            'D-pad = Tune/Step    R1/R2 = Noise    Select = Back', True, GRAY
        )
        screen.blit(help_surf, (SCREEN_W // 2 - help_surf.get_width() // 2,
                                SCREEN_H - 30))

        pygame.display.flip()
