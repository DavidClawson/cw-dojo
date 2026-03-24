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
import pygame
from settings import Settings
from progress import KochProgress
from scenes import (MenuScene, StraightKeyScene, KochScene, SettingsScene,
                    GlossaryScene, CallsignScene)
from waterfall import WaterfallScene
from buttons import BTN_SELECT, BTN_START

SCREEN_W, SCREEN_H = 640, 480
FPS = 60


def main():
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(4)

    import os
    if os.environ.get('SDL_VIDEODRIVER') == 'wayland':
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("CW Dojo")
    clock = pygame.time.Clock()

    # Show loading splash immediately
    screen.fill((0, 0, 0))
    splash_font = pygame.font.Font(None, 72)
    sub_font = pygame.font.Font(None, 32)
    title = splash_font.render("CW DOJO", True, (255, 180, 0))
    sub = sub_font.render("Loading...", True, (80, 80, 80))
    screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 180))
    screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 260))
    pygame.display.flip()

    # Load persistent state
    settings = Settings.load()
    progress = KochProgress.load()

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
        'koch': KochScene(settings, progress),
        'waterfall': WaterfallScene(settings),
        'callsign': CallsignScene(settings),
        'glossary': GlossaryScene(settings),
        'settings': SettingsScene(settings),
    }
    current = 'menu'
    scenes[current].on_enter()

    select_held = False
    start_held = False
    running = True

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

            # Keyboard quit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False
                continue

            # Dispatch to current scene
            next_scene = scenes[current].handle_event(event, now_ms)
            if next_scene and next_scene in scenes:
                scenes[current].on_exit()
                current = next_scene
                scenes[current].on_enter()

        # Update
        next_scene = scenes[current].update(now_ms)
        if next_scene and next_scene in scenes:
            scenes[current].on_exit()
            current = next_scene
            scenes[current].on_enter()

        # Draw
        scenes[current].draw(screen, display)
        clock.tick(FPS)

    # Cleanup
    settings.save()
    progress.save()
    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    main()
