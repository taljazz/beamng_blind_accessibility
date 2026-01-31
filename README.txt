BeamNG Blind Accessibility Mod
==============================

A mod to make BeamNG.drive accessible to blind and visually impaired players
using NVDA or other screen readers.

ARCHITECTURE
============

This mod uses a two-component design:

1. BeamNG Mod (Lua)
   - Captures menu state and UI events
   - Sends data via UDP to external helper

2. External Helper App (Python)
   - Receives UDP packets from BeamNG
   - Speaks through NVDA/JAWS/SAPI

This design is necessary because BeamNG sandboxes Lua and blocks
direct DLL loading (like Tolk.dll for screen reader access).


INSTALLATION
============

Part 1: BeamNG Mod
------------------
1. Copy the entire "mods/unpacked/blind_accessibility" folder to:
   Documents\BeamNG.drive\mods\unpacked\

   Final path should be:
   Documents\BeamNG.drive\mods\unpacked\blind_accessibility\

2. The mod will load automatically when BeamNG starts.


Part 2: Helper Application
--------------------------
1. Install Python 3.8 or newer from https://python.org

2. Open a command prompt in the "helper" folder and run:
   pip install -r requirements.txt

3. Download Tolk from https://github.com/dkager/tolk/releases
   - Extract Tolk.dll and the lib/ folder
   - Place them in helper/tolk/

4. Start the helper before or while BeamNG is running:
   python main.py

   Or use the batch file:
   run_helper.bat


USAGE
=====

1. Start the helper application (python main.py)
2. Start NVDA (or your preferred screen reader)
3. Launch BeamNG.drive
4. Use arrow keys to navigate menus
5. The helper will speak menu items as you navigate


CONFIGURATION
=============

Helper App (helper/config.py):
- UDP_PORT: Port number (default 4445)
- SCREEN_READER: "auto", "nvda", "jaws", or "sapi"
- INTERRUPT_SPEECH: True to interrupt ongoing speech
- ANNOUNCE_VEHICLE_TELEMETRY: True to hear speed/rpm while driving


TROUBLESHOOTING
===============

No speech output:
- Make sure NVDA is running
- Check that the helper shows "Using screen reader: NVDA"
- If Tolk.dll is missing, it will fall back to SAPI

Helper won't start:
- Install Python dependencies: pip install -r requirements.txt
- Make sure port 4445 is not in use

Mod not loading:
- Check Documents\BeamNG.drive\mods\unpacked\ path is correct
- Look for errors in BeamNG's console (press ~ key)
- Try reloading Lua with Ctrl+L


FILES
=====

BeamNG Mod:
- scripts/blind_accessibility/modScript.lua  - Entry point
- lua/ge/extensions/blindAccessibility.lua   - Menu tracking
- lua/vehicle/protocols/blindAccess.lua      - UDP protocol
- ui/modules/apps/blindAccessibility/        - UI state capture

Helper App:
- main.py           - Entry point
- udp_listener.py   - UDP packet handling
- speech.py         - Screen reader interface
- config.py         - Configuration


LICENSE
=======

This mod is provided as-is for accessibility purposes.
Feel free to modify and distribute.


CREDITS
=======

Developed with assistance from Claude AI.
Inspired by the RAD (Racing Auditory Display) research project.

Resources used:
- Tolk screen reader library: https://github.com/dkager/tolk
- BeamNG modding documentation: https://documentation.beamng.com
