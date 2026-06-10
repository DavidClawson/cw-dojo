#!/usr/bin/env python3
"""CW Dojo — Morse Code Trainer for R36S.

Controls:
    Menu:        D-pad = navigate, A = select
    Straight Key: A/Space = key, D-pad U/D = WPM
    Koch Trainer: face buttons = answer, R1/R = replay
    Settings:    D-pad = navigate/adjust
    Quit:        Select+Start (any screen)
"""

import sys
import os
import time
import pygame
from settings import Settings
from progress import KochProgress
from profiles import ProfileManager
from scenes import (MenuScene, StraightKeyScene, KochScene, SettingsScene,
                    ProfileScene, GlossaryScene, CallsignScene,
                    VocabQuizScene, ProcedureScene, SendDrillScene)
from waterfall import WaterfallScene
from buttons import BTN_SELECT, BTN_START, BTN_L2
from sounds import sfx

SCREEN_W, SCREEN_H = 640, 480
FPS = 60


def main():
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(6)

    if os.environ.get('SDL_VIDEODRIVER') == 'wayland':
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("CW Dojo")
    clock = pygame.time.Clock()

    # Show splash screen immediately
    base = os.path.dirname(__file__) or '.'
    screen.fill((0, 0, 0))
    for splash_path in [os.path.join(base, 'assets', 'splash.png'),
                        os.path.join(base, 'splash.png')]:
        try:
            splash_img = pygame.image.load(splash_path)
            splash_img = pygame.transform.scale(splash_img, (SCREEN_W, SCREEN_H))
            screen.blit(splash_img, (0, 0))
            break
        except Exception:
            continue
    pygame.display.flip()

    # Init sound effects
    sfx.init()

    # Load persistent state
    settings = Settings.load()
    profile_mgr = ProfileManager.load()

    # Apply volume and key sound to SFX
    sfx.set_volume(settings.volume)
    sfx.apply_key_sound(settings.key_sound)
    progress = profile_mgr.load_progress()

    # Import Display here so pygame is already initialized
    from ui import Display
    display = Display(screen)

    # Init joystick
    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    # Scene setup
    scenes = {
        'menu': MenuScene(),
        'straight_key': StraightKeyScene(settings),
        'send_drill': SendDrillScene(settings),
        'koch': KochScene(settings, progress),
        'waterfall': WaterfallScene(settings),
        'callsign': CallsignScene(settings),
        'vocab_quiz': VocabQuizScene(settings),
        'procedure': ProcedureScene(settings),
        'glossary': GlossaryScene(settings),
        'profiles': ProfileScene(profile_mgr, progress),
        'settings': SettingsScene(settings, progress, profile_mgr),
    }
    current = 'menu'
    scenes[current].on_enter()

    select_held = False
    start_held = False
    running = True
    screenshot_flash = 0  # ticks remaining for white flash feedback

    # Screenshot directory (next to the app)
    screenshot_dir = os.path.join(base, 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)

    def take_screenshot():
        """Save current screen to screenshots/ with timestamp filename."""
        nonlocal screenshot_flash
        ts = time.strftime('%Y%m%d-%H%M%S')
        path = os.path.join(screenshot_dir, f'cw-dojo-{ts}.png')
        pygame.image.save(screen, path)
        screenshot_flash = 8  # flash for ~8 frames
        print(f'[screenshot] saved: {path}')

    while running:
        now_ms = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            # Global quit combo: Select + Start
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == BTN_SELECT:
                    select_held = True
                elif event.button == BTN_START:
                    start_held = True
                if select_held and start_held:
                    running = False
                    continue
            elif event.type == pygame.JOYBUTTONUP:
                if event.button == BTN_SELECT:
                    select_held = False
                elif event.button == BTN_START:
                    start_held = False

            # Screenshot: L2 button or F12 on keyboard
            if event.type == pygame.JOYBUTTONDOWN and event.button == BTN_L2:
                take_screenshot()
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F12:
                take_screenshot()
                continue

            # Log unknown joystick buttons to help discover Fn mapping
            if event.type == pygame.JOYBUTTONDOWN:
                from buttons import ALL_KNOWN
                if event.button not in ALL_KNOWN:
                    print(f'[buttons] unknown button index: {event.button}')

            # Keyboard quit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False
                continue

            # Dispatch to current scene
            next_scene = scenes[current].handle_event(event, now_ms)
            if next_scene and next_scene in scenes:
                scenes[current].on_exit()
                current = next_scene
                sfx.set_volume(settings.volume)
                sfx.apply_key_sound(settings.key_sound)
                scenes[current].on_enter()

        # Update
        next_scene = scenes[current].update(now_ms)
        if next_scene and next_scene in scenes:
            scenes[current].on_exit()
            current = next_scene
            sfx.set_volume(settings.volume)
            sfx.apply_key_sound(settings.key_sound)
            scenes[current].on_enter()

        # Draw
        scenes[current].draw(screen, display)

        # Screenshot flash overlay (brief white flash as confirmation)
        if screenshot_flash > 0:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H))
            overlay.fill((255, 255, 255))
            overlay.set_alpha(100)
            screen.blit(overlay, (0, 0))
            pygame.display.flip()
            screenshot_flash -= 1

        clock.tick(FPS)

    # Cleanup
    settings.save()
    progress.save()
    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    main()
