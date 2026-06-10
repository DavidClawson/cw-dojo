"""Scene system: menu, straight key, Koch trainer, glossary, callsign,
vocab quiz, procedure trainer, and settings."""

import pygame
from audio import Sidetone, CWPlayer
from morse import Decoder, KOCH_ORDER
from sounds import sfx
from koch import KochTrainer
from progress import KochProgress
from profiles import ProfileManager
from settings import Settings
from glossary import GLOSSARY
from vocab_quiz import VocabTrainer, VocabProgress, REQUIRED_CORRECT
from qso_scripts import QSO_SCRIPTS, ScriptRunner
from buttons import (BTN_A, BTN_B, BTN_X, BTN_Y,
                     BTN_L1, BTN_R1, BTN_L2, BTN_R2,
                     BTN_SELECT, BTN_START,
                     BTN_DPAD_UP, BTN_DPAD_DOWN,
                     BTN_DPAD_LEFT, BTN_DPAD_RIGHT)
from ui import Display

# Keyboard mappings for face buttons (desktop testing)
KEY_TO_BTN = {
    pygame.K_d: BTN_A,      # A (right)
    pygame.K_s: BTN_B,      # B (bottom)
    pygame.K_a: BTN_Y,      # Y (left)
    pygame.K_w: BTN_X,      # X (top)
}

MIN_WPM = 5
MAX_WPM = 30


def _is_dpad(event, direction):
    """Check for D-pad input from keyboard or gamepad button."""
    if direction == 'up':
        return ((event.type == pygame.KEYDOWN and event.key == pygame.K_UP) or
                (event.type == pygame.JOYBUTTONDOWN and event.button == BTN_DPAD_UP))
    elif direction == 'down':
        return ((event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN) or
                (event.type == pygame.JOYBUTTONDOWN and event.button == BTN_DPAD_DOWN))
    elif direction == 'left':
        return ((event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT) or
                (event.type == pygame.JOYBUTTONDOWN and event.button == BTN_DPAD_LEFT))
    elif direction == 'right':
        return ((event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT) or
                (event.type == pygame.JOYBUTTONDOWN and event.button == BTN_DPAD_RIGHT))
    return False


def _is_btn(event, btn):
    """Check for a face button press from keyboard or gamepad."""
    if event.type == pygame.JOYBUTTONDOWN and event.button == btn:
        return True
    if event.type == pygame.KEYDOWN:
        return KEY_TO_BTN.get(event.key) == btn
    return False


def _is_back(event):
    """Check for back/menu action (Select button or Escape)."""
    return ((event.type == pygame.JOYBUTTONDOWN and event.button == BTN_SELECT) or
            (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE))


# --- Paddle / key inputs ---
# The 3.5mm jack hardware mod wires a key or paddle to the L1/R1 shoulder
# pads (tip = L1, ring = R1), so the shoulders always act as paddle inputs
# alongside A/Y: L1 = dit / straight key, R1 = dah. Because R1 is the dah
# paddle in iambic mode, the "hear it" control moves to D-pad Left there
# (keyboard R works in either mode).

_DIT_BUTTONS = (BTN_A, BTN_L1)
_DAH_BUTTONS = (BTN_Y, BTN_R1)
_DIT_KEYS = (pygame.K_SPACE, pygame.K_d)
_DAH_KEYS = (pygame.K_a,)


def _is_dit_down(event):
    """Dit paddle (or straight key) pressed: A, L1, Space, or D."""
    return ((event.type == pygame.JOYBUTTONDOWN and event.button in _DIT_BUTTONS) or
            (event.type == pygame.KEYDOWN and event.key in _DIT_KEYS))


def _is_dit_up(event):
    return ((event.type == pygame.JOYBUTTONUP and event.button in _DIT_BUTTONS) or
            (event.type == pygame.KEYUP and event.key in _DIT_KEYS))


def _is_dah_down(event):
    """Dah paddle pressed: Y, R1, or keyboard A."""
    return ((event.type == pygame.JOYBUTTONDOWN and event.button in _DAH_BUTTONS) or
            (event.type == pygame.KEYDOWN and event.key in _DAH_KEYS))


def _is_dah_up(event):
    return ((event.type == pygame.JOYBUTTONUP and event.button in _DAH_BUTTONS) or
            (event.type == pygame.KEYUP and event.key in _DAH_KEYS))


def _is_replay(event, iambic):
    """'Hear it' inside a keying scene: D-pad Left or keyboard R, plus R1
    in straight mode (where it isn't the dah paddle)."""
    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
        return True
    if _is_dpad(event, 'left'):
        return True
    return (not iambic and event.type == pygame.JOYBUTTONDOWN
            and event.button == BTN_R1)


class Scene:
    """Base class for all app scenes."""

    def handle_event(self, event, now_ms):
        return None

    def update(self, now_ms):
        return None

    def draw(self, screen, display):
        pass

    def on_enter(self):
        pass

    def on_exit(self):
        pass


class MenuScene(Scene):
    """Main menu."""

    # Two columns: Practice (left) and Reference (right)
    ITEMS = [
        ('Straight Key', 'straight_key'),
        ('Challenges', 'callsign'),
        ('Koch Trainer', 'koch'),
        ('Vocab Trainer', 'vocab_quiz'),
        ('Band Explorer', 'waterfall'),
        ('QSO Trainer', 'procedure'),
        ('Glossary', 'glossary'),
        ('Settings', 'settings'),
    ]

    def __init__(self):
        self.selected = 0

    def handle_event(self, event, now_ms):
        if _is_dpad(event, 'up'):
            self.selected = (self.selected - 1) % len(self.ITEMS)
            sfx.play('navigate')
        elif _is_dpad(event, 'down'):
            self.selected = (self.selected + 1) % len(self.ITEMS)
            sfx.play('navigate')
        elif _is_dpad(event, 'left'):
            rows = (len(self.ITEMS) + 1) // 2
            self.selected = max(0, self.selected - rows)
            sfx.play('navigate')
        elif _is_dpad(event, 'right'):
            rows = (len(self.ITEMS) + 1) // 2
            self.selected = min(len(self.ITEMS) - 1, self.selected + rows)
            sfx.play('navigate')
        elif (_is_btn(event, BTN_A) or
              (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN)):
            sfx.play('select')
            return self.ITEMS[self.selected][1]
        return None

    def draw(self, screen, display):
        display.draw_menu(
            [item[0] for item in self.ITEMS],
            self.selected
        )


class StraightKeyScene(Scene):
    """Key practice mode — supports straight key and iambic paddles."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.sidetone = None
        self.decoder = None
        self.key_is_down = False
        self.keyer = None  # IambicKeyer for iambic modes

    def on_enter(self):
        from keyer import IambicKeyer
        self.sidetone = Sidetone(
            freq=self.settings.sidetone_freq,
            volume=self.settings.volume
        )
        self.decoder = Decoder(wpm=self.settings.char_wpm)
        self.key_is_down = False
        self.keyer = IambicKeyer(wpm=self.settings.char_wpm)

    def on_exit(self):
        if self.sidetone:
            self.sidetone.key_up()

    @property
    def _is_iambic(self):
        return self.settings.key_mode > 0

    def handle_event(self, event, now_ms):
        if self._is_iambic:
            return self._handle_iambic(event, now_ms)
        return self._handle_straight(event, now_ms)

    def _handle_straight(self, event, now_ms):
        if not self.key_is_down and _is_dit_down(event):
            self.key_is_down = True
            self.sidetone.key_down()
            self.decoder.on_key_down(now_ms)
            return None

        if self.key_is_down and _is_dit_up(event):
            self.key_is_down = False
            self.sidetone.key_up()
            self.decoder.on_key_up(now_ms)
            return None

        return self._handle_common(event, now_ms)

    def _handle_iambic(self, event, now_ms):
        if _is_dit_down(event):
            self.keyer.paddle_dit_down()
        elif _is_dit_up(event):
            self.keyer.paddle_dit_up()

        if _is_dah_down(event):
            self.keyer.paddle_dah_down()
        elif _is_dah_up(event):
            self.keyer.paddle_dah_up()

        return self._handle_common(event, now_ms)

    def _handle_common(self, event, now_ms):
        # WPM adjust
        if _is_dpad(event, 'up'):
            new_wpm = min(self.decoder.wpm + 1, MAX_WPM)
            self.decoder.set_wpm(new_wpm)
            self.keyer.set_wpm(new_wpm)
        elif _is_dpad(event, 'down'):
            new_wpm = max(self.decoder.wpm - 1, MIN_WPM)
            self.decoder.set_wpm(new_wpm)
            self.keyer.set_wpm(new_wpm)

        # Clear decoded text
        if ((event.type == pygame.JOYBUTTONDOWN and event.button == BTN_R2) or
            (event.type == pygame.KEYDOWN and event.key == pygame.K_c)):
            self.decoder.reset()
            self.keyer.reset()

        # Back to menu
        if _is_back(event):
            return 'menu'

        return None

    def update(self, now_ms):
        self.decoder.check_timeout(now_ms)

        # Drive the iambic keyer
        if self._is_iambic and self.keyer:
            was_on = self.keyer.tone_on
            tone_on, new_element = self.keyer.update(now_ms, self.settings.key_mode)

            # Manage sidetone based on keyer output
            if tone_on and not was_on:
                self.sidetone.key_down()
                self.key_is_down = True
                self.decoder.on_key_down(now_ms)
            elif not tone_on and was_on:
                self.sidetone.key_up()
                self.key_is_down = False
                self.decoder.on_key_up(now_ms)

        return None

    def draw(self, screen, display):
        from keyer import MODE_NAMES
        mode_label = MODE_NAMES[self.settings.key_mode] if self.settings.key_mode > 0 else None
        display.draw_straight_key(
            decoded_text=self.decoder.decoded_text,
            current_element=self.decoder.current_element,
            key_is_down=self.key_is_down,
            wpm=self.decoder.wpm,
            key_mode_label=mode_label,
        )


class KochScene(Scene):
    """Koch method receive trainer."""

    IDLE = 'idle'
    PLAYING = 'playing'
    WAITING = 'waiting'
    FEEDBACK = 'feedback'

    FEEDBACK_DURATION_MS = 800

    def __init__(self, settings: Settings, progress: KochProgress):
        self.settings = settings
        self.progress = progress
        self.trainer = KochTrainer(progress)
        self.player = None
        self.state = self.IDLE
        self.feedback_start = 0
        self.promoted = False

    def on_enter(self):
        self.player = CWPlayer(
            freq=self.settings.sidetone_freq,
            char_wpm=self.settings.char_wpm,
            eff_wpm=self.settings.eff_wpm,
            volume=self.settings.volume,
        )
        self.trainer = KochTrainer(self.progress)
        self.state = self.IDLE
        self.promoted = False

    def on_exit(self):
        if self.player:
            self.player.stop()
        self.progress.save()

    def handle_event(self, event, now_ms):
        btn = self._get_button(event)

        # Back to menu (Select or Escape)
        if _is_back(event):
            return 'menu'

        # Replay (R1 or R key)
        if ((event.type == pygame.JOYBUTTONDOWN and event.button == BTN_R1) or
            (event.type == pygame.KEYDOWN and event.key == pygame.K_r)):
            if self.state in (self.WAITING, self.FEEDBACK) and self.trainer.current_char:
                self.player.play_char(self.trainer.current_char)
            return None

        # Hint toggle (D-pad up or H key)
        if _is_dpad(event, 'up') or (event.type == pygame.KEYDOWN and event.key == pygame.K_h):
            self.trainer.show_hints = not self.trainer.show_hints
            return None

        if btn is None:
            return None

        if self.state == self.IDLE:
            if btn == BTN_A:
                self._start_round()

        elif self.state == self.WAITING:
            answer = self._button_to_choice(btn)
            if answer is not None:
                self.trainer.submit_answer(answer)
                self.promoted = self.trainer.check_promotion()
                if self.promoted:
                    sfx.play('levelup')
                self.feedback_start = now_ms
                self.state = self.FEEDBACK

        elif self.state == self.FEEDBACK:
            if btn == BTN_A:
                self._start_round()

        return None

    def update(self, now_ms):
        if self.state == self.PLAYING:
            if not self.player.is_playing():
                self.state = self.WAITING
        elif self.state == self.FEEDBACK:
            if now_ms - self.feedback_start >= self.FEEDBACK_DURATION_MS:
                self._start_round()
        return None

    def draw(self, screen, display):
        # Build hints dict if enabled
        hints = {}
        if self.trainer.show_hints:
            for ch in self.trainer.choices:
                hints[ch] = self.trainer.get_hint(ch)

        display.draw_koch(
            state=self.state,
            current_char=self.trainer.current_char,
            choices=self.trainer.choices,
            last_correct=self.trainer.last_correct,
            session_correct=self.trainer.session_correct,
            session_total=self.trainer.session_total,
            active_chars=self.trainer.active_chars,
            promoted=self.promoted,
            hints=hints,
        )

    def _start_round(self):
        char = self.trainer.start_round()
        self.player.play_char(char)
        self.state = self.PLAYING
        self.promoted = False

    def _get_button(self, event):
        """Extract face button from event, or None."""
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button in (BTN_A, BTN_B, BTN_X, BTN_Y):
                return event.button
        elif event.type == pygame.KEYDOWN:
            return KEY_TO_BTN.get(event.key)
        return None

    def _button_to_choice(self, btn):
        """Map face button to choice index, return the choice character."""
        # Diamond layout: X=top(0), A=right(1), B=bottom(2), Y=left(3)
        btn_order = [BTN_X, BTN_A, BTN_B, BTN_Y]
        if btn in btn_order:
            idx = btn_order.index(btn)
            if idx < len(self.trainer.choices):
                return self.trainer.choices[idx]
        return None


class SettingsScene(Scene):
    """Settings editor."""

    FIELDS = [
        ('sidetone_freq', 'Sidetone Freq', 'Hz', 50, 400, 900),
        ('char_wpm', 'Char Speed', 'WPM', 1, 5, 30),
        ('eff_wpm', 'Effective Speed', 'WPM', 1, 5, 30),
        ('speaker_vol', 'Speaker Vol', '%', 0.05, 0.05, 1.0),
        ('headphone_vol', 'Headphone Vol', '%', 0.01, 0.01, 0.20),
        ('key_sound', 'Key Sound', '', 1, 0, 2),
        ('key_mode', 'Key Mode', '', 1, 0, 2),
    ]

    KEY_SOUND_NAMES = ['None', 'Wood Block', 'Soft Tap']
    KEY_MODE_NAMES = ['Straight', 'Iambic A', 'Iambic B']

    # Action items (not value sliders) — listed after FIELDS
    ACTIONS = [
        ('user_profiles', 'User Profiles'),
        ('reset_koch', 'Reset Koch Progress'),
    ]

    def __init__(self, settings: Settings, progress: KochProgress = None,
                 profile_mgr: ProfileManager = None):
        self.settings = settings
        self.progress = progress
        self.profile_mgr = profile_mgr
        self.selected = 0
        self.player = None
        self.confirming_reset = False
        self.confirm_selection = 1  # 0=Yes, 1=No (default No)

    @property
    def _total_items(self):
        return len(self.FIELDS) + len(self.ACTIONS)

    def on_enter(self):
        self.player = CWPlayer(
            freq=self.settings.sidetone_freq,
            char_wpm=self.settings.char_wpm,
            eff_wpm=self.settings.eff_wpm,
            volume=self.settings.volume,
        )

    def on_exit(self):
        if self.player:
            self.player.stop()

    def handle_event(self, event, now_ms):
        # Confirmation dialog mode
        if self.confirming_reset:
            return self._handle_confirm(event)

        if _is_dpad(event, 'up'):
            self.selected = (self.selected - 1) % self._total_items
        elif _is_dpad(event, 'down'):
            self.selected = (self.selected + 1) % self._total_items
        elif _is_dpad(event, 'left'):
            if self.selected < len(self.FIELDS):
                self._adjust(-1)
        elif _is_dpad(event, 'right') or _is_btn(event, BTN_A):
            if self.selected < len(self.FIELDS):
                if _is_dpad(event, 'right'):
                    self._adjust(1)
            else:
                action_idx = self.selected - len(self.FIELDS)
                action_name = self.ACTIONS[action_idx][0]
                if action_name == 'user_profiles':
                    return 'profiles'
                elif action_name == 'reset_koch':
                    self.confirming_reset = True
                    self.confirm_selection = 1  # default to No
        elif _is_back(event):
            self.settings.save()
            return 'menu'
        return None

    def _handle_confirm(self, event):
        if _is_dpad(event, 'left') or _is_dpad(event, 'right'):
            self.confirm_selection = 1 - self.confirm_selection
        elif _is_btn(event, BTN_A) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            if self.confirm_selection == 0 and self.progress:  # Yes
                self.progress.reset()
            self.confirming_reset = False
        elif _is_back(event):
            self.confirming_reset = False
        return None

    def draw(self, screen, display):
        active_name = self.profile_mgr.active if self.profile_mgr else ''
        items = []
        for field_name, label, unit, step, min_v, max_v in self.FIELDS:
            val = getattr(self.settings, field_name)
            if field_name == 'key_sound':
                items.append((label, self.KEY_SOUND_NAMES[val], ''))
            elif field_name == 'key_mode':
                items.append((label, self.KEY_MODE_NAMES[val], ''))
            elif unit == '%':
                items.append((label, f'{int(round(val * 100))}', unit))
            elif isinstance(val, float):
                items.append((label, f'{val:.1f}', unit))
            else:
                items.append((label, str(val), unit))
        # Add action items
        for action_name, label in self.ACTIONS:
            if action_name == 'user_profiles' and active_name:
                items.append((f'{label} ({active_name})', '', ''))
            else:
                items.append((label, '', ''))
        display.draw_settings(items, self.selected, self.confirming_reset,
                              self.confirm_selection)

    def _adjust(self, direction):
        field_name, _, unit, step, min_v, max_v = self.FIELDS[self.selected]
        val = getattr(self.settings, field_name)
        val = val + direction * step
        if isinstance(min_v, float):
            # Round to 2 decimals first to avoid float drift, then clamp
            val = round(val, 2)
            val = max(min_v, min(max_v, val))
        else:
            val = max(min_v, min(max_v, int(val)))
        setattr(self.settings, field_name, val)
        self._play_preview(field_name)

    def _play_preview(self, field_name):
        """Play a short audio preview after adjusting a setting."""
        if not self.player:
            return
        # Update player to match current settings
        self.player.freq = self.settings.sidetone_freq
        self.player.char_wpm = self.settings.char_wpm
        self.player.eff_wpm = self.settings.eff_wpm
        # Use the specific volume being adjusted, or active volume
        if field_name == 'speaker_vol':
            self.player.volume = self.settings.speaker_vol
        elif field_name == 'headphone_vol':
            self.player.volume = self.settings.headphone_vol
        else:
            self.player.volume = self.settings.volume

        if field_name == 'sidetone_freq':
            # Short tone so you can hear the frequency
            self.player.play_char('E')  # single dit
        elif field_name in ('char_wpm', 'eff_wpm'):
            # dit-dah pattern to hear the speed
            self.player.play_char('R')  # .-.
        elif field_name in ('speaker_vol', 'headphone_vol'):
            # dit-dah at the adjusted volume
            self.player.play_char('A')  # .-
        elif field_name == 'key_sound':
            # Preview the selected key sound
            sfx.apply_key_sound(self.settings.key_sound)
            sfx.play('navigate')


class ProfileScene(Scene):
    """User profile management — list, create, switch, delete profiles."""

    LIST = 'list'
    CREATE = 'create'
    CONFIRM_DELETE = 'confirm_delete'

    # Characters available for name entry
    NAME_CHARS = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ')
    MAX_NAME_LEN = 10

    def __init__(self, profile_mgr: ProfileManager, progress: KochProgress):
        self.mgr = profile_mgr
        self.progress = progress
        self.state = self.LIST
        self.selected = 0
        # Create mode state
        self.new_name = []
        self.name_cursor = 0
        self.new_level = 0  # Koch level (0 = 2 chars)
        self.create_field = 0  # 0=name, 1=level, 2=confirm button
        # Delete confirmation
        self.confirm_selection = 1  # 0=Yes, 1=No

    def on_enter(self):
        self.state = self.LIST
        self.selected = self.mgr.profile_names().index(self.mgr.active) \
            if self.mgr.active in self.mgr.profile_names() else 0

    def handle_event(self, event, now_ms):
        if self.state == self.LIST:
            return self._handle_list(event)
        elif self.state == self.CREATE:
            return self._handle_create(event)
        elif self.state == self.CONFIRM_DELETE:
            return self._handle_delete_confirm(event)
        return None

    def _handle_list(self, event):
        names = self.mgr.profile_names()
        total = len(names) + 1  # profiles + "Create New"

        if _is_dpad(event, 'up'):
            self.selected = (self.selected - 1) % total
        elif _is_dpad(event, 'down'):
            self.selected = (self.selected + 1) % total
        elif _is_btn(event, BTN_A) or _is_dpad(event, 'right') or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            if self.selected < len(names):
                # Switch to selected profile
                name = names[self.selected]
                if name != self.mgr.active:
                    self.mgr.switch_to(name, self.progress)
            else:
                # "Create New" selected
                self.state = self.CREATE
                self.new_name = list('GUEST')
                self.name_cursor = 4  # cursor at end of GUEST
                self.new_level = 0
                self.create_field = 0
        elif _is_btn(event, BTN_X) or (event.type == pygame.KEYDOWN and event.key == pygame.K_x):
            # Delete profile (X button)
            if self.selected < len(names) and len(names) > 1:
                name = names[self.selected]
                if name != self.mgr.active:
                    self.state = self.CONFIRM_DELETE
                    self.confirm_selection = 1
        elif _is_back(event):
            return 'settings'
        return None

    def _handle_create(self, event):
        if _is_back(event):
            self.state = self.LIST
            return None

        if self.create_field == 0:
            # Name entry mode
            if _is_dpad(event, 'up'):
                self._cycle_char(1)
            elif _is_dpad(event, 'down'):
                self._cycle_char(-1)
            elif _is_dpad(event, 'left'):
                if self.name_cursor > 0:
                    self.name_cursor -= 1
            elif _is_dpad(event, 'right'):
                if self.name_cursor < len(self.new_name) - 1:
                    self.name_cursor += 1
                elif len(self.new_name) < self.MAX_NAME_LEN:
                    self.new_name.append('A')
                    self.name_cursor = len(self.new_name) - 1
            elif _is_btn(event, BTN_B) or (event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE):
                # Backspace
                if self.new_name:
                    if self.name_cursor >= len(self.new_name):
                        self.name_cursor = len(self.new_name) - 1
                    self.new_name.pop(self.name_cursor)
                    self.name_cursor = max(0, self.name_cursor - 1)
            elif _is_btn(event, BTN_A) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                self.create_field = 1  # move to level picker
        elif self.create_field == 1:
            # Level picker
            if _is_dpad(event, 'left'):
                self.new_level = max(0, self.new_level - 1)
            elif _is_dpad(event, 'right'):
                self.new_level = min(len(KOCH_ORDER) - 2, self.new_level)
                self.new_level = min(38, self.new_level + 1)
            elif _is_dpad(event, 'up'):
                self.create_field = 0  # back to name
            elif _is_btn(event, BTN_A) or _is_dpad(event, 'down') or \
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                self.create_field = 2  # move to create button
        elif self.create_field == 2:
            # Create button
            if _is_dpad(event, 'up'):
                self.create_field = 1
            elif _is_btn(event, BTN_A) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                name = ''.join(self.new_name).strip()
                if name and name not in self.mgr.profile_names():
                    self.mgr.create_profile(name, self.new_level)
                    self.mgr.switch_to(name, self.progress)
                    self.state = self.LIST
                    names = self.mgr.profile_names()
                    self.selected = names.index(name)
        return None

    def _handle_delete_confirm(self, event):
        if _is_dpad(event, 'left') or _is_dpad(event, 'right'):
            self.confirm_selection = 1 - self.confirm_selection
        elif _is_btn(event, BTN_A) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            if self.confirm_selection == 0:  # Yes
                names = self.mgr.profile_names()
                if self.selected < len(names):
                    self.mgr.delete_profile(names[self.selected])
                    self.selected = min(self.selected, len(self.mgr.profile_names()) - 1)
            self.state = self.LIST
        elif _is_back(event):
            self.state = self.LIST
        return None

    def _cycle_char(self, direction):
        if not self.new_name:
            self.new_name = ['A']
            self.name_cursor = 0
            return
        cur = self.new_name[self.name_cursor]
        idx = self.NAME_CHARS.index(cur) if cur in self.NAME_CHARS else 0
        idx = (idx + direction) % len(self.NAME_CHARS)
        self.new_name[self.name_cursor] = self.NAME_CHARS[idx]

    def draw(self, screen, display):
        if self.state == self.LIST:
            names = self.mgr.profile_names()
            profiles_info = []
            for name in names:
                p = KochProgress.load(self.mgr.progress_file(name))
                n_chars = min(p.level + 2, len(KOCH_ORDER))
                is_active = (name == self.mgr.active)
                profiles_info.append((name, n_chars, p.total_accuracy, is_active))
            display.draw_profiles(profiles_info, self.selected)
        elif self.state == self.CREATE:
            chars = KOCH_ORDER[:self.new_level + 2]
            display.draw_profile_create(
                self.new_name, self.name_cursor,
                self.new_level + 2, chars,
                self.create_field,
            )
        elif self.state == self.CONFIRM_DELETE:
            names = self.mgr.profile_names()
            profiles_info = []
            for name in names:
                p = KochProgress.load(self.mgr.progress_file(name))
                n_chars = min(p.level + 2, len(KOCH_ORDER))
                is_active = (name == self.mgr.active)
                profiles_info.append((name, n_chars, p.total_accuracy, is_active))
            del_name = names[self.selected] if self.selected < len(names) else ''
            display.draw_profiles(profiles_info, self.selected,
                                  confirming_delete=del_name,
                                  confirm_sel=self.confirm_selection)


class GlossaryScene(Scene):
    """Browsable CW glossary with audio playback."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.categories = list(GLOSSARY.keys())
        self.cat_idx = 0
        self.item_idx = 0
        self.player = None

    def on_enter(self):
        self.player = CWPlayer(
            freq=self.settings.sidetone_freq,
            char_wpm=self.settings.char_wpm,
            eff_wpm=self.settings.eff_wpm,
            volume=self.settings.volume,
        )

    def on_exit(self):
        if self.player:
            self.player.stop()

    @property
    def _current_items(self):
        return GLOSSARY[self.categories[self.cat_idx]]

    def handle_event(self, event, now_ms):
        if _is_back(event):
            return 'menu'

        # D-pad up/down = scroll items
        if _is_dpad(event, 'up'):
            self.item_idx = max(0, self.item_idx - 1)
        elif _is_dpad(event, 'down'):
            self.item_idx = min(len(self._current_items) - 1, self.item_idx + 1)

        # D-pad left/right = change category
        elif _is_dpad(event, 'left'):
            self.cat_idx = (self.cat_idx - 1) % len(self.categories)
            self.item_idx = 0
        elif _is_dpad(event, 'right'):
            self.cat_idx = (self.cat_idx + 1) % len(self.categories)
            self.item_idx = 0

        # R1 = play the selected term as CW (consistent "play" button)
        elif ((event.type == pygame.JOYBUTTONDOWN and event.button == BTN_R1) or
              (event.type == pygame.KEYDOWN and event.key == pygame.K_r)):
            items = self._current_items
            if items:
                abbrev = items[self.item_idx][0]
                self.player.play_text(abbrev)

        return None

    def draw(self, screen, display):
        display.draw_glossary(
            category=self.categories[self.cat_idx],
            items=self._current_items,
            selected=self.item_idx,
            num_categories=len(self.categories),
            cat_idx=self.cat_idx,
        )


class CallsignScene(Scene):
    """Practice keying your callsign and common phrases."""

    CHALLENGES = [
        ('Key your callsign', '{call}'),
        ('Call CQ', 'CQ CQ CQ DE {call} {call} K'),
        ('Answer a CQ', '{other} DE {call} {call} K'),
        ('Send 73', '73 DE {call} SK'),
        ('Send signal report', 'UR RST 599 599'),
        ('Send your name', 'NAME HR {name}'),
        ('Send QTH', 'QTH {qth}'),
    ]

    def __init__(self, settings: Settings):
        self.settings = settings
        self.callsign = settings.callsign if hasattr(settings, 'callsign') else ''
        self.challenge_idx = 0
        self.editing_callsign = not bool(self.callsign)
        self.edit_buffer = list(self.callsign)
        self.edit_pos = len(self.edit_buffer)
        self.sidetone = None
        self.decoder = None
        self.key_is_down = False
        self.target_text = ''
        self.active = False  # True when user is keying
        self.keyer = None

    def on_enter(self):
        from keyer import IambicKeyer
        self.sidetone = Sidetone(
            freq=self.settings.sidetone_freq,
            volume=self.settings.volume
        )
        self._cw_player = CWPlayer(
            freq=self.settings.sidetone_freq,
            char_wpm=self.settings.char_wpm,
            eff_wpm=self.settings.eff_wpm,
            volume=self.settings.volume,
        )
        self.decoder = Decoder(wpm=self.settings.char_wpm)
        self.key_is_down = False
        self.keyer = IambicKeyer(wpm=self.settings.char_wpm)
        self.callsign = getattr(self.settings, 'callsign', '')
        if not self.callsign:
            self.editing_callsign = True
            self.edit_buffer = []
            self.edit_pos = 0
        else:
            self.editing_callsign = False
            self._set_challenge()

    def on_exit(self):
        if self.sidetone:
            self.sidetone.key_up()

    @property
    def _is_iambic(self):
        return self.settings.key_mode > 0

    def _set_challenge(self):
        _, template = self.CHALLENGES[self.challenge_idx]
        from band import random_callsign
        self.target_text = template.format(
            call=self.callsign,
            other=random_callsign(),
            name='BOB',
            qth='CA',
        )
        self.decoder.reset()
        self.active = False

    # Character set for callsign editing
    CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/'

    def handle_event(self, event, now_ms):
        if _is_back(event):
            if self.editing_callsign and self.edit_buffer:
                # Save callsign and exit edit mode
                self.callsign = ''.join(self.edit_buffer)
                self.settings.callsign = self.callsign
                self.settings.save()
                self.editing_callsign = False
                self._set_challenge()
                return None
            return 'menu'

        if self.editing_callsign:
            return self._handle_edit(event)
        else:
            return self._handle_challenge(event, now_ms)

    def _handle_edit(self, event):
        """Handle callsign text entry using D-pad.

        D-pad Up/Down = cycle character at cursor position
        A = accept current letter, advance cursor (add another)
        X = delete character at cursor
        B = save callsign and start challenges
        R1 = play the callsign as CW so you can hear it
        """
        # Up/Down = cycle character at current position
        if _is_dpad(event, 'up'):
            if self.edit_pos < len(self.edit_buffer):
                idx = self.CHARS.index(self.edit_buffer[self.edit_pos])
                self.edit_buffer[self.edit_pos] = self.CHARS[(idx + 1) % len(self.CHARS)]
            else:
                self.edit_buffer.append('A')
        elif _is_dpad(event, 'down'):
            if self.edit_pos < len(self.edit_buffer):
                idx = self.CHARS.index(self.edit_buffer[self.edit_pos])
                self.edit_buffer[self.edit_pos] = self.CHARS[(idx - 1) % len(self.CHARS)]
            else:
                self.edit_buffer.append('A')

        # Left/Right = move cursor
        elif _is_dpad(event, 'left'):
            self.edit_pos = max(0, self.edit_pos - 1)
        elif _is_dpad(event, 'right'):
            if self.edit_pos < len(self.edit_buffer):
                self.edit_pos += 1

        # A = accept letter and advance cursor (ready for next char)
        elif _is_btn(event, BTN_A):
            if self.edit_pos < len(self.edit_buffer):
                # Accept current letter, move cursor right
                self.edit_pos += 1

        # B = save callsign and go to challenges
        elif _is_btn(event, BTN_B):
            if self.edit_buffer:
                self.callsign = ''.join(self.edit_buffer)
                self.settings.callsign = self.callsign
                self.settings.save()
                self.editing_callsign = False
                self._set_challenge()

        # X = delete character at cursor
        elif _is_btn(event, BTN_X):
            if self.edit_buffer and self.edit_pos > 0:
                self.edit_buffer.pop(self.edit_pos - 1)
                self.edit_pos -= 1

        # R1 = play callsign as CW
        elif (event.type == pygame.JOYBUTTONDOWN and event.button == BTN_R1) or \
             (event.type == pygame.KEYDOWN and event.key == pygame.K_r):
            if self.edit_buffer and hasattr(self, '_cw_player'):
                self._cw_player.play_text(''.join(self.edit_buffer))

        return None

    def _handle_challenge(self, event, now_ms):
        """Handle keying practice for challenges (straight or iambic)."""
        if self._is_iambic:
            # Iambic paddle events
            if _is_dit_down(event):
                self.keyer.paddle_dit_down()
                self.active = True
            elif _is_dit_up(event):
                self.keyer.paddle_dit_up()

            if _is_dah_down(event):
                self.keyer.paddle_dah_down()
                self.active = True
            elif _is_dah_up(event):
                self.keyer.paddle_dah_up()
        else:
            # Straight key
            if not self.key_is_down and _is_dit_down(event):
                self.key_is_down = True
                self.active = True
                self.sidetone.key_down()
                self.decoder.on_key_down(now_ms)
                return None

            if self.key_is_down and _is_dit_up(event):
                self.key_is_down = False
                self.sidetone.key_up()
                self.decoder.on_key_up(now_ms)
                return None

            # Y = edit callsign (only in straight key mode)
            if _is_btn(event, BTN_Y):
                self.editing_callsign = True
                self.edit_buffer = list(self.callsign)
                self.edit_pos = len(self.edit_buffer)
                return None

        # D-pad up/down = change challenge
        if _is_dpad(event, 'up'):
            self.challenge_idx = (self.challenge_idx - 1) % len(self.CHALLENGES)
            self._set_challenge()
            if self.keyer:
                self.keyer.reset()
        elif _is_dpad(event, 'down'):
            self.challenge_idx = (self.challenge_idx + 1) % len(self.CHALLENGES)
            self._set_challenge()
            if self.keyer:
                self.keyer.reset()

        # X = edit callsign (in iambic mode, since Y is dah paddle)
        elif self._is_iambic and _is_btn(event, BTN_X):
            self.editing_callsign = True
            self.edit_buffer = list(self.callsign)
            self.edit_pos = len(self.edit_buffer)

        # Hear the target played as CW
        elif _is_replay(event, self._is_iambic):
            if self.target_text:
                self._cw_player.play_text(self.target_text)

        # R2 = clear decoded text
        elif ((event.type == pygame.JOYBUTTONDOWN and event.button == BTN_R2) or
              (event.type == pygame.KEYDOWN and event.key == pygame.K_c)):
            self.decoder.reset()
            if self.keyer:
                self.keyer.reset()

        return None

    def update(self, now_ms):
        if not self.editing_callsign and self.decoder:
            self.decoder.check_timeout(now_ms)

        # Drive iambic keyer
        if not self.editing_callsign and self._is_iambic and self.keyer:
            was_on = self.keyer.tone_on
            tone_on, _ = self.keyer.update(now_ms, self.settings.key_mode)
            if tone_on and not was_on:
                self.sidetone.key_down()
                self.key_is_down = True
                self.decoder.on_key_down(now_ms)
            elif not tone_on and was_on:
                self.sidetone.key_up()
                self.key_is_down = False
                self.decoder.on_key_up(now_ms)

        return None

    def draw(self, screen, display):
        if self.editing_callsign:
            display.draw_callsign_edit(
                buffer=''.join(self.edit_buffer),
                cursor_pos=self.edit_pos,
            )
        else:
            challenge_name = self.CHALLENGES[self.challenge_idx][0]
            display.draw_callsign_challenge(
                callsign=self.callsign,
                challenge_name=challenge_name,
                target_text=self.target_text,
                decoded_text=self.decoder.decoded_text if self.decoder else '',
                current_element=self.decoder.current_element if self.decoder else '',
                key_is_down=self.key_is_down,
                iambic=self._is_iambic,
            )


class VocabQuizScene(Scene):
    """Linear vocabulary trainer — learn terms one at a time with keying practice."""

    INTRO = 'intro'       # showing term, meaning, history
    KEYING = 'keying'     # user is keying the term
    FEEDBACK = 'feedback' # correct/wrong after submit
    MASTERED = 'mastered'  # keyed correctly 3x
    COMPLETE = 'complete'  # all terms done

    def __init__(self, settings: Settings):
        self.settings = settings
        self.vocab_progress = VocabProgress.load()
        self.trainer = VocabTrainer(self.vocab_progress)
        self.player = None
        self.sidetone = None
        self.decoder = None
        self.key_is_down = False
        self.keyer = None
        self.state = self.INTRO

    @property
    def _is_iambic(self):
        return self.settings.key_mode > 0

    def on_enter(self):
        from keyer import IambicKeyer
        self.player = CWPlayer(
            freq=self.settings.sidetone_freq,
            char_wpm=self.settings.char_wpm,
            eff_wpm=self.settings.eff_wpm,
            volume=self.settings.volume,
        )
        self.sidetone = Sidetone(
            freq=self.settings.sidetone_freq,
            volume=self.settings.volume,
        )
        self.decoder = Decoder(wpm=self.settings.char_wpm)
        self.key_is_down = False
        self.keyer = IambicKeyer(wpm=self.settings.char_wpm)
        self.vocab_progress = VocabProgress.load()
        self.trainer = VocabTrainer(self.vocab_progress)

        if self.trainer.is_complete:
            self.state = self.COMPLETE
        else:
            self.trainer.start_term()
            self.state = self.INTRO

    def on_exit(self):
        if self.player:
            self.player.stop()
        if self.sidetone:
            self.sidetone.key_up()
        self.vocab_progress.save()

    def handle_event(self, event, now_ms):
        if _is_back(event):
            if self.state in (self.KEYING, self.FEEDBACK):
                self.sidetone.key_up()
                self.key_is_down = False
                if self.keyer:
                    self.keyer.reset()
                self.state = self.INTRO
                return None
            return 'menu'

        if self.state == self.INTRO:
            return self._handle_intro(event)
        elif self.state == self.KEYING:
            return self._handle_keying(event, now_ms)
        elif self.state == self.FEEDBACK:
            return self._handle_feedback(event)
        elif self.state == self.MASTERED:
            return self._handle_mastered(event)
        elif self.state == self.COMPLETE:
            if _is_btn(event, BTN_A):
                return 'menu'
        return None

    def _handle_intro(self, event):
        # R1 = hear the term
        if ((event.type == pygame.JOYBUTTONDOWN and event.button == BTN_R1) or
            (event.type == pygame.KEYDOWN and event.key == pygame.K_r)):
            if self.trainer.term:
                self.player.play_text(self.trainer.term)
            return None

        # D-pad up/down = toggle morse hint
        if _is_dpad(event, 'up') or _is_dpad(event, 'down'):
            self.trainer.show_morse = not self.trainer.show_morse
            return None

        # A = start keying
        if _is_btn(event, BTN_A) or \
           (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            self.decoder.reset()
            self.key_is_down = False
            self.state = self.KEYING
            return None

        return None

    def _handle_keying(self, event, now_ms):
        if self._is_iambic:
            # Iambic paddle events
            if _is_dit_down(event):
                self.keyer.paddle_dit_down()
            elif _is_dit_up(event):
                self.keyer.paddle_dit_up()

            if _is_dah_down(event):
                self.keyer.paddle_dah_down()
            elif _is_dah_up(event):
                self.keyer.paddle_dah_up()
        else:
            # Straight key
            if not self.key_is_down and _is_dit_down(event):
                self.key_is_down = True
                self.sidetone.key_down()
                self.decoder.on_key_down(now_ms)
                return None

            if self.key_is_down and _is_dit_up(event):
                self.key_is_down = False
                self.sidetone.key_up()
                self.decoder.on_key_up(now_ms)
                return None

        # B = submit
        if _is_btn(event, BTN_B):
            self.sidetone.key_up()
            self.key_is_down = False
            if self.keyer:
                self.keyer.reset()
            correct, mastered = self.trainer.check_send(self.decoder.decoded_text)
            if mastered:
                sfx.play('levelup')
                self.state = self.MASTERED
            else:
                self.state = self.FEEDBACK
            return None

        # R2 = clear
        if ((event.type == pygame.JOYBUTTONDOWN and event.button == BTN_R2) or
            (event.type == pygame.KEYDOWN and event.key == pygame.K_c)):
            self.decoder.reset()
            if self.keyer:
                self.keyer.reset()

        # Hear it
        if _is_replay(event, self._is_iambic):
            if self.trainer.term:
                self.player.play_text(self.trainer.term)

        # D-pad up/down = toggle morse hint
        if _is_dpad(event, 'up') or _is_dpad(event, 'down'):
            self.trainer.show_morse = not self.trainer.show_morse

        return None

    def _handle_feedback(self, event):
        if _is_btn(event, BTN_A):
            # Try again
            self.decoder.reset()
            self.state = self.KEYING
        return None

    def _handle_mastered(self, event):
        if _is_btn(event, BTN_A):
            self.trainer.advance()
            if self.trainer.is_complete:
                self.state = self.COMPLETE
            else:
                self.trainer.start_term()
                self.state = self.INTRO
        return None

    def update(self, now_ms):
        if self.state == self.KEYING and self.decoder:
            self.decoder.check_timeout(now_ms)

            # Drive iambic keyer
            if self._is_iambic and self.keyer:
                was_on = self.keyer.tone_on
                tone_on, _ = self.keyer.update(now_ms, self.settings.key_mode)
                if tone_on and not was_on:
                    self.sidetone.key_down()
                    self.key_is_down = True
                    self.decoder.on_key_down(now_ms)
                elif not tone_on and was_on:
                    self.sidetone.key_up()
                    self.key_is_down = False
                    self.decoder.on_key_up(now_ms)

        return None

    def draw(self, screen, display):
        display.draw_vocab_trainer(
            state=self.state,
            trainer=self.trainer,
            decoded_text=self.decoder.decoded_text if self.decoder else '',
            current_element=self.decoder.current_element if self.decoder else '',
            key_is_down=self.key_is_down,
            iambic=self._is_iambic,
        )


class ProcedureScene(Scene):
    """QSO procedure trainer — guided step-by-step conversations."""

    SELECT = 'select'
    LISTENING = 'listening'
    SENDING = 'sending'
    STEP_DONE = 'step_done'
    COMPLETE = 'complete'

    def __init__(self, settings: Settings):
        self.settings = settings
        self.script_idx = 0
        self.runner = None
        self.state = self.SELECT
        self.player = None
        self.sidetone = None
        self.decoder = None
        self.key_is_down = False
        self.keyer = None
        self.steps_keyed = 0
        self.steps_correct = 0

    @property
    def _is_iambic(self):
        return self.settings.key_mode > 0

    def on_enter(self):
        from keyer import IambicKeyer
        self.player = CWPlayer(
            freq=self.settings.sidetone_freq,
            char_wpm=self.settings.char_wpm,
            eff_wpm=self.settings.eff_wpm,
            volume=self.settings.volume,
        )
        self.sidetone = Sidetone(
            freq=self.settings.sidetone_freq,
            volume=self.settings.volume,
        )
        self.decoder = Decoder(wpm=self.settings.char_wpm)
        self.keyer = IambicKeyer(wpm=self.settings.char_wpm)
        self.state = self.SELECT
        self.runner = None
        self.key_is_down = False

    def on_exit(self):
        if self.player:
            self.player.stop()
        if self.sidetone:
            self.sidetone.key_up()

    def handle_event(self, event, now_ms):
        if _is_back(event):
            if self.state != self.SELECT:
                # Go back to script select
                self.state = self.SELECT
                self.runner = None
                if self.sidetone:
                    self.sidetone.key_up()
                self.key_is_down = False
                return None
            return 'menu'

        if self.state == self.SELECT:
            return self._handle_select(event)
        elif self.state == self.LISTENING:
            return self._handle_listening(event)
        elif self.state == self.SENDING:
            return self._handle_sending(event, now_ms)
        elif self.state == self.STEP_DONE:
            return self._handle_step_done(event)
        elif self.state == self.COMPLETE:
            return self._handle_complete(event)
        return None

    def _handle_select(self, event):
        if _is_dpad(event, 'up'):
            self.script_idx = (self.script_idx - 1) % len(QSO_SCRIPTS)
            sfx.play('navigate')
        elif _is_dpad(event, 'down'):
            self.script_idx = (self.script_idx + 1) % len(QSO_SCRIPTS)
            sfx.play('navigate')
        elif _is_btn(event, BTN_A):
            callsign = getattr(self.settings, 'callsign', '') or 'N0CALL'
            self.runner = ScriptRunner(QSO_SCRIPTS[self.script_idx], callsign)
            self.steps_keyed = 0
            self.steps_correct = 0
            self._begin_step()
        return None

    def _begin_step(self):
        """Start the current step."""
        if self.runner.is_complete:
            self.state = self.COMPLETE
            return

        speaker, desc, text = self.runner.current_step
        if speaker == 'them':
            self.player.play_text(text)
            self.state = self.LISTENING
        else:
            self.decoder.reset()
            self.key_is_down = False
            self.state = self.SENDING

    def _handle_listening(self, event):
        # R1 = replay
        if ((event.type == pygame.JOYBUTTONDOWN and event.button == BTN_R1) or
            (event.type == pygame.KEYDOWN and event.key == pygame.K_r)):
            if self.runner and self.runner.current_step:
                _, _, text = self.runner.current_step
                self.player.play_text(text)
        # A = continue (after playback)
        elif _is_btn(event, BTN_A):
            if not self.player.is_playing():
                self.runner.advance()
                self._begin_step()
        return None

    def _handle_sending(self, event, now_ms):
        if self._is_iambic:
            # Iambic paddle events
            if _is_dit_down(event):
                self.keyer.paddle_dit_down()
            elif _is_dit_up(event):
                self.keyer.paddle_dit_up()

            if _is_dah_down(event):
                self.keyer.paddle_dah_down()
            elif _is_dah_up(event):
                self.keyer.paddle_dah_up()
        else:
            # Straight key
            if not self.key_is_down and _is_dit_down(event):
                self.key_is_down = True
                self.sidetone.key_down()
                self.decoder.on_key_down(now_ms)
                return None

            if self.key_is_down and _is_dit_up(event):
                self.key_is_down = False
                self.sidetone.key_up()
                self.decoder.on_key_up(now_ms)
                return None

        # Hear the target
        if _is_replay(event, self._is_iambic):
            if self.runner and self.runner.current_step:
                _, _, text = self.runner.current_step
                self.player.play_text(text)

        # R2 = clear decoded text
        elif ((event.type == pygame.JOYBUTTONDOWN and event.button == BTN_R2) or
              (event.type == pygame.KEYDOWN and event.key == pygame.K_c)):
            self.decoder.reset()
            if self.keyer:
                self.keyer.reset()

        # B = done with this step
        elif _is_btn(event, BTN_B):
            self.sidetone.key_up()
            self.key_is_down = False
            if self.keyer:
                self.keyer.reset()
            self.steps_keyed += 1
            # Simple check: see if decoded text roughly matches target
            if self.runner.current_step:
                _, _, target = self.runner.current_step
                decoded = self.decoder.decoded_text.strip()
                target_clean = target.strip()
                if decoded and target_clean:
                    # Count matching characters
                    matches = sum(a == b for a, b in
                                  zip(decoded.upper(), target_clean.upper()))
                    accuracy = matches / len(target_clean) if target_clean else 0
                    if accuracy >= 0.5:
                        self.steps_correct += 1
            self.state = self.STEP_DONE

        # Start = skip this step
        elif ((event.type == pygame.JOYBUTTONDOWN and event.button == BTN_START) or
              (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN)):
            self.sidetone.key_up()
            self.key_is_down = False
            self.runner.advance()
            self._begin_step()

        return None

    def _handle_step_done(self, event):
        if _is_btn(event, BTN_A):
            self.runner.advance()
            self._begin_step()
        return None

    def _handle_complete(self, event):
        if _is_btn(event, BTN_A):
            self.state = self.SELECT
            self.runner = None
        return None

    def update(self, now_ms):
        if self.state == self.SENDING and self.decoder:
            self.decoder.check_timeout(now_ms)

            # Drive iambic keyer
            if self._is_iambic and self.keyer:
                was_on = self.keyer.tone_on
                tone_on, _ = self.keyer.update(now_ms, self.settings.key_mode)
                if tone_on and not was_on:
                    self.sidetone.key_down()
                    self.key_is_down = True
                    self.decoder.on_key_down(now_ms)
                elif not tone_on and was_on:
                    self.sidetone.key_up()
                    self.key_is_down = False
                    self.decoder.on_key_up(now_ms)

        return None

    def draw(self, screen, display):
        if self.state == self.SELECT:
            display.draw_procedure_select(
                scripts=QSO_SCRIPTS,
                selected=self.script_idx,
            )
        elif self.state == self.COMPLETE:
            display.draw_procedure_complete(
                script_name=self.runner.script['name'],
                steps_keyed=self.steps_keyed,
                steps_correct=self.steps_correct,
                total_steps=self.runner.total_steps,
            )
        else:
            step = self.runner.current_step if self.runner else None
            display.draw_procedure_step(
                state=self.state,
                step=step,
                step_idx=self.runner.step_idx if self.runner else 0,
                total_steps=self.runner.total_steps if self.runner else 0,
                decoded_text=self.decoder.decoded_text if self.decoder else '',
                current_element=self.decoder.current_element if self.decoder else '',
                key_is_down=self.key_is_down,
                script_name=self.runner.script['name'] if self.runner else '',
                iambic=self._is_iambic,
            )
