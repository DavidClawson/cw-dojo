"""Display helpers for the Morse trainer — 640x480 layout."""

import os
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
GRAY = (80, 80, 80)
LIGHT_GRAY = (160, 160, 160)
HIGHLIGHT = (40, 60, 100)

SCREEN_W, SCREEN_H = 640, 480


class Display:
    """Manages the pygame display for the Morse trainer."""

    def __init__(self, screen):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 64)
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 28)
        self.font_element = pygame.font.Font(None, 56)
        self.font_choice = pygame.font.Font(None, 48)

    # --- Menu ---

    def draw_menu(self, items, selected):
        self.screen.fill(BLACK)

        # Title
        title = self.font_title.render("CW DOJO", True, AMBER)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 60))

        subtitle = self.font_small.render("Morse Code Trainer", True, GRAY)
        self.screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 120))

        # Menu items — two columns if 5+ items
        y_start = 180
        col_w = 280
        col_spacing = 50
        rows = (len(items) + 1) // 2  # items per column

        for i, item in enumerate(items):
            col = i // rows  # 0 = left, 1 = right
            row = i % rows
            x = 40 + col * (col_w + col_spacing)
            y = y_start + row * 55

            color = WHITE if i == selected else GRAY
            if i == selected:
                bar_rect = pygame.Rect(x - 5, y - 5, col_w, 45)
                pygame.draw.rect(self.screen, HIGHLIGHT, bar_rect, border_radius=6)
            text = self.font_medium.render(item, True, color)
            self.screen.blit(text, (x + 10, y))

        # Help
        help_text = self.font_small.render(
            "D-pad = Navigate    A = Confirm    Select+Start = Quit" if ON_DEVICE else
            "Arrows = Navigate    D = Confirm    Q = Quit", True, GRAY
        )
        self.screen.blit(help_text, (SCREEN_W // 2 - help_text.get_width() // 2,
                                     SCREEN_H - 40))
        pygame.display.flip()

    # --- Straight Key ---

    def draw_straight_key(self, decoded_text, current_element, key_is_down, wpm):
        self.screen.fill(BLACK)

        title = self.font_medium.render("STRAIGHT KEY", True, AMBER)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 15))

        wpm_text = self.font_small.render(f"{wpm} WPM", True, GRAY)
        self.screen.blit(wpm_text, (SCREEN_W - wpm_text.get_width() - 20, 20))

        # Key indicator
        color = GREEN if key_is_down else DARK_GREEN
        pygame.draw.circle(self.screen, color, (SCREEN_W // 2, 80), 20)
        pygame.draw.circle(self.screen, GRAY, (SCREEN_W // 2, 80), 20, 2)

        # Current element
        if current_element:
            spaced = '  '.join(current_element)
            elem_surf = self.font_element.render(spaced, True, GREEN)
            self.screen.blit(elem_surf,
                             (SCREEN_W // 2 - elem_surf.get_width() // 2, 120))

        # Decoded text
        self._draw_wrapped_text(decoded_text, 200, self.font_large, WHITE, 28)

        # Help
        help_surf = self.font_small.render(
            "A = Key    D-pad U/D = WPM    Select = Back" if ON_DEVICE else
            "SPACE = Key    Arrows U/D = WPM    ESC = Back", True, GRAY
        )
        self.screen.blit(help_surf, (SCREEN_W // 2 - help_surf.get_width() // 2,
                                     SCREEN_H - 40))
        pygame.display.flip()

    # --- Koch Trainer ---

    def draw_koch(self, state, current_char, choices, last_correct,
                  session_correct, session_total, active_chars, promoted,
                  hints=None):
        self.screen.fill(BLACK)
        if hints is None:
            hints = {}

        # Title and level
        title = self.font_medium.render("KOCH TRAINER", True, AMBER)
        self.screen.blit(title, (20, 15))

        level_str = ' '.join(active_chars)
        level_surf = self.font_small.render(f"Chars: {level_str}", True, GRAY)
        self.screen.blit(level_surf, (20, 50))

        if state == 'idle':
            prompt = self.font_medium.render("Press A to start", True, WHITE)
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 200))

        elif state == 'playing':
            prompt = self.font_medium.render("Listen...", True, LIGHT_GRAY)
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 100))

        elif state in ('waiting', 'feedback'):
            prompt_text = "What did you hear?" if state == 'waiting' else ""
            if state == 'feedback':
                if last_correct:
                    prompt_text = "Correct!"
                else:
                    prompt_text = f"Wrong — it was {current_char}"

            color = GREEN if (state == 'feedback' and last_correct) else \
                    RED if (state == 'feedback' and not last_correct) else WHITE
            prompt = self.font_medium.render(prompt_text, True, color)
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 100))

            # Diamond layout for 4 choices matching face buttons
            # X=top, Y=left, A=right, B=bottom
            if choices:
                cx, cy = SCREEN_W // 2, 250
                h_spacing = 130
                v_spacing = 80
                positions = [
                    (cx, cy - v_spacing),         # X (top)
                    (cx + h_spacing, cy),         # A (right)
                    (cx, cy + v_spacing),         # B (bottom)
                    (cx - h_spacing, cy),         # Y (left)
                ]
                labels = ['X', 'A', 'B', 'Y'] if ON_DEVICE else ['W', 'D', 'S', 'A']

                for i, (px, py) in enumerate(positions):
                    if i >= len(choices):
                        break
                    ch = choices[i]

                    # Highlight correct answer during feedback
                    if state == 'feedback' and ch == current_char:
                        bg_color = (0, 80, 0)
                    elif state == 'feedback' and last_correct is False and ch != current_char:
                        bg_color = (40, 40, 40)
                    else:
                        bg_color = HIGHLIGHT

                    # Wider box if showing hints
                    box_w = 110 if hints else 70
                    btn_rect = pygame.Rect(px - box_w // 2, py - 25, box_w, 50)
                    pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=8)
                    pygame.draw.rect(self.screen, GRAY, btn_rect, 2, border_radius=8)

                    if hints and ch in hints:
                        # Show character + morse pattern
                        char_surf = self.font_medium.render(ch, True, WHITE)
                        hint_surf = self.font_small.render(hints[ch], True, LIGHT_GRAY)
                        total_w = char_surf.get_width() + 8 + hint_surf.get_width()
                        x_start = px - total_w // 2
                        self.screen.blit(char_surf, (x_start,
                                                     py - char_surf.get_height() // 2))
                        self.screen.blit(hint_surf, (x_start + char_surf.get_width() + 8,
                                                     py - hint_surf.get_height() // 2))
                    else:
                        char_surf = self.font_choice.render(ch, True, WHITE)
                        self.screen.blit(char_surf, (px - char_surf.get_width() // 2,
                                                     py - char_surf.get_height() // 2))

                    lbl_surf = self.font_small.render(labels[i], True, GRAY)
                    self.screen.blit(lbl_surf, (px - lbl_surf.get_width() // 2,
                                                py + 28))

        # Promoted banner
        if promoted:
            banner = self.font_medium.render("Level Up! New character unlocked!", True, GREEN)
            self.screen.blit(banner, (SCREEN_W // 2 - banner.get_width() // 2, 370))

        # Stats
        if session_total > 0:
            acc = session_correct / session_total * 100
            stats = self.font_small.render(
                f"Session: {session_correct}/{session_total} ({acc:.0f}%)", True, LIGHT_GRAY
            )
            self.screen.blit(stats, (20, SCREEN_H - 70))

        # Hint indicator
        hint_status = "Hints: ON" if hints else ""
        if hint_status:
            hs = self.font_small.render(hint_status, True, AMBER)
            self.screen.blit(hs, (SCREEN_W - hs.get_width() - 20, SCREEN_H - 70))

        # Help
        help_surf = self.font_small.render(
            "R1 = Replay    D-Up = Hints    Select = Back" if ON_DEVICE else
            "R = Replay    H = Hints    ESC = Back", True, GRAY
        )
        self.screen.blit(help_surf, (SCREEN_W // 2 - help_surf.get_width() // 2,
                                     SCREEN_H - 40))
        pygame.display.flip()

    # --- Settings ---

    def draw_settings(self, items, selected, confirming=False, confirm_sel=1):
        """items: list of (label, value_str, unit)
        Action items have empty value_str and unit."""
        self.screen.fill(BLACK)

        title = self.font_medium.render("SETTINGS", True, AMBER)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 30))

        y_start = 120
        for i, (label, val, unit) in enumerate(items):
            y = y_start + i * 70
            is_action = (val == '' and unit == '')
            color = WHITE if i == selected else GRAY

            if i == selected:
                bar_rect = pygame.Rect(40, y - 5, SCREEN_W - 80, 55)
                bar_color = (80, 40, 0) if is_action else HIGHLIGHT
                pygame.draw.rect(self.screen, bar_color, bar_rect, border_radius=6)

            if is_action:
                act_color = AMBER if i == selected else GRAY
                lbl_surf = self.font_medium.render(label, True, act_color)
                self.screen.blit(lbl_surf, (SCREEN_W // 2 - lbl_surf.get_width() // 2, y))
            else:
                lbl_surf = self.font_medium.render(label, True, color)
                self.screen.blit(lbl_surf, (60, y))

                val_str = f"< {val} {unit} >" if i == selected else f"{val} {unit}"
                val_surf = self.font_medium.render(val_str, True, color)
                self.screen.blit(val_surf, (SCREEN_W - val_surf.get_width() - 60, y))

        help_surf = self.font_small.render(
            "D-pad U/D = Navigate    L/R = Adjust    Select = Back" if ON_DEVICE else
            "Arrows U/D = Navigate    L/R = Adjust    ESC = Back", True, GRAY
        )
        self.screen.blit(help_surf, (SCREEN_W // 2 - help_surf.get_width() // 2,
                                     SCREEN_H - 40))

        if confirming:
            self._draw_confirm_dialog(
                "Reset Koch progress?",
                "All levels and stats will be lost.",
                confirm_sel,
            )

        pygame.display.flip()

    def _draw_confirm_dialog(self, title, message, selected):
        """Draw a modal confirmation dialog. selected: 0=Yes, 1=No."""
        dim = pygame.Surface((SCREEN_W, SCREEN_H))
        dim.fill(BLACK)
        dim.set_alpha(160)
        self.screen.blit(dim, (0, 0))

        dlg_w, dlg_h = 400, 180
        dlg_x = (SCREEN_W - dlg_w) // 2
        dlg_y = (SCREEN_H - dlg_h) // 2
        pygame.draw.rect(self.screen, (30, 30, 30),
                         (dlg_x, dlg_y, dlg_w, dlg_h), border_radius=14)
        pygame.draw.rect(self.screen, GRAY,
                         (dlg_x, dlg_y, dlg_w, dlg_h), width=2, border_radius=14)

        title_surf = self.font_medium.render(title, True, AMBER)
        self.screen.blit(title_surf, (SCREEN_W // 2 - title_surf.get_width() // 2,
                                      dlg_y + 24))

        msg_surf = self.font_small.render(message, True, LIGHT_GRAY)
        self.screen.blit(msg_surf, (SCREEN_W // 2 - msg_surf.get_width() // 2,
                                    dlg_y + 64))

        btn_y = dlg_y + dlg_h - 56
        for bi, label in enumerate(["Yes", "No"]):
            bx = SCREEN_W // 2 + (bi * 120 - 110)
            bw, bh = 100, 40
            if bi == selected:
                color = RED if bi == 0 else GREEN
                pygame.draw.rect(self.screen, color, (bx, btn_y, bw, bh),
                                 border_radius=8)
            else:
                pygame.draw.rect(self.screen, GRAY, (bx, btn_y, bw, bh),
                                 width=2, border_radius=8)
            btn_text = self.font_medium.render(label, True,
                                               WHITE if bi == selected else GRAY)
            self.screen.blit(btn_text, (bx + (bw - btn_text.get_width()) // 2,
                                        btn_y + (bh - btn_text.get_height()) // 2))

    # --- Profiles ---

    def draw_profiles(self, profiles_info, selected, confirming_delete='',
                      confirm_sel=1):
        """Draw profile list. profiles_info: list of (name, n_chars, accuracy, is_active)"""
        self.screen.fill(BLACK)

        title = self.font_medium.render("USER PROFILES", True, AMBER)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 30))

        y_start = 100
        total = len(profiles_info) + 1
        for i in range(total):
            y = y_start + i * 65
            is_selected = (i == selected)

            if is_selected:
                bar_rect = pygame.Rect(40, y - 5, SCREEN_W - 80, 55)
                pygame.draw.rect(self.screen, HIGHLIGHT, bar_rect, border_radius=6)

            if i < len(profiles_info):
                name, n_chars, accuracy, is_active = profiles_info[i]
                color = WHITE if is_selected else GRAY
                display_name = f"\u2605 {name}" if is_active else f"  {name}"
                lbl = self.font_medium.render(display_name, True, color)
                self.screen.blit(lbl, (60, y))
                pct = int(accuracy * 100) if accuracy > 0 else 0
                stats = f"{n_chars} chars  {pct}%"
                stats_surf = self.font_small.render(stats, True,
                                                    LIGHT_GRAY if is_selected else GRAY)
                self.screen.blit(stats_surf,
                                 (SCREEN_W - stats_surf.get_width() - 60, y + 5))
            else:
                color = GREEN if is_selected else GRAY
                lbl = self.font_medium.render("+ Create New", True, color)
                self.screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, y))

        help_surf = self.font_small.render(
            "A = Select    X = Delete    Select = Back" if ON_DEVICE else
            "Enter = Select    X = Delete    ESC = Back", True, GRAY
        )
        self.screen.blit(help_surf, (SCREEN_W // 2 - help_surf.get_width() // 2,
                                     SCREEN_H - 40))

        if confirming_delete:
            self._draw_confirm_dialog(
                f"Delete \"{confirming_delete}\"?",
                "This profile and its progress will be removed.",
                confirm_sel,
            )

        pygame.display.flip()

    def draw_profile_create(self, name_chars, cursor, n_chars, koch_chars,
                            active_field):
        """Draw the create-new-profile screen."""
        self.screen.fill(BLACK)

        title = self.font_medium.render("NEW PROFILE", True, AMBER)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 30))

        # Name entry
        name_y = 100
        name_label = self.font_medium.render("Name:", True,
                                             WHITE if active_field == 0 else GRAY)
        self.screen.blit(name_label, (60, name_y))

        char_w = 32
        char_gap = 4
        name_x_start = 60
        char_y = name_y + 45
        for ci, ch in enumerate(name_chars):
            x = name_x_start + ci * (char_w + char_gap)
            is_cursor = (ci == cursor and active_field == 0)
            if is_cursor:
                pygame.draw.rect(self.screen, AMBER, (x, char_y, char_w, 40),
                                 border_radius=6)
                ch_surf = self.font_medium.render(ch, True, BLACK)
                arr_up = self.font_small.render("\u25b2", True, AMBER)
                self.screen.blit(arr_up, (x + (char_w - arr_up.get_width()) // 2,
                                          char_y - 18))
                arr_dn = self.font_small.render("\u25bc", True, AMBER)
                self.screen.blit(arr_dn, (x + (char_w - arr_dn.get_width()) // 2,
                                          char_y + 42))
            else:
                pygame.draw.rect(self.screen, GRAY, (x, char_y, char_w, 40),
                                 width=1, border_radius=6)
                ch_surf = self.font_medium.render(ch, True, WHITE)
            self.screen.blit(ch_surf, (x + (char_w - ch_surf.get_width()) // 2,
                                       char_y + (40 - ch_surf.get_height()) // 2))

        # Koch level
        level_y = 250
        level_color = WHITE if active_field == 1 else GRAY
        if active_field == 1:
            pygame.draw.rect(self.screen, HIGHLIGHT,
                             (40, level_y - 5, SCREEN_W - 80, 50), border_radius=6)
        level_label = self.font_medium.render("Koch Level:", True, level_color)
        self.screen.blit(level_label, (60, level_y))
        level_val = f"< {n_chars} chars >" if active_field == 1 else f"{n_chars} chars"
        level_surf = self.font_medium.render(level_val, True, level_color)
        self.screen.blit(level_surf, (SCREEN_W - level_surf.get_width() - 60, level_y))

        chars_str = ' '.join(koch_chars[:20])
        if len(koch_chars) > 20:
            chars_str += ' ...'
        chars_surf = self.font_small.render(chars_str, True, LIGHT_GRAY)
        self.screen.blit(chars_surf, (60, level_y + 55))

        # Create button
        btn_y = 370
        btn_w, btn_h = 200, 48
        btn_x = SCREEN_W // 2 - btn_w // 2
        if active_field == 2:
            pygame.draw.rect(self.screen, GREEN, (btn_x, btn_y, btn_w, btn_h),
                             border_radius=10)
        else:
            pygame.draw.rect(self.screen, GRAY, (btn_x, btn_y, btn_w, btn_h),
                             width=2, border_radius=10)
        btn_text = self.font_medium.render("Create", True,
                                           WHITE if active_field == 2 else GRAY)
        self.screen.blit(btn_text, (SCREEN_W // 2 - btn_text.get_width() // 2,
                                    btn_y + (btn_h - btn_text.get_height()) // 2))

        if active_field == 0:
            help1 = "U/D = Letter    L/R = Cursor    B = Delete"
            help2 = "A = Next    Select = Cancel" if ON_DEVICE else \
                    "Enter = Next    ESC = Cancel"
            s1 = self.font_small.render(help1, True, GRAY)
            s2 = self.font_small.render(help2, True, GRAY)
            self.screen.blit(s1, (SCREEN_W // 2 - s1.get_width() // 2, SCREEN_H - 55))
            self.screen.blit(s2, (SCREEN_W // 2 - s2.get_width() // 2, SCREEN_H - 30))
        elif active_field == 1:
            h = self.font_small.render(
                "L/R = Adjust    A = Next    U = Back" if ON_DEVICE else
                "L/R = Adjust    Enter = Next    Up = Back", True, GRAY)
            self.screen.blit(h, (SCREEN_W // 2 - h.get_width() // 2, SCREEN_H - 40))
        else:
            h = self.font_small.render(
                "A = Create    U = Back    Select = Cancel" if ON_DEVICE else
                "Enter = Create    Up = Back    ESC = Cancel", True, GRAY)
            self.screen.blit(h, (SCREEN_W // 2 - h.get_width() // 2, SCREEN_H - 40))

        pygame.display.flip()

    # --- Glossary ---

    def draw_glossary(self, category, items, selected, num_categories, cat_idx):
        self.screen.fill(BLACK)

        # Category header with arrows
        cat_text = f"< {category} >"
        cat_surf = self.font_medium.render(cat_text, True, AMBER)
        self.screen.blit(cat_surf, (SCREEN_W // 2 - cat_surf.get_width() // 2, 15))

        # Page indicator
        page = self.font_small.render(f"{cat_idx + 1}/{num_categories}", True, GRAY)
        self.screen.blit(page, (SCREEN_W - page.get_width() - 20, 20))

        # Items list (scrollable window of 7 items)
        y_start = 65
        visible = 7
        scroll_top = max(0, selected - visible + 1)
        visible_items = items[scroll_top:scroll_top + visible]

        for i, (abbrev, meaning) in enumerate(visible_items):
            real_idx = scroll_top + i
            y = y_start + i * 52
            color = WHITE if real_idx == selected else GRAY

            if real_idx == selected:
                bar = pygame.Rect(10, y - 2, SCREEN_W - 20, 46)
                pygame.draw.rect(self.screen, HIGHLIGHT, bar, border_radius=4)

            # Abbreviation (bold/large)
            ab_surf = self.font_medium.render(abbrev, True, color)
            self.screen.blit(ab_surf, (20, y))

            # Meaning
            mn_surf = self.font_small.render(meaning, True, LIGHT_GRAY if real_idx == selected else GRAY)
            self.screen.blit(mn_surf, (20, y + 26))

        # Help
        help_surf = self.font_small.render(
            "D-pad U/D = Browse    L/R = Category    R1 = Play    Select = Back"
            if ON_DEVICE else
            "Arrows = Browse    L/R = Category    R = Play    ESC = Back",
            True, GRAY
        )
        self.screen.blit(help_surf, (SCREEN_W // 2 - help_surf.get_width() // 2,
                                     SCREEN_H - 30))
        pygame.display.flip()

    # --- Callsign Trainer ---

    def draw_callsign_edit(self, buffer, cursor_pos):
        from morse import CHAR_TO_MORSE

        self.screen.fill(BLACK)

        title = self.font_medium.render("ENTER YOUR CALLSIGN", True, AMBER)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 30))

        if buffer:
            # Render characters — only show morse for highlighted letter
            char_w = 50
            total_w = len(buffer) * char_w
            x_start = SCREEN_W // 2 - total_w // 2

            for i, ch in enumerate(buffer):
                x = x_start + i * char_w
                is_cursor = (i == cursor_pos)
                color = GREEN if is_cursor else WHITE

                # Character
                ch_surf = self.font_title.render(ch, True, color)
                self.screen.blit(ch_surf, (x + char_w // 2 - ch_surf.get_width() // 2, 100))

                # Underline cursor position
                if is_cursor:
                    cx = x + char_w // 2
                    pygame.draw.rect(self.screen, GREEN,
                        (cx - 15, 160, 30, 3))

            # Show morse pattern only for highlighted character (centered below)
            if cursor_pos < len(buffer):
                ch = buffer[cursor_pos]
                pattern = CHAR_TO_MORSE.get(ch, '')
                spaced = '  '.join(pattern)
                morse_surf = self.font_medium.render(spaced, True, AMBER)
                self.screen.blit(morse_surf,
                    (SCREEN_W // 2 - morse_surf.get_width() // 2, 180))

            # "New char" indicator at end
            if cursor_pos >= len(buffer):
                nx = x_start + len(buffer) * char_w
                plus = self.font_medium.render("+", True, GREEN)
                self.screen.blit(plus, (nx + 10, 110))
                hint = self.font_small.render("D-pad Up", True, GRAY)
                self.screen.blit(hint, (nx - 5, 180))
        else:
            prompt = self.font_medium.render("Press D-pad Up to start", True, GRAY)
            self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 140))

        # Instructions
        if ON_DEVICE:
            lines = [
                "D-pad U/D = Change letter",
                "A = Accept letter    X = Delete",
                "B = Save callsign    R1 = Hear it",
            ]
        else:
            lines = [
                "Up/Down = Change letter",
                "D = Accept    A/S = cursor    W = Delete",
                "X = Save callsign    R = Hear it",
            ]
        for i, line in enumerate(lines):
            surf = self.font_small.render(line, True, GRAY)
            self.screen.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2, 280 + i * 30))

        help_surf = self.font_small.render("Select = Back", True, GRAY)
        self.screen.blit(help_surf, (SCREEN_W // 2 - help_surf.get_width() // 2,
                                     SCREEN_H - 30))
        pygame.display.flip()

    def draw_callsign_challenge(self, callsign, challenge_name, target_text,
                                decoded_text, current_element, key_is_down):
        self.screen.fill(BLACK)

        # Header
        call_surf = self.font_medium.render(f"Callsign: {callsign}", True, AMBER)
        self.screen.blit(call_surf, (20, 10))

        # Challenge name
        ch_surf = self.font_medium.render(challenge_name, True, WHITE)
        self.screen.blit(ch_surf, (SCREEN_W // 2 - ch_surf.get_width() // 2, 50))

        # Target text to key
        target_surf = self.font_medium.render(target_text, True, LIGHT_GRAY)
        self.screen.blit(target_surf, (SCREEN_W // 2 - target_surf.get_width() // 2, 100))

        # Key indicator
        color = GREEN if key_is_down else DARK_GREEN
        pygame.draw.circle(self.screen, color, (SCREEN_W // 2, 160), 15)
        pygame.draw.circle(self.screen, GRAY, (SCREEN_W // 2, 160), 15, 2)

        # Current element
        if current_element:
            spaced = '  '.join(current_element)
            elem_surf = self.font_element.render(spaced, True, GREEN)
            self.screen.blit(elem_surf, (SCREEN_W // 2 - elem_surf.get_width() // 2, 190))

        # Decoded text
        self._draw_wrapped_text(decoded_text, 240, self.font_large, WHITE, 28)

        # Help (two rows)
        if ON_DEVICE:
            row1 = "A = Key    R1 = Hear    R2 = Clear    U/D = Challenge"
            row2 = "Y = Edit Call    Select = Back"
        else:
            row1 = "SPACE = Key    R = Hear    C = Clear    U/D = Challenge"
            row2 = "ESC = Back"
        h1 = self.font_small.render(row1, True, GRAY)
        h2 = self.font_small.render(row2, True, GRAY)
        self.screen.blit(h1, (SCREEN_W // 2 - h1.get_width() // 2, SCREEN_H - 50))
        self.screen.blit(h2, (SCREEN_W // 2 - h2.get_width() // 2, SCREEN_H - 28))
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
