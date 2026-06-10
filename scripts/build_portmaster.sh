#!/usr/bin/env bash
# Build the PortMaster package.
#
# Syncs portmaster/cw.dojo/ from the main source tree (modules, assets,
# license), compile-checks the result, and produces cw.dojo.zip at the
# repo root. Used locally and by the build-portmaster GitHub Action.
set -euo pipefail
cd "$(dirname "$0")/.."

PKG=portmaster/cw.dojo
MODULES=(audio.py band.py buttons.py glossary.py keyer.py koch.py main.py
         morse.py profiles.py progress.py qso_scripts.py scenes.py
         settings.py sounds.py ui.py vocab_quiz.py waterfall.py)

cp "${MODULES[@]}" "$PKG/"
rm -rf "$PKG/assets"
cp -R assets "$PKG/assets"
cp LICENSE "$PKG/licenses/LICENSE"

python3 -m py_compile "$PKG"/*.py

find portmaster \( -name '.DS_Store' -o -name '*.pyc' \) -delete
find portmaster -name '__pycache__' -type d -prune -exec rm -rf {} +

rm -f cw.dojo.zip
(cd portmaster && zip -r ../cw.dojo.zip "CW Dojo.sh" port.json cw.dojo \
    -x '*.DS_Store' -x '*__pycache__*')

echo "Built cw.dojo.zip ($(du -h cw.dojo.zip | cut -f1))"
