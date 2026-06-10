#!/usr/bin/env python3
"""CW Dojo self-updater.

Checks the latest GitHub release, downloads cw.dojo.zip, and overlays it
onto this install. User data (settings.json, profiles.json, progress
files) is never touched — the release zip doesn't contain those files.

Runs on the device with the same Python/pygame/SDL stack as the app, so
progress and errors are shown on screen. Launch via "CW Dojo Update.sh".
"""

import json
import os
import shutil
import sys
import tempfile
import urllib.request
import zipfile

import pygame

REPO = 'DavidClawson/cw-dojo'
API_LATEST = f'https://api.github.com/repos/{REPO}/releases/latest'
ASSET_NAME = 'cw.dojo.zip'
ZIP_PREFIX = 'cw.dojo/'  # app files live under this prefix in the zip

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SCREEN_W, SCREEN_H = 640, 480

BG = (24, 26, 33)
FG = (230, 230, 230)
DIM = (140, 140, 140)
GREEN = (110, 200, 120)
RED = (220, 110, 110)
BAR_BG = (60, 60, 70)
BAR_FG = (255, 180, 0)


class Ui:
    """Minimal status screen: a few lines of text and a progress bar."""

    def __init__(self):
        pygame.init()
        if os.environ.get('SDL_VIDEODRIVER') == 'wayland':
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H),
                                                  pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption('CW Dojo Update')
        font_path = os.path.join(APP_DIR, 'assets', 'NotoSans.ttf')
        if os.path.exists(font_path):
            self.font_big = pygame.font.Font(font_path, 36)
            self.font = pygame.font.Font(font_path, 22)
        else:
            self.font_big = pygame.font.Font(None, 48)
            self.font = pygame.font.Font(None, 28)
        if pygame.joystick.get_count() > 0:
            pygame.joystick.Joystick(0).init()
        self.lines = []

    def show(self, *lines, progress=None, color=FG):
        self.lines = list(lines)
        self.screen.fill(BG)
        title = self.font_big.render('CW DOJO UPDATE', True, BAR_FG)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 90))
        y = 190
        for line in self.lines:
            surf = self.font.render(line, True, color)
            self.screen.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2, y))
            y += 36
        if progress is not None:
            bar_w, bar_h = 400, 18
            x = (SCREEN_W - bar_w) // 2
            pygame.draw.rect(self.screen, BAR_BG, (x, 330, bar_w, bar_h),
                             border_radius=9)
            fill = max(0, min(bar_w, int(bar_w * progress)))
            if fill > 0:
                pygame.draw.rect(self.screen, BAR_FG, (x, 330, fill, bar_h),
                                 border_radius=9)
        pygame.display.flip()
        pygame.event.pump()

    def wait_for_button(self, timeout_ms=30000):
        """Block until any button/key press (or timeout)."""
        hint = self.font.render('Press any button to exit', True, DIM)
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 400))
        pygame.display.flip()
        deadline = pygame.time.get_ticks() + timeout_ms
        while pygame.time.get_ticks() < deadline:
            for event in pygame.event.get():
                if event.type in (pygame.JOYBUTTONDOWN, pygame.KEYDOWN,
                                  pygame.QUIT):
                    return
            pygame.time.wait(50)


def local_version():
    try:
        with open(os.path.join(APP_DIR, 'VERSION')) as f:
            return f.read().strip().lstrip('v')
    except OSError:
        return None


def fetch_latest():
    """Return (tag, zip_url) for the latest release."""
    req = urllib.request.Request(API_LATEST,
                                 headers={'User-Agent': 'cw-dojo-updater'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        release = json.load(resp)
    tag = release.get('tag_name', '')
    for asset in release.get('assets', []):
        if asset.get('name') == ASSET_NAME:
            return tag, asset['browser_download_url']
    return tag, None


def download(url, dest, ui):
    req = urllib.request.Request(url,
                                 headers={'User-Agent': 'cw-dojo-updater'})
    with urllib.request.urlopen(req, timeout=30) as resp, \
            open(dest, 'wb') as out:
        total = int(resp.headers.get('Content-Length') or 0)
        done = 0
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                ui.show('Downloading update...',
                        f'{done // 1024} / {total // 1024} KB',
                        progress=done / total)


def apply_zip(zip_path, ui):
    """Extract the app files over this install."""
    with zipfile.ZipFile(zip_path) as zf:
        members = [m for m in zf.namelist()
                   if m.startswith(ZIP_PREFIX) and not m.endswith('/')]
        with tempfile.TemporaryDirectory() as tmp:
            for i, member in enumerate(members):
                rel = member[len(ZIP_PREFIX):]
                src = zf.extract(member, tmp)
                dest = os.path.join(APP_DIR, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copyfile(src, dest)
                ui.show('Installing...', rel,
                        progress=(i + 1) / len(members))


def main():
    ui = Ui()
    current = local_version()
    ui.show('Checking for updates...',
            f'Installed: v{current}' if current else 'Installed: unknown')

    try:
        tag, zip_url = fetch_latest()
    except Exception as e:
        ui.show('Could not reach GitHub.', 'Is WiFi connected?',
                f'({type(e).__name__})', color=RED)
        ui.wait_for_button()
        return 1

    latest = tag.lstrip('v')
    if current and latest and current == latest:
        ui.show(f'Already up to date (v{current})', color=GREEN)
        ui.wait_for_button()
        return 0

    if not zip_url:
        ui.show(f'Latest release {tag} has no {ASSET_NAME}.',
                'Try again after the next release.', color=RED)
        ui.wait_for_button()
        return 1

    try:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, ASSET_NAME)
            ui.show('Downloading update...', progress=0)
            download(zip_url, zip_path, ui)
            apply_zip(zip_path, ui)
    except Exception as e:
        ui.show('Update failed.', str(e)[:60],
                'Existing install left as-is.', color=RED)
        ui.wait_for_button()
        return 1

    ui.show(f'Updated v{current} -> v{latest}' if current
            else f'Updated to v{latest}',
            'Launch CW Dojo to use the new version.', color=GREEN)
    ui.wait_for_button()
    return 0


if __name__ == '__main__':
    code = main()
    pygame.quit()
    sys.exit(code)
