#!/bin/bash
# Launch script for EmulationStation Ports menu
# Place this file in: /storage/roms/ports/Morse Trainer.sh

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$SCRIPT_DIR" || exit 1

python3 main.py
