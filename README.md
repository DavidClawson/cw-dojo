# CW Dojo

A Morse code (CW) trainer designed for the R36S handheld game console running ROCKNIX. Built with Python and pygame.

Learn CW the way you'd learn a language — through drills, listening, and practice on a device that fits in your pocket.

## Features

**Straight Key** — Practice sending with the A button as a straight key. Hear your sidetone, see your dits and dahs decoded in real time.

**Koch Trainer** — Receive practice using the Koch method with spaced repetition. Characters you struggle with appear more often. Toggle hints (D-pad Up) to see dit/dah patterns while learning. Progress persists between sessions.

**Band Explorer** — Simulated HF waterfall display. Tune across a 40m CW band segment with D-pad, hear stations calling CQ and having QSOs. Realistic band noise with atmospheric fading and static. Adjust noise level with R1/R2.

**Challenges** — Enter your callsign, then practice keying CQ calls, signal reports, and common exchanges. Press R1 to hear how it should sound, then try to match it.

**Glossary** — Browse common CW abbreviations, prosigns, Q-codes, and typical QSO phrases. Press R1 to hear any term played as CW.

**Settings** — Adjust sidetone frequency, character speed (WPM), Farnsworth spacing, and master volume.

## Controls (R36S)

| Button | Function |
|--------|----------|
| D-pad | Navigate menus, tune waterfall, adjust WPM |
| A | Confirm, straight key, start round |
| B | Answer choice (Koch) |
| X | Answer choice (Koch), delete (callsign editor) |
| Y | Answer choice (Koch), edit callsign |
| R1 | Play/hear audio (everywhere) |
| R2 | Adjust noise (waterfall), clear text (challenges) |
| Select | Back to menu |
| Select+Start | Quit to EmulationStation |

## Controls (Desktop/Keyboard)

| Key | Function |
|-----|----------|
| Arrow keys | D-pad equivalent |
| Space | Straight key |
| W/D/S/A | X/A/B/Y face buttons |
| R | Replay / play audio |
| H | Toggle hints (Koch) |
| Escape | Back to menu |
| Q | Quit |

## Requirements

- Python 3.10+
- pygame (or pygame-ce) >= 2.5
- numpy >= 1.24

## Running on Desktop (Development)

```bash
cd morse_trainer
uv run python main.py
```

Or with pip:

```bash
pip install pygame-ce numpy
python main.py
```

## Installing on R36S (ROCKNIX)

### Prerequisites

- R36S running ROCKNIX
- WiFi dongle connected and configured
- SSH access to the device

### Install Steps

1. **Install Python packages** on the device:

   ```bash
   # From your computer, download aarch64 wheels
   pip download --only-binary=:all: --platform manylinux2014_aarch64 \
     --python-version 3.11 --implementation cp pygame numpy -d /tmp/wheels/

   # Copy to device
   scp /tmp/wheels/*.whl root@<device-ip>:/tmp/

   # SSH in and install
   ssh root@<device-ip>
   mkdir -p /storage/lib/python3.11/site-packages
   cd /tmp
   python3 -c "
   import zipfile
   site = '/storage/lib/python3.11/site-packages'
   for whl in ['pygame-*.whl', 'numpy-*.whl']:
       import glob
       for f in glob.glob(whl):
           print(f'Installing {f}...')
           zipfile.ZipFile(f).extractall(site)
   "
   ```

   Then symlink system SDL2 over the bundled versions (ROCKNIX's SDL2 has the correct display drivers):

   ```bash
   cd /storage/lib/python3.11/site-packages/pygame.libs/
   ln -sf /usr/lib/libSDL2-2.0.so.0 libSDL2-*.so.*
   ln -sf /usr/lib/libSDL2_image-2.0.so.0 libSDL2_image-*.so.*
   ln -sf /usr/lib/libSDL2_mixer-2.0.so.0 libSDL2_mixer-*.so.*
   ln -sf /usr/lib/libSDL2_ttf-2.0.so.0 libSDL2_ttf-*.so.*
   ```

2. **Copy CW Dojo** to the device:

   ```bash
   scp -r morse_trainer/ root@<device-ip>:/storage/roms/ports/morse_trainer/
   ```

3. **Create the launch script**:

   ```bash
   ssh root@<device-ip>
   cat > '/storage/roms/ports/CW Dojo.sh' << 'EOF'
   #!/bin/bash
   . /etc/profile
   export PYTHONPATH=/storage/lib/python3.11/site-packages
   cd /storage/roms/ports/morse_trainer
   python3 main.py > /tmp/cwdojo.log 2>&1
   EOF
   chmod +x '/storage/roms/ports/CW Dojo.sh'
   ```

4. **Restart EmulationStation** — CW Dojo will appear under Ports.

## Project Structure

```
morse_trainer/
  main.py         Entry point and scene dispatcher
  audio.py        Sidetone and CW character playback (numpy + pygame)
  band.py         Simulated HF band with CW stations
  buttons.py      R36S button mapping constants
  glossary.py     CW abbreviations and Q-codes
  koch.py         Koch method trainer with spaced repetition
  morse.py        Morse code table, decoder, and Koch character order
  progress.py     Persistent Koch training progress
  scenes.py       All scene classes (menu, straight key, Koch, etc.)
  settings.py     Persistent user settings
  ui.py           Display rendering for all screens
  waterfall.py    Waterfall display and band explorer scene
```

## Hardware Mod (Planned)

A 3.5mm stereo jack (PJ-307) can be wired to the L1/L2 shoulder button pads to accept a CW straight key or iambic paddle. When nothing is plugged in, the shoulder buttons work normally (the jack's internal switches are normally closed). When a key is plugged in, the switches open and the key contacts take over.

## License

MIT

## Contributing

Issues and pull requests welcome. This project is in early alpha — feedback from CW operators is especially appreciated.

73 de CW Dojo
