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

    def draw_settings(self, items, selected):
        """items: list of (label, value_str, unit)"""
        self.screen.fill(BLACK)

        title = self.font_medium.render("SETTINGS", True, AMBER)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 30))

        y_start = 120
        for i, (label, val, unit) in enumerate(items):
            y = y_start + i * 70
            color = WHITE if i == selected else GRAY

            if i == selected:
                bar_rect = pygame.Rect(40, y - 5, SCREEN_W - 80, 55)
                pygame.draw.rect(self.screen, HIGHLIGHT, bar_rect, border_radius=6)

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
