#!/bin/bash
# CW Dojo — Morse Code Trainer
# SPDX-License-Identifier: MIT

XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}

if [ -d "/opt/system/Tools/PortMaster/" ]; then
  controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then
  controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then
  controlfolder="$XDG_DATA_HOME/PortMaster"
else
  controlfolder="/roms/ports/PortMaster"
fi

source $controlfolder/control.txt
[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"
get_controls

GAMEDIR="/$directory/ports/cw.dojo"

cd "${GAMEDIR}"

> "${GAMEDIR}/log.txt" && exec > >(tee "${GAMEDIR}/log.txt") 2>&1

# Load Python 3.11 runtime
runtime="python_3.11.aarch64"
export python_dir="$HOME/python311"
mkdir -p "${python_dir}"

if [ ! -f "$controlfolder/libs/${runtime}.squashfs" ]; then
  if [ ! -f "$controlfolder/harbourmaster" ]; then
    pm_message "This port requires the latest PortMaster to run, please go to https://portmaster.games/ for more info."
    sleep 5
    exit 1
  fi
  $ESUDO $controlfolder/harbourmaster --quiet --no-check runtime_check "${runtime}.squashfs"
fi

if [[ "$PM_CAN_MOUNT" != "N" ]]; then
    $ESUDO umount "${python_dir}" 2>/dev/null
fi
$ESUDO mount "$controlfolder/libs/${runtime}.squashfs" "${python_dir}"

# Set up Python environment
source "${python_dir}/bin/activate" 2>/dev/null
export PYTHONHOME="${python_dir}"
export PYTHONPYCACHEPREFIX="${GAMEDIR}/python.cache"
export PYTHONPATH="${GAMEDIR}:${python_dir}/lib/python3.11/site-packages"

# SDL controller config
export SDL_GAMECONTROLLERCONFIG="$sdl_controllerconfig"

# Launch with gptokeyb for controller support
$GPTOKEYB "python3" &
pm_platform_helper "${python_dir}/bin/python3"

"${python_dir}/bin/python3" "${GAMEDIR}/main.py"

# Cleanup
if [[ "$PM_CAN_MOUNT" != "N" ]]; then
    $ESUDO umount "${python_dir}"
fi

pm_finish
