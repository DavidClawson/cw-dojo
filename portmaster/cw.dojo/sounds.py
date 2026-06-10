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


class SoundFX:
    """Manages UI sound effects. Fails silently if files are missing."""

    # Key sound presets: (navigate_file, select_file)
    # 0 = None, 1 = Wood Block, 2 = Soft Tap
    KEY_SOUND_PRESETS = [
        (None, None),
        ('wood-echo.mp3', 'soft-wood-thump.mp3'),
        ('wood-echo.mp3', 'wood-echo.mp3'),
    ]

    def __init__(self):
        self._sounds = {}
        self._muted = False

    def init(self):
        """Call after pygame.mixer is initialized."""
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
        if self._muted and name in ('select', 'navigate'):
            return
        sound = self._sounds.get(name)
        if sound:
            sound.play()

    def set_volume(self, volume):
        """Set volume for all UI sounds."""
        for sound in self._sounds.values():
            if sound:
                sound.set_volume(volume)

    def apply_key_sound(self, key_sound_idx):
        """Change which sounds play for select/navigate based on setting.

        0 = None (muted), 1 = Wood Block, 2 = Soft Tap
        """
        if key_sound_idx == 0:
            self._muted = True
            return

        self._muted = False
        nav_file, sel_file = self.KEY_SOUND_PRESETS[key_sound_idx]
        if nav_file:
            self._load('navigate', nav_file)
        if sel_file:
            self._load('select', sel_file)


# Global instance — import this
sfx = SoundFX()
