"""Display helpers for the Morse trainer — 640x480 layout."""

import os
import time
import pygame

# Detect if running on device or desktop
ON_DEVICE = os.environ.get('SDL_VIDEODRIVER') == 'wayland'

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 220, 80)
RED = (220, 50, 50)
AMBER = (255, 180, 0)
DARK_GREEN = (0, 60, 20)
DARK_GRAY = (40, 40, 40)
GRAY = (80, 80, 80)
LIGHT_GRAY = (160, 160, 160)
CREAM = (235, 225, 200)
OLIVE_GREEN = (106, 117, 83)
OLIVE_GREEN_LIGHT = (126, 137, 103)
HIGHLIGHT_BLUE = (40, 60, 100)

SCREEN_W, SCREEN_H = 640, 480


def _find_asset(*names):
    """Find an asset file, checking assets/ subdir and current dir."""
    base = os.path.dirname(__file__) or '.'
    for name in names:
        for path in [os.path.join(base, 'assets', name),
                     os.path.join(base, name)]:
            if os.path.exists(path):
                return path
    return None


def _load_bg(filename, darken=160):
    """Load and darken a background image to screen size."""
    path = _find_asset(filename)
    if not path:
        return None
    try:
        img = pygame.image.load(path).convert()
        img = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
        dark = pygame.Surface((SCREEN_W, SCREEN_H))
        dark.fill((0, 0, 0))
        dark.set_alpha(darken)
        img.blit(dark, (0, 0))
        return img
    except Exception:
        return None


def _rounded_rect_surface(w, h, color, radius=10):
    """Create a surface with a rounded rectangle and alpha."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    r, g, b, a = color if len(color) == 4 else (*color, 255)
    pygame.draw.rect(surf, (r, g, b, a), (0, 0, w, h), border_radius=radius)
    return surf


class Display:
    """Manages the pygame display for the Morse trainer."""

    def __init__(self, screen):
        self.screen = screen

        # Load custom font (Noto Sans), fall back to pygame default
        font_path = _find_asset('NotoSans.ttf')
        if font_path:
            self.font_title = pygame.font.Font(font_path, 52)
            self.font_large = pygame.font.Font(font_path, 56)
            self.font_medium = pygame.font.Font(font_path, 30)
            self.font_small = pygame.font.Font(font_path, 20)
            self.font_element = pygame.font.Font(font_path, 44)
            self.font_choice = pygame.font.Font(font_path, 38)
        else:
            self.font_title = pygame.font.Font(None, 64)
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 40)
            self.font_small = pygame.font.Font(None, 28)
            self.font_element = pygame.font.Font(None, 56)
            self.font_choice = pygame.font.Font(None, 48)

        # Load background images
        self.bg_menu = _load_bg('splash.png', darken=100)
        self.bg_minimal = _load_bg('bg-minimal.png', darken=80)
        self.bg_radio = _load_bg('radio-operator.png', darken=120)

        # Load sakura indicator
        self.sakura = None
        sakura_path = _find_asset('sakura.png')
        if sakura_path:
            try:
                raw = pygame.image.load(sakura_path).convert_alpha()
                self.sakura = pygame.transform.smoothscale(raw, (28, 28))
            except Exception:
                pass

    def _draw_bg(self, bg=None):
        """Draw a background image, or fall back to black."""
        bg = bg or self.bg_menu
        if bg:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill(BLACK)

    def _draw_help_bar(self, text, y=None):
        """Draw help text with a subtle dark background strip."""
        if y is None:
            y = SCREEN_H - 35
        help_surf = self.font_small.render(text, True, LIGHT_GRAY)
        hw = help_surf.get_width()
        hh = help_surf.get_height()
        bar = _rounded_rect_surface(hw + 30, hh + 8, (0, 0, 0, 120), radius=6)
        bx = SCREEN_W // 2 - (hw + 30) // 2
        self.screen.blit(bar, (bx, y - 4))
        self.screen.blit(help_surf, (SCREEN_W // 2 - hw // 2, y))

    def _draw_help_bar_2row(self, row1, row2, y=None):
        """Draw two-row help text with background."""
        if y is None:
            y = SCREEN_H - 55
        s1 = self.font_small.render(row1, True, LIGHT_GRAY)
        s2 = self.font_small.render(row2, True, LIGHT_GRAY)
        max_w = max(s1.get_width(), s2.get_width())
        bar_h = s1.get_height() + s2.get_height() + 12
        bar = _rounded_rect_surface(max_w + 30, bar_h, (0, 0, 0, 120), radius=6)
        bx = SCREEN_W // 2 - (max_w + 30) // 2
        self.screen.blit(bar, (bx, y - 4))
        self.screen.blit(s1, (SCREEN_W // 2 - s1.get_width() // 2, y))
        self.screen.blit(s2, (SCREEN_W // 2 - s2.get_width() // 2,
                              y + s1.get_height() + 4))

    def _draw_cream_pill(self, text, font, x, y, color=DARK_GRAY, pad_x=12, pad_y=4):
        """Draw text on a cream semi-transparent rounded pill."""
        surf = font.render(text, True, color)
        w, h = surf.get_size()
        bg = _rounded_rect_surface(w + pad_x * 2, h + pad_y * 2,
                                   (235, 225, 200, 160), radius=8)
        self.screen.blit(bg, (x - pad_x, y - pad_y))
        self.screen.blit(surf, (x, y))
        return w + pad_x * 2, h + pad_y * 2

    def _draw_status_bar(self):
        """Draw battery percentage and time at the top center."""
        parts = []
        # Time
        parts.append(time.strftime('%H:%M'))
        # Battery
        try:
            with open('/sys/class/power_supply/battery/capacity', 'r') as f:
                pct = f.read().strip()
            with open('/sys/class/power_supply/battery/status', 'r') as f:
                status = f.read().strip()
            icon = '\u26a1' if status == 'Charging' else '\U0001f50b'
            parts.append(f'{icon} {pct}%')
        except Exception:
            pass  # not on device

        if parts:
            text = '    '.join(parts)
            surf = self.font_small.render(text, True, DARK_GRAY)
            x = SCREEN_W // 2 - surf.get_width() // 2
            bg = _rounded_rect_surface(surf.get_width() + 16, surf.get_height() + 6,
                                       (235, 225, 200, 120), radius=6)
            self.screen.blit(bg, (x - 8, 2))
            self.screen.blit(surf, (x, 5))

    # --- Menu ---

    def draw_menu(self, items, selected):
        self._draw_bg(self.bg_menu)
        self._draw_status_bar()

        col_w = 250
        rows = (len(items) + 1) // 2
        item_h = 48
        gap = 10
        total_h = rows * item_h + (rows - 1) * gap
        y_start = (SCREEN_H - total_h) // 2

        # Center columns with equal padding on left, middle, right
        # Total content width = col_w + col_spacing + col_w
        # We want equal margins: margin = (SCREEN_W - 2*col_w - col_spacing) / 2
        col_spacing = 30
        total_w = col_w * 2 + col_spacing
        left_margin = (SCREEN_W - total_w) // 2

        for i, item in enumerate(items):
            col = i // rows
            row = i % rows
            x = left_margin + col * (col_w + col_spacing)
            y = y_start + row * (item_h + gap)

            if i == selected:
                box = _rounded_rect_surface(col_w, item_h, (0, 0, 0, 160), radius=10)
                self.screen.blit(box, (x, y))
                color = WHITE
                # Sakura overlaid on left side without shifting text
                if self.sakura:
                    self.screen.blit(self.sakura, (x + 5, y + (item_h - 28) // 2))
            else:
                box = _rounded_rect_surface(col_w, item_h, (0, 0, 0, 100), radius=10)
                self.screen.blit(box, (x, y))
                color = LIGHT_GRAY

            text = self.font_medium.render(item, True, color)
            tx = x + (col_w - text.get_width()) // 2
            ty = y + (item_h - text.get_height()) // 2
            self.screen.blit(text, (tx, ty))

        self._draw_help_bar(
            "D-pad = Navigate    A = Confirm    Select+Start = Quit" if ON_DEVICE else
            "Arrows = Navigate    D = Confirm    Q = Quit"
        )
        pygame.display.flip()

    # --- Straight Key ---

    def draw_straight_key(self, decoded_text, current_element, key_is_down,
                          wpm, key_mode_label=None):
        self._draw_bg(self.bg_minimal)
        self._draw_status_bar()

        title_text = key_mode_label or "STRAIGHT KEY"
        title = self.font_medium.render(title_text, True, DARK_GRAY)
        self.screen.blit(title, (SCREEN_W - title.get_width() - 20, 15))

        wpm_text = self.font_small.render(f"{wpm} WPM", True, GRAY)
        self.screen.blit(wpm_text, (SCREEN_W - wpm_text.get_width() - 20, 48))

        # Key indicator
        color = GREEN if key_is_down else DARK_GREEN
        pygame.draw.circle(self.screen, color, (SCREEN_W // 2, 110), 20)
        pygame.draw.circle(self.screen, GRAY, (SCREEN_W // 2, 110), 20, 2)

        # Current element — cream pill with dark gray morse
        if current_element:
            spaced = '  '.join(current_element)
            self._draw_cream_pill(spaced, self.font_element,
                SCREEN_W // 2 - self.font_element.size(spaced)[0] // 2, 145,
                color=DARK_GRAY)

        # Decoded text — single line scrolling left with semi-transparent background
        text_y = 220
        text_h = 70
        text_area_w = SCREEN_W - 40
        text_bg = _rounded_rect_surface(text_area_w, text_h, (80, 80, 80, 80), radius=8)
        self.screen.blit(text_bg, (20, text_y))

        if decoded_text:
            text_surf = self.font_large.render(decoded_text, True, WHITE)
            tw = text_surf.get_width()
            th = text_surf.get_height()
            # Center text vertically in the box
            ty = text_y + (text_h - th) // 2
            if tw <= text_area_w - 20:
                self.screen.blit(text_surf, (30, ty))
            else:
                clip_x = tw - (text_area_w - 20)
                clip_rect = pygame.Rect(clip_x, 0, text_area_w - 20, th)
                self.screen.blit(text_surf, (30, ty), area=clip_rect)

        if key_mode_label:
            self._draw_help_bar(
                "A/L1 = Dit    Y/R1 = Dah    U/D = WPM    R2 = Clear    Select = Back"
                if ON_DEVICE else
                "SPACE = Dit    A = Dah    U/D = WPM    C = Clear    ESC = Back"
            )
        else:
            self._draw_help_bar(
                "A/L1 = Key    U/D = WPM    R2 = Clear    Select = Back" if ON_DEVICE else
                "SPACE = Key    U/D = WPM    C = Clear    ESC = Back"
            )
        pygame.display.flip()

    # --- Koch Trainer ---

    def draw_koch(self, state, current_char, choices, last_correct,
                  session_correct, session_total, active_chars, promoted,
                  hints=None):
        self._draw_bg(self.bg_minimal)
        self._draw_status_bar()
        if hints is None:
            hints = {}

        # Title in top right (above container)
        title = self.font_medium.render("KOCH TRAINER", True, DARK_GRAY)
        self.screen.blit(title, (SCREEN_W - title.get_width() - 20, 12))

        # --- Container: full width, below CW Dojo, above help bar ---
        CON_X = 25
        CON_Y = 155
        CON_W = SCREEN_W - 50
        CON_H = SCREEN_H - CON_Y - 45  # stop above help bar
        container = _rounded_rect_surface(CON_W, CON_H, (235, 225, 200, 140), radius=12)
        self.screen.blit(container, (CON_X, CON_Y))

        # 40/60 split
        SPLIT = int(CON_W * 0.40)
        LEFT_X = CON_X + 20          # padding inside container
        LEFT_W = SPLIT - 40
        RIGHT_X = CON_X + SPLIT + 10
        RIGHT_W = CON_W - SPLIT - 30
        RIGHT_CX = RIGHT_X + RIGHT_W // 2  # center of right column

        PAD_TOP = CON_Y + 18  # top padding inside container

        # --- Left column: chars learned + session stats ---

        # Chars learned label
        lbl = self.font_small.render("Chars learned:", True, DARK_GRAY)
        self.screen.blit(lbl, (LEFT_X, PAD_TOP))

        # Wrap active chars into rows that fit the left column
        char_str = '  '.join(active_chars)
        char_surf = self.font_medium.render(char_str, True, OLIVE_GREEN)
        chars_y = PAD_TOP + 32
        if char_surf.get_width() <= LEFT_W:
            self.screen.blit(char_surf, (LEFT_X, chars_y))
            stats_y = chars_y + 50
        else:
            # Split into rows
            mid = len(active_chars) // 2
            row1 = '  '.join(active_chars[:mid])
            row2 = '  '.join(active_chars[mid:])
            s1 = self.font_medium.render(row1, True, OLIVE_GREEN)
            s2 = self.font_medium.render(row2, True, OLIVE_GREEN)
            self.screen.blit(s1, (LEFT_X, chars_y))
            self.screen.blit(s2, (LEFT_X, chars_y + 36))
            stats_y = chars_y + 85

        # Session stats
        if session_total > 0:
            acc = session_correct / session_total * 100
            slbl = self.font_small.render("Session:", True, DARK_GRAY)
            self.screen.blit(slbl, (LEFT_X, stats_y))
            score = f"{session_correct}/{session_total} ({acc:.0f}%)"
            sscore = self.font_medium.render(score, True, OLIVE_GREEN)
            self.screen.blit(sscore, (LEFT_X, stats_y + 28))

        # Promoted banner
        if promoted:
            py = stats_y + 75
            plbl = self.font_medium.render("Level Up!", True, GREEN)
            self.screen.blit(plbl, (LEFT_X, py))
            if self.sakura:
                self.screen.blit(self.sakura, (LEFT_X + plbl.get_width() + 5, py + 2))

        # Hints indicator at bottom of left column
        if hints:
            hs = self.font_small.render("Hints: ON", True, AMBER)
            self.screen.blit(hs, (LEFT_X, CON_Y + CON_H - 30))

        # --- Right column: prompt + diamond choices ---

        if state == 'idle':
            prompt = self.font_medium.render("Press A to start", True, DARK_GRAY)
            self.screen.blit(prompt, (RIGHT_CX - prompt.get_width() // 2,
                                      CON_Y + CON_H // 2 - 15))

        elif state == 'playing':
            prompt = self.font_medium.render("Listen...", True, DARK_GRAY)
            self.screen.blit(prompt, (RIGHT_CX - prompt.get_width() // 2,
                                      CON_Y + CON_H // 2 - 15))

        elif state in ('waiting', 'feedback'):
            prompt_text = "What did you hear?" if state == 'waiting' else ""
            if state == 'feedback':
                if last_correct:
                    prompt_text = "Correct!"
                else:
                    prompt_text = f"Wrong \u2014 it was {current_char}"

            color = GREEN if (state == 'feedback' and last_correct) else \
                    RED if (state == 'feedback' and not last_correct) else DARK_GRAY
            prompt = self.font_small.render(prompt_text, True, color)
            self.screen.blit(prompt, (RIGHT_CX - prompt.get_width() // 2, PAD_TOP))

            # Diamond layout — centered in right column
            if choices:
                labels = ['X', 'A', 'B', 'Y'] if ON_DEVICE else ['W', 'D', 'S', 'A']
                cx = RIGHT_CX
                cy = CON_Y + CON_H // 2 + 10
                h_sp = 90
                v_sp = 65
                positions = [
                    (cx, cy - v_sp),       # top = X
                    (cx + h_sp, cy),       # right = A
                    (cx, cy + v_sp),       # bottom = B
                    (cx - h_sp, cy),       # left = Y
                ]

                for i, (px, py) in enumerate(positions):
                    if i >= len(choices):
                        break
                    ch = choices[i]

                    if state == 'feedback' and ch == current_char:
                        bg_color = (0, 100, 0)
                    elif state == 'feedback' and last_correct is False and ch != current_char:
                        bg_color = (50, 50, 50)
                    else:
                        bg_color = OLIVE_GREEN

                    box_w = 70
                    box_h = 50
                    if hints and ch in hints:
                        box_w = 110
                    btn_rect = pygame.Rect(px - box_w // 2, py - box_h // 2,
                                           box_w, box_h)
                    pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=8)
                    pygame.draw.rect(self.screen, OLIVE_GREEN_LIGHT, btn_rect, 2,
                                     border_radius=8)

                    if hints and ch in hints:
                        char_surf = self.font_medium.render(ch, True, CREAM)
                        hint_surf = self.font_small.render(hints[ch], True, LIGHT_GRAY)
                        total_w = char_surf.get_width() + 6 + hint_surf.get_width()
                        x_start = px - total_w // 2
                        self.screen.blit(char_surf, (x_start,
                                                     py - char_surf.get_height() // 2))
                        self.screen.blit(hint_surf, (x_start + char_surf.get_width() + 6,
                                                     py - hint_surf.get_height() // 2))
                    else:
                        char_surf = self.font_choice.render(ch, True, CREAM)
                        self.screen.blit(char_surf, (px - char_surf.get_width() // 2,
                                                     py - char_surf.get_height() // 2))

                    lbl_surf = self.font_small.render(labels[i], True, GRAY)
                    self.screen.blit(lbl_surf, (px - lbl_surf.get_width() // 2,
                                                py + box_h // 2 + 2))

        self._draw_help_bar(
            "R1 = Replay    D-Up = Hints    Select = Back" if ON_DEVICE else
            "R = Replay    H = Hints    ESC = Back",
            y=SCREEN_H - 28
        )
        pygame.display.flip()

    # --- Settings ---

    def draw_settings(self, items, selected, confirming=False, confirm_sel=1):
        """items: list of (label, value_str, unit)
        Action items have empty value_str and unit."""
        self._draw_bg(self.bg_minimal)
        self._draw_status_bar()

        title = self.font_medium.render("SETTINGS", True, DARK_GRAY)
        self.screen.blit(title, (SCREEN_W - title.get_width() - 20, 15))

        # Scrolling list — show up to 4 items at a time
        visible = 4
        item_h = 58
        gap = 8
        y_start = 140
        scroll_top = max(0, selected - visible + 1)
        visible_items = items[scroll_top:scroll_top + visible]

        # Scroll indicators
        if scroll_top > 0:
            arr = self.font_small.render("\u25b2", True, LIGHT_GRAY)
            self.screen.blit(arr, (SCREEN_W // 2 - arr.get_width() // 2, y_start - 22))
        if scroll_top + visible < len(items):
            bot_y = y_start + visible * (item_h + gap)
            arr = self.font_small.render("\u25bc", True, LIGHT_GRAY)
            self.screen.blit(arr, (SCREEN_W // 2 - arr.get_width() // 2, bot_y))

        for vi, (label, val, unit) in enumerate(visible_items):
            i = scroll_top + vi
            y = y_start + vi * (item_h + gap)
            is_action = (val == '' and unit == '')
            color = WHITE if i == selected else LIGHT_GRAY

            bar_rect = pygame.Rect(40, y, SCREEN_W - 80, item_h)
            if is_action and i == selected:
                # Highlight action items in amber when selected
                box = _rounded_rect_surface(bar_rect.width, bar_rect.height,
                                            (80, 40, 0, 160), radius=10)
            else:
                alpha = 160 if i == selected else 80
                box = _rounded_rect_surface(bar_rect.width, bar_rect.height,
                                            (0, 0, 0, alpha), radius=10)
            self.screen.blit(box, bar_rect.topleft)

            if is_action:
                # Center action label
                act_color = AMBER if i == selected else LIGHT_GRAY
                lbl_surf = self.font_medium.render(label, True, act_color)
                self.screen.blit(lbl_surf, (SCREEN_W // 2 - lbl_surf.get_width() // 2,
                                            y + (item_h - lbl_surf.get_height()) // 2))
            else:
                lbl_surf = self.font_medium.render(label, True, color)
                self.screen.blit(lbl_surf, (60, y + (item_h - lbl_surf.get_height()) // 2))

                val_str = f"<  {val} {unit}  >" if i == selected else f"{val} {unit}"
                val_surf = self.font_medium.render(val_str, True, color)
                self.screen.blit(val_surf, (SCREEN_W - val_surf.get_width() - 60,
                                            y + (item_h - val_surf.get_height()) // 2))

        self._draw_help_bar(
            "D-pad U/D = Navigate    L/R = Adjust    Select = Back" if ON_DEVICE else
            "Arrows U/D = Navigate    L/R = Adjust    ESC = Back"
        )

        # Confirmation dialog overlay
        if confirming:
            self._draw_confirm_dialog(
                "Reset Koch progress?",
                "All levels and stats will be lost.",
                confirm_sel,
            )

        pygame.display.flip()

    def _draw_confirm_dialog(self, title, message, selected):
        """Draw a modal confirmation dialog. selected: 0=Yes, 1=No."""
        # Dim background
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        self.screen.blit(dim, (0, 0))

        # Dialog box
        dlg_w, dlg_h = 400, 180
        dlg_x = (SCREEN_W - dlg_w) // 2
        dlg_y = (SCREEN_H - dlg_h) // 2
        box = _rounded_rect_surface(dlg_w, dlg_h, (30, 30, 30, 240), radius=14)
        self.screen.blit(box, (dlg_x, dlg_y))

        # Title
        title_surf = self.font_medium.render(title, True, AMBER)
        self.screen.blit(title_surf, (SCREEN_W // 2 - title_surf.get_width() // 2,
                                      dlg_y + 24))

        # Message
        msg_surf = self.font_small.render(message, True, LIGHT_GRAY)
        self.screen.blit(msg_surf, (SCREEN_W // 2 - msg_surf.get_width() // 2,
                                    dlg_y + 64))

        # Yes / No buttons
        btn_y = dlg_y + dlg_h - 56
        for bi, label in enumerate(["Yes", "No"]):
            bx = SCREEN_W // 2 + (bi * 120 - 110)
            bw, bh = 100, 40
            if bi == selected:
                btn_bg = _rounded_rect_surface(bw, bh, (220, 50, 50, 200) if bi == 0
                                               else (60, 100, 60, 200), radius=8)
            else:
                btn_bg = _rounded_rect_surface(bw, bh, (60, 60, 60, 160), radius=8)
            self.screen.blit(btn_bg, (bx, btn_y))
            btn_text = self.font_medium.render(label, True,
                                               WHITE if bi == selected else GRAY)
            self.screen.blit(btn_text, (bx + (bw - btn_text.get_width()) // 2,
                                        btn_y + (bh - btn_text.get_height()) // 2))

    # --- Profiles ---

    def draw_profiles(self, profiles_info, selected, confirming_delete='',
                      confirm_sel=1):
        """Draw profile list.
        profiles_info: list of (name, n_chars, accuracy, is_active)
        """
        self._draw_bg(self.bg_minimal)
        self._draw_status_bar()

        title = self.font_medium.render("USER PROFILES", True, DARK_GRAY)
        self.screen.blit(title, (SCREEN_W - title.get_width() - 20, 15))

        visible = 4
        item_h = 58
        gap = 8
        y_start = 130
        total = len(profiles_info) + 1  # +1 for "Create New"
        scroll_top = max(0, selected - visible + 1)

        # Scroll indicators
        if scroll_top > 0:
            arr = self.font_small.render("\u25b2", True, LIGHT_GRAY)
            self.screen.blit(arr, (SCREEN_W // 2 - arr.get_width() // 2, y_start - 22))
        if scroll_top + visible < total:
            bot_y = y_start + visible * (item_h + gap)
            arr = self.font_small.render("\u25bc", True, LIGHT_GRAY)
            self.screen.blit(arr, (SCREEN_W // 2 - arr.get_width() // 2, bot_y))

        for vi in range(min(visible, total - scroll_top)):
            i = scroll_top + vi
            y = y_start + vi * (item_h + gap)
            is_selected = (i == selected)

            bar_rect = pygame.Rect(40, y, SCREEN_W - 80, item_h)
            alpha = 160 if is_selected else 80
            box = _rounded_rect_surface(bar_rect.width, bar_rect.height,
                                        (0, 0, 0, alpha), radius=10)
            self.screen.blit(box, bar_rect.topleft)

            if i < len(profiles_info):
                name, n_chars, accuracy, is_active = profiles_info[i]
                color = WHITE if is_selected else LIGHT_GRAY
                # Name with active indicator
                display_name = f"\u2605 {name}" if is_active else f"  {name}"
                lbl = self.font_medium.render(display_name, True, color)
                self.screen.blit(lbl, (60, y + (item_h - lbl.get_height()) // 2))
                # Stats on right
                pct = int(accuracy * 100) if accuracy > 0 else 0
                stats = f"{n_chars} chars  {pct}%"
                stats_surf = self.font_small.render(stats, True,
                                                    LIGHT_GRAY if is_selected else GRAY)
                self.screen.blit(stats_surf,
                                 (SCREEN_W - stats_surf.get_width() - 60,
                                  y + (item_h - stats_surf.get_height()) // 2))
            else:
                # "Create New" item
                color = GREEN if is_selected else LIGHT_GRAY
                lbl = self.font_medium.render("+ Create New", True, color)
                self.screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2,
                                       y + (item_h - lbl.get_height()) // 2))

        self._draw_help_bar(
            "A = Select    X = Delete    Select = Back" if ON_DEVICE else
            "Enter = Select    X = Delete    ESC = Back"
        )

        # Delete confirmation overlay
        if confirming_delete:
            self._draw_confirm_dialog(
                f"Delete \"{confirming_delete}\"?",
                "This profile and its progress will be removed.",
                confirm_sel,
            )

        pygame.display.flip()

    def draw_profile_create(self, name_chars, cursor, n_chars, koch_chars,
                            active_field):
        """Draw the create-new-profile screen.
        name_chars: list of single chars for the name
        cursor: position in name_chars being edited
        n_chars: total Koch characters at chosen level
        koch_chars: list of chars at chosen level
        active_field: 0=name, 1=level, 2=create button
        """
        self._draw_bg(self.bg_minimal)
        self._draw_status_bar()

        title = self.font_medium.render("NEW PROFILE", True, DARK_GRAY)
        self.screen.blit(title, (SCREEN_W - title.get_width() - 20, 15))

        # Name entry section
        name_y = 120
        name_label = self.font_medium.render("Name:", True,
                                             WHITE if active_field == 0 else LIGHT_GRAY)
        self.screen.blit(name_label, (60, name_y))

        # Draw name characters as individual boxes
        char_w = 32
        char_gap = 4
        name_x_start = 60
        char_y = name_y + 45
        for ci, ch in enumerate(name_chars):
            x = name_x_start + ci * (char_w + char_gap)
            is_cursor = (ci == cursor and active_field == 0)
            bg_color = (255, 180, 0, 200) if is_cursor else (60, 60, 60, 160)
            box = _rounded_rect_surface(char_w, 40, bg_color, radius=6)
            self.screen.blit(box, (x, char_y))
            ch_surf = self.font_medium.render(ch, True, BLACK if is_cursor else WHITE)
            self.screen.blit(ch_surf, (x + (char_w - ch_surf.get_width()) // 2,
                                       char_y + (40 - ch_surf.get_height()) // 2))
            if is_cursor:
                # Up/down arrows above and below
                arr_up = self.font_small.render("\u25b2", True, AMBER)
                self.screen.blit(arr_up, (x + (char_w - arr_up.get_width()) // 2,
                                          char_y - 18))
                arr_dn = self.font_small.render("\u25bc", True, AMBER)
                self.screen.blit(arr_dn, (x + (char_w - arr_dn.get_width()) // 2,
                                          char_y + 42))

        # Koch level section
        level_y = 270
        level_color = WHITE if active_field == 1 else LIGHT_GRAY
        level_box = _rounded_rect_surface(SCREEN_W - 80, 58,
                                          (0, 0, 0, 160 if active_field == 1 else 80),
                                          radius=10)
        self.screen.blit(level_box, (40, level_y))

        level_label = self.font_medium.render("Koch Level:", True, level_color)
        self.screen.blit(level_label, (60, level_y + 14))

        level_val = f"<  {n_chars} chars  >" if active_field == 1 else f"{n_chars} chars"
        level_surf = self.font_medium.render(level_val, True, level_color)
        self.screen.blit(level_surf, (SCREEN_W - level_surf.get_width() - 60,
                                      level_y + 14))

        # Show Koch characters preview
        chars_str = ' '.join(koch_chars[:20])
        if len(koch_chars) > 20:
            chars_str += ' ...'
        chars_surf = self.font_small.render(chars_str, True, LIGHT_GRAY)
        self.screen.blit(chars_surf, (60, level_y + 70))

        # Create button
        btn_y = 380
        btn_w, btn_h = 200, 48
        btn_x = SCREEN_W // 2 - btn_w // 2
        if active_field == 2:
            btn_bg = _rounded_rect_surface(btn_w, btn_h, (0, 140, 60, 200), radius=10)
        else:
            btn_bg = _rounded_rect_surface(btn_w, btn_h, (60, 60, 60, 120), radius=10)
        self.screen.blit(btn_bg, (btn_x, btn_y))
        btn_text = self.font_medium.render("Create", True,
                                           WHITE if active_field == 2 else GRAY)
        self.screen.blit(btn_text, (SCREEN_W // 2 - btn_text.get_width() // 2,
                                    btn_y + (btn_h - btn_text.get_height()) // 2))

        if active_field == 0:
            self._draw_help_bar_2row(
                "U/D = Letter    L/R = Cursor    B = Delete",
                "A = Next    Select = Cancel" if ON_DEVICE else
                "Enter = Next    ESC = Cancel"
            )
        elif active_field == 1:
            self._draw_help_bar(
                "L/R = Adjust    A = Next    U = Back" if ON_DEVICE else
                "L/R = Adjust    Enter = Next    Up = Back"
            )
        else:
            self._draw_help_bar(
                "A = Create    U = Back    Select = Cancel" if ON_DEVICE else
                "Enter = Create    Up = Back    ESC = Cancel"
            )

        pygame.display.flip()

    # --- Glossary ---

    def draw_glossary(self, category, items, selected, num_categories, cat_idx):
        self.screen.fill(BLACK)

        # Category header — dark gray on cream pill, text arrows
        cat_text = f"<  {category}  >"
        self._draw_cream_pill(cat_text, self.font_medium,
            SCREEN_W // 2 - self.font_medium.size(cat_text)[0] // 2, 12)

        # Page indicator
        page = self.font_small.render(f"{cat_idx + 1}/{num_categories}", True, LIGHT_GRAY)
        self.screen.blit(page, (SCREEN_W - page.get_width() - 15, 16))

        # Items list — card-style cells with abbreviation on top, description below
        y_start = 52
        visible = 7
        item_h = 52
        gap = 4
        scroll_top = max(0, selected - visible + 1)
        visible_items = items[scroll_top:scroll_top + visible]

        for i, (abbrev, meaning) in enumerate(visible_items):
            real_idx = scroll_top + i
            y = y_start + i * (item_h + gap)
            is_sel = real_idx == selected

            # Card background
            card = pygame.Rect(12, y, SCREEN_W - 24, item_h)
            if is_sel:
                box = _rounded_rect_surface(card.width, card.height,
                                            (40, 60, 100, 200), radius=8)
            else:
                box = _rounded_rect_surface(card.width, card.height,
                                            (30, 30, 30, 140), radius=8)
            self.screen.blit(box, card.topleft)

            # Abbreviation — left side, bold
            ab_color = WHITE if is_sel else LIGHT_GRAY
            ab_surf = self.font_medium.render(abbrev, True, ab_color)
            self.screen.blit(ab_surf, (24, y + 4))

            # Separator: meaning to the right of abbreviation
            ab_w = ab_surf.get_width()
            sep_x = max(90, ab_w + 40)  # consistent left edge for meanings

            mn_color = LIGHT_GRAY if is_sel else GRAY
            mn_surf = self.font_small.render(meaning, True, mn_color)
            # Vertically center meaning with abbreviation
            mn_y = y + (item_h - mn_surf.get_height()) // 2
            self.screen.blit(mn_surf, (sep_x, mn_y))

        self._draw_help_bar(
            "U/D = Browse    L/R = Category    R1 = Play    Select = Back"
            if ON_DEVICE else
            "Arrows = Browse    L/R = Category    R = Play    ESC = Back",
            y=SCREEN_H - 28
        )
        pygame.display.flip()

    # --- Callsign Trainer ---

    def draw_callsign_edit(self, buffer, cursor_pos):
        from morse import CHAR_TO_MORSE

        self._draw_bg(self.bg_radio)
        self._draw_status_bar()

        # Title below CW Dojo
        title = self.font_medium.render("ENTER YOUR CALLSIGN", True, AMBER)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 90))

        if buffer:
            char_w = 50
            total_w = len(buffer) * char_w
            x_start = SCREEN_W // 2 - total_w // 2

            # Cream background behind callsign letters
            pill_w = total_w + 24
            pill_h = 80
            pill = _rounded_rect_surface(pill_w, pill_h, (235, 225, 200, 160), radius=10)
            self.screen.blit(pill, (x_start - 12, 125))

            for i, ch in enumerate(buffer):
                x = x_start + i * char_w
                is_cursor = (i == cursor_pos)
                color = GREEN if is_cursor else DARK_GRAY

                ch_surf = self.font_title.render(ch, True, color)
                self.screen.blit(ch_surf, (x + char_w // 2 - ch_surf.get_width() // 2, 130))

                if is_cursor:
                    cx = x + char_w // 2
                    pygame.draw.rect(self.screen, GREEN,
                        (cx - 15, 195, 30, 3))

            # Morse pattern — gray on cream pill
            if cursor_pos < len(buffer):
                ch = buffer[cursor_pos]
                pattern = CHAR_TO_MORSE.get(ch, '')
                spaced = '  '.join(pattern)
                self._draw_cream_pill(spaced, self.font_medium,
                    SCREEN_W // 2 - self.font_medium.size(spaced)[0] // 2, 215,
                    color=GRAY)

            if cursor_pos >= len(buffer):
                nx = x_start + len(buffer) * char_w
                plus = self.font_medium.render("+", True, GREEN)
                self.screen.blit(plus, (nx + 10, 145))
                hint = self.font_small.render("D-pad Up", True, LIGHT_GRAY)
                self.screen.blit(hint, (nx - 5, 215))
        else:
            prompt = self.font_medium.render("Press D-pad Up to start", True, LIGHT_GRAY)
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 170))

        # Two-row help bar
        if ON_DEVICE:
            self._draw_help_bar_2row(
                "U/D = Letter    A = Next    X = Del    B = Save",
                "R1 = Hear    Select = Back"
            )
        else:
            self._draw_help_bar_2row(
                "U/D = Letter    D = Next    W = Del    X = Save",
                "R = Hear    ESC = Back"
            )
        pygame.display.flip()

    def draw_callsign_challenge(self, callsign, challenge_name, target_text,
                                decoded_text, current_element, key_is_down,
                                iambic=False):
        self._draw_bg(self.bg_radio)
        self._draw_status_bar()

        # Callsign in top right — cream pill
        self._draw_cream_pill(callsign, self.font_small,
            SCREEN_W - self.font_small.size(callsign)[0] - 20, 14)

        # Challenge name and target below CW Dojo — moved down
        self._draw_cream_pill(challenge_name, self.font_medium,
            SCREEN_W // 2 - self.font_medium.size(challenge_name)[0] // 2, 95)

        # Target text
        target_surf = self.font_medium.render(target_text, True, LIGHT_GRAY)
        self.screen.blit(target_surf, (SCREEN_W // 2 - target_surf.get_width() // 2, 138))

        # Key indicator
        color = GREEN if key_is_down else DARK_GREEN
        pygame.draw.circle(self.screen, color, (SCREEN_W // 2, 190), 15)
        pygame.draw.circle(self.screen, GRAY, (SCREEN_W // 2, 190), 15, 2)

        # Current element — cream pill with dark gray morse
        if current_element:
            spaced = '  '.join(current_element)
            self._draw_cream_pill(spaced, self.font_element,
                SCREEN_W // 2 - self.font_element.size(spaced)[0] // 2, 215,
                color=DARK_GRAY)

        # Decoded text
        self._draw_wrapped_text(decoded_text, 275, self.font_large, WHITE, 28)

        # Two-row help bar
        if ON_DEVICE and iambic:
            self._draw_help_bar_2row(
                "A/L1 = Dit    Y/R1 = Dah    D-Left = Hear    R2 = Clear",
                "U/D = Challenge    X = Edit Call    Select = Back"
            )
        elif ON_DEVICE:
            self._draw_help_bar_2row(
                "A/L1 = Key    R1 = Hear    R2 = Clear    U/D = Challenge",
                "Y = Edit Call    Select = Back"
            )
        else:
            self._draw_help_bar_2row(
                "SPACE = Key    R = Hear    C = Clear    U/D = Challenge",
                "ESC = Back"
            )
        pygame.display.flip()

    # --- Vocab Quiz ---

    def draw_vocab_trainer(self, state, trainer, decoded_text='',
                          current_element='', key_is_down=False,
                          iambic=False):
        """Draw the linear vocabulary trainer."""
        self._draw_bg(self.bg_minimal)
        self._draw_status_bar()

        # Title + progress
        title = self.font_medium.render("VOCAB TRAINER", True, DARK_GRAY)
        self.screen.blit(title, (SCREEN_W - title.get_width() - 20, 12))

        if not trainer.is_complete:
            prog = f"{trainer.term_number}/{trainer.total_terms}"
            prog_surf = self.font_small.render(prog, True, GRAY)
            self.screen.blit(prog_surf, (20, 16))

        # --- Complete screen ---
        if state == 'complete':
            lbl = self.font_large.render("All Done!", True, GREEN)
            self.screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, 120))
            n = len(trainer.progress.mastered)
            sub = self.font_medium.render(f"{n} terms mastered", True, OLIVE_GREEN)
            self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 200))
            congrats = self.font_small.render("Great work! 73", True, LIGHT_GRAY)
            self.screen.blit(congrats, (SCREEN_W // 2 - congrats.get_width() // 2, 260))
            self._draw_help_bar("A = Menu    Select = Back" if ON_DEVICE else
                                "D = Menu    ESC = Back")
            pygame.display.flip()
            return

        term = trainer.term
        meaning = trainer.meaning
        history = trainer.history

        # --- Intro screen: show term, meaning, history ---
        if state == 'intro':
            # Term in large text
            if term:
                self._draw_cream_pill(term, self.font_large,
                    SCREEN_W // 2 - self.font_large.size(term)[0] // 2, 60)

            # Meaning
            if meaning:
                m_surf = self.font_medium.render(meaning, True, DARK_GRAY)
                self.screen.blit(m_surf,
                    (SCREEN_W // 2 - m_surf.get_width() // 2, 125))

            # Morse pattern (if toggled) — cream pill with dark text
            if trainer.show_morse:
                morse = trainer.get_morse_pattern()
                if morse:
                    font = self.font_medium
                    if font.size(morse)[0] > SCREEN_W - 60:
                        font = self.font_small
                    self._draw_cream_pill(morse, font,
                        SCREEN_W // 2 - font.size(morse)[0] // 2, 165,
                        color=DARK_GRAY)

            # History — wrapped text in a container
            if history:
                hist_y = 210
                hist_box = _rounded_rect_surface(SCREEN_W - 50, 160,
                                                  (0, 0, 0, 80), radius=10)
                self.screen.blit(hist_box, (25, hist_y - 5))
                self._draw_wrapped_history(history, 35, hist_y, SCREEN_W - 70)

            # Prompt
            prompt = self.font_small.render("Press A to practice keying", True, LIGHT_GRAY)
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 380))

            self._draw_help_bar_2row(
                "R1 = Hear it    U/D = Morse pattern",
                "A = Start keying    Select = Back"
            )
            pygame.display.flip()
            return

        # --- Keying / Feedback / Mastered screens ---
        # Term + meaning at top
        if term:
            self._draw_cream_pill(term, self.font_large,
                SCREEN_W // 2 - self.font_large.size(term)[0] // 2, 55)

        if meaning:
            m_surf = self.font_small.render(meaning, True, DARK_GRAY)
            self.screen.blit(m_surf, (SCREEN_W // 2 - m_surf.get_width() // 2, 120))

        # Progress dots
        from vocab_quiz import REQUIRED_CORRECT
        dot_y = 155
        dot_spacing = 30
        total_w = REQUIRED_CORRECT * dot_spacing
        dot_start_x = SCREEN_W // 2 - total_w // 2
        streak = trainer.correct_streak
        for i in range(REQUIRED_CORRECT):
            cx = dot_start_x + i * dot_spacing + 10
            if i < streak:
                pygame.draw.circle(self.screen, GREEN, (cx, dot_y), 8)
            else:
                pygame.draw.circle(self.screen, GRAY, (cx, dot_y), 8, 2)

        # Morse hint on cream pill
        if trainer.show_morse:
            morse = trainer.get_morse_pattern()
            if morse:
                self._draw_cream_pill(morse, self.font_small,
                    SCREEN_W // 2 - self.font_small.size(morse)[0] // 2, 175,
                    color=DARK_GRAY)

        if state == 'mastered':
            lbl = self.font_medium.render("Mastered!", True, GREEN)
            self.screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, 230))
            if self.sakura:
                self.screen.blit(self.sakura,
                    (SCREEN_W // 2 + lbl.get_width() // 2 + 5, 232))
            hint = self.font_small.render("A = Next term", True, LIGHT_GRAY)
            self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 300))
            self._draw_help_bar(
                "A = Next    Select = Back" if ON_DEVICE else
                "D = Next    ESC = Back")
            pygame.display.flip()
            return

        if state == 'feedback':
            if trainer.quiz_last_correct:
                fb = self.font_medium.render("Correct!", True, GREEN)
            else:
                fb = self.font_medium.render(f"Not quite — try again", True, RED)
            self.screen.blit(fb, (SCREEN_W // 2 - fb.get_width() // 2, 230))
            # Show what they sent vs target
            sent_lbl = self.font_small.render(
                f"You sent: {decoded_text or '(nothing)'}",
                True, LIGHT_GRAY)
            self.screen.blit(sent_lbl,
                (SCREEN_W // 2 - sent_lbl.get_width() // 2, 280))
            self._draw_help_bar(
                "A = Try again    Select = Back" if ON_DEVICE else
                "D = Try again    ESC = Back")
            pygame.display.flip()
            return

        # --- Active keying ---
        # Key indicator
        color = GREEN if key_is_down else DARK_GREEN
        pygame.draw.circle(self.screen, color, (SCREEN_W // 2, 215), 15)
        pygame.draw.circle(self.screen, GRAY, (SCREEN_W // 2, 215), 15, 2)

        # Current element
        if current_element:
            spaced = '  '.join(current_element)
            self._draw_cream_pill(spaced, self.font_element,
                SCREEN_W // 2 - self.font_element.size(spaced)[0] // 2, 245,
                color=DARK_GRAY)

        # Decoded text
        if decoded_text:
            dec_surf = self.font_medium.render(decoded_text, True, WHITE)
            self.screen.blit(dec_surf,
                (SCREEN_W // 2 - dec_surf.get_width() // 2, 310))

        if iambic:
            self._draw_help_bar_2row(
                "A/L1 = Dit    Y/R1 = Dah    B = Submit    D-Left = Hear",
                "R2 = Clear    U/D = Morse hint    Select = Back"
            )
        else:
            self._draw_help_bar_2row(
                "A/L1 = Key    B = Submit    R1 = Hear    R2 = Clear",
                "U/D = Morse hint    Select = Back"
            )
        pygame.display.flip()

    # --- Procedure Trainer ---

    def draw_procedure_select(self, scripts, selected):
        self._draw_bg(self.bg_radio)
        self._draw_status_bar()

        title = self.font_medium.render("QSO TRAINER", True, AMBER)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 50))

        subtitle = self.font_small.render("Practice real CW conversations", True, LIGHT_GRAY)
        self.screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 90))

        # Script list
        item_h = 72
        gap = 8
        y_start = 130

        for i, script in enumerate(scripts):
            y = y_start + i * (item_h + gap)
            is_sel = (i == selected)

            alpha = 180 if is_sel else 100
            box = _rounded_rect_surface(SCREEN_W - 60, item_h,
                                        (0, 0, 0, alpha), radius=10)
            self.screen.blit(box, (30, y))

            if is_sel and self.sakura:
                self.screen.blit(self.sakura, (38, y + (item_h - 28) // 2))

            name_color = WHITE if is_sel else LIGHT_GRAY
            name_surf = self.font_medium.render(script['name'], True, name_color)
            self.screen.blit(name_surf, (55, y + 8))

            desc_color = LIGHT_GRAY if is_sel else GRAY
            desc_surf = self.font_small.render(script['description'], True, desc_color)
            self.screen.blit(desc_surf, (55, y + 42))

            steps_text = f"{len(script['steps'])} steps"
            steps_surf = self.font_small.render(steps_text, True, GRAY)
            self.screen.blit(steps_surf,
                             (SCREEN_W - 30 - steps_surf.get_width() - 15,
                              y + (item_h - steps_surf.get_height()) // 2))

        self._draw_help_bar(
            "U/D = Choose    A = Start    Select = Back" if ON_DEVICE else
            "U/D = Choose    D = Start    ESC = Back"
        )
        pygame.display.flip()

    def draw_procedure_step(self, state, step, step_idx, total_steps,
                            decoded_text, current_element, key_is_down,
                            script_name, iambic=False):
        self._draw_bg(self.bg_radio)
        self._draw_status_bar()

        if step is None:
            pygame.display.flip()
            return

        speaker, desc, text = step

        # Script name + progress in top area
        self._draw_cream_pill(script_name, self.font_small,
            SCREEN_W - self.font_small.size(script_name)[0] - 20, 14)

        progress = f"Step {step_idx + 1}/{total_steps}"
        prog_surf = self.font_small.render(progress, True, LIGHT_GRAY)
        self.screen.blit(prog_surf, (20, 16))

        # Speaker indicator
        if speaker == 'them':
            speaker_label = "INCOMING"
            speaker_color = AMBER
        else:
            speaker_label = "YOUR TURN"
            speaker_color = GREEN

        lbl = self.font_medium.render(speaker_label, True, speaker_color)
        self.screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, 50))

        # Description
        desc_surf = self.font_small.render(desc, True, LIGHT_GRAY)
        self.screen.blit(desc_surf, (SCREEN_W // 2 - desc_surf.get_width() // 2, 88))

        if state == 'listening':
            # Show the CW text in a cream pill
            self._draw_cream_pill(text, self.font_medium,
                max(20, SCREEN_W // 2 - self.font_medium.size(text)[0] // 2), 130)

            # Hint
            hint_text = "Press A when ready to continue"
            hint = self.font_small.render(hint_text, True, LIGHT_GRAY)
            self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 300))

            self._draw_help_bar(
                "R1 = Replay    A = Continue    Select = Back" if ON_DEVICE else
                "R = Replay    D = Continue    ESC = Back"
            )

        elif state == 'sending':
            # Target text in cream pill
            target_surf = self.font_medium.render(text, True, DARK_GRAY)
            # If too wide, use small font
            if target_surf.get_width() > SCREEN_W - 60:
                target_surf = self.font_small.render(text, True, DARK_GRAY)
            pill_x = max(20, SCREEN_W // 2 - target_surf.get_width() // 2 - 12)
            self._draw_cream_pill(text,
                self.font_medium if self.font_medium.size(text)[0] <= SCREEN_W - 60
                else self.font_small,
                max(20, SCREEN_W // 2 - (self.font_medium if self.font_medium.size(text)[0] <= SCREEN_W - 60 else self.font_small).size(text)[0] // 2),
                125)

            # Key indicator
            color = GREEN if key_is_down else DARK_GREEN
            pygame.draw.circle(self.screen, color, (SCREEN_W // 2, 195), 15)
            pygame.draw.circle(self.screen, GRAY, (SCREEN_W // 2, 195), 15, 2)

            # Current element
            if current_element:
                spaced = '  '.join(current_element)
                self._draw_cream_pill(spaced, self.font_element,
                    SCREEN_W // 2 - self.font_element.size(spaced)[0] // 2, 220,
                    color=DARK_GRAY)

            # Decoded text
            if decoded_text:
                dec_surf = self.font_medium.render(decoded_text, True, WHITE)
                if dec_surf.get_width() > SCREEN_W - 60:
                    # Scroll left
                    clip_w = SCREEN_W - 60
                    clip_x = dec_surf.get_width() - clip_w
                    self.screen.blit(dec_surf, (30, 280),
                                     area=pygame.Rect(clip_x, 0, clip_w, dec_surf.get_height()))
                else:
                    self.screen.blit(dec_surf, (30, 280))

            if iambic:
                self._draw_help_bar_2row(
                    "A/L1 = Dit    Y/R1 = Dah    D-Left = Hear    B = Done",
                    "R2 = Clear    Start = Skip    Select = Back"
                )
            else:
                self._draw_help_bar_2row(
                    "A/L1 = Key    R1 = Hear    R2 = Clear    B = Done",
                    "Start = Skip    Select = Back"
                )

        elif state == 'step_done':
            # Show what was expected vs what was sent
            done_lbl = self.font_medium.render("Step complete!", True, GREEN)
            self.screen.blit(done_lbl, (SCREEN_W // 2 - done_lbl.get_width() // 2, 140))

            exp_lbl = self.font_small.render("Expected:", True, LIGHT_GRAY)
            self.screen.blit(exp_lbl, (30, 200))
            exp_text = self.font_small.render(text, True, WHITE)
            self.screen.blit(exp_text, (30, 225))

            sent_lbl = self.font_small.render("You sent:", True, LIGHT_GRAY)
            self.screen.blit(sent_lbl, (30, 270))
            sent_text = self.font_small.render(decoded_text or "(nothing)", True, AMBER)
            self.screen.blit(sent_text, (30, 295))

            self._draw_help_bar(
                "A = Next step    Select = Back" if ON_DEVICE else
                "D = Next step    ESC = Back"
            )

        pygame.display.flip()

    def draw_procedure_complete(self, script_name, steps_keyed, steps_correct,
                                total_steps):
        self._draw_bg(self.bg_radio)
        self._draw_status_bar()

        # Title
        complete = self.font_large.render("QSO Complete!", True, GREEN)
        self.screen.blit(complete, (SCREEN_W // 2 - complete.get_width() // 2, 80))

        name = self.font_medium.render(script_name, True, AMBER)
        self.screen.blit(name, (SCREEN_W // 2 - name.get_width() // 2, 155))

        # Stats
        if steps_keyed > 0:
            stats = f"Steps keyed: {steps_keyed}    Correct: {steps_correct}"
            stats_surf = self.font_medium.render(stats, True, WHITE)
            self.screen.blit(stats_surf,
                             (SCREEN_W // 2 - stats_surf.get_width() // 2, 220))

        congrats = self.font_small.render("Great practice! 73", True, LIGHT_GRAY)
        self.screen.blit(congrats, (SCREEN_W // 2 - congrats.get_width() // 2, 290))

        self._draw_help_bar(
            "A = Back to scripts    Select = Menu" if ON_DEVICE else
            "D = Back to scripts    ESC = Menu"
        )
        pygame.display.flip()

    # --- Helpers ---

    def _draw_wrapped_text(self, text, y_start, font, color, chars_per_line):
        lines = []
        for i in range(0, max(1, len(text)), chars_per_line):
            lines.append(text[i:i + chars_per_line])
        lines = lines[-4:]  # last 4 lines
        for i, line in enumerate(lines):
            surf = font.render(line, True, color)
            self.screen.blit(surf, (30, y_start + i * 65))

    def _draw_wrapped_history(self, text, x, y, max_width):
        """Word-wrap history text into the available width."""
        words = text.split()
        lines = []
        current_line = ''
        for word in words:
            test = current_line + (' ' if current_line else '') + word
            if self.font_small.size(test)[0] <= max_width:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        line_h = self.font_small.get_height() + 4
        for i, line in enumerate(lines[:6]):  # max 6 lines
            surf = self.font_small.render(line, True, LIGHT_GRAY)
            self.screen.blit(surf, (x, y + i * line_h))
