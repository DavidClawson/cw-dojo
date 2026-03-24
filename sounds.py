"""UI sound effects for CW Dojo.

Usage:
    from sounds import sfx
    sfx.play('select')    # wood thump on confirm
    sfx.play('navigate')  # light tap on menu move
    sfx.play('levelup')   # chime on promotion
"""

import os
import pygame

ASSETS_DIR = os.path.join(os.path.dirname(__file__) or '.', 'assets')

# Channel 3 reserved for UI sounds (0=sidetone, 1=CW playback, 2=noise)
UI_CHANNEL = 3


class SoundFX:
    """Manages UI sound effects. Fails silently if files are missing."""

    def __init__(self):
        self._sounds = {}
        self._channel = None

    def init(self):
        """Call after pygame.mixer is initialized."""
        self._channel = pygame.mixer.Channel(UI_CHANNEL)
        self._load('select', 'soft-wood-thump.mp3')
        self._load('navigate', 'wood-echo.mp3')
        self._load('levelup', 'soft-chime.mp3')

    def _load(self, name, filename):
        path = os.path.join(ASSETS_DIR, filename)
        try:
            self._sounds[name] = pygame.mixer.Sound(path)
        except Exception:
            self._sounds[name] = None

    def play(self, name):
        sound = self._sounds.get(name)
        if sound and self._channel:
            self._channel.play(sound)

    def set_volume(self, volume):
        for sound in self._sounds.values():
            if sound:
                sound.set_volume(volume)


# Global instance — import this
sfx = SoundFX()
