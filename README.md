# BeamNG.drive Blind Accessibility Mod

A comprehensive accessibility mod that makes BeamNG.drive playable for blind and visually impaired users through screen reader support.

## What This Mod Does

This mod speaks menu items, game events, and UI elements through your screen reader (NVDA, JAWS, or Windows SAPI) as you navigate BeamNG.drive. It also includes an accessible launcher for selecting maps and vehicles without needing to navigate the game's visual menus.

### Features

- **Menu Navigation** - Announces menu items as you navigate with arrow keys
- **Accessible Launcher** - Screen reader friendly launcher to select maps and vehicles
- **Vehicle Tuning** - Customize vehicles with engine swaps, transmissions, turbos, and more
- **Screen Reader Support** - Works with NVDA, JAWS, or Windows SAPI (built-in voices)

### Planned Features

- AI state announcements (when AI is enabled/disabled)
- Traffic spawn announcements
- Driving feedback (speed, RPM, audio cues)

## Requirements

- BeamNG.drive (Steam version)
- Windows 10 or 11
- Python 3.8 or newer
- A screen reader: NVDA (recommended), JAWS, or Windows SAPI

### Optional Mods (for extra features)

- **AgentY Tracked Wydra** - Adds tracked vehicle support for the FPU Wydra
- **AgentY Engine Swaps** - Enables engine swapping on any vehicle

## Installation

### Step 1: Install the BeamNG Mod

1. Download or clone this repository
2. Copy the `mods/unpacked/blind_accessibility` folder to your BeamNG mods folder:
   ```
   %LocalAppData%\BeamNG.drive\mods\unpacked\
   ```
   The full path will be something like:
   ```
   C:\Users\YourName\AppData\Local\BeamNG.drive\mods\unpacked\blind_accessibility\
   ```
   **Tip:** Press Win+R, type `%LocalAppData%\BeamNG.drive\mods` and press Enter to open the folder directly.
3. The mod loads automatically when BeamNG starts

### Step 2: Install Python Dependencies

1. Open a command prompt
2. Navigate to the `helper` folder:
   ```
   cd path\to\beamng_blind_accessibility\helper
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

### Step 3: Verify Installation

1. Start your screen reader (NVDA recommended)
2. Run the helper with a test:
   ```
   python main.py --test
   ```
3. You should hear "BeamNG Accessibility Helper ready" spoken

## Quick Start Guide

### Basic Usage

1. **Start the helper app** (required for speech):
   ```
   cd helper
   python main.py
   ```
   Or double-click `run_helper.bat`

2. **Start your screen reader** (NVDA, JAWS, etc.)

3. **Launch BeamNG.drive**

4. **Navigate menus** using arrow keys - items will be announced

### Using the Accessible Launcher (Recommended)

The launcher provides a fully accessible way to start the game:

1. Run the launcher:
   ```
   cd launcher
   python accessible_launcher.py
   ```
   Or double-click `run_launcher.bat`

2. Use arrow keys to navigate the menu:
   - **1-5**: Quick launch presets (different maps/vehicles)
   - **T**: Tune an existing vehicle config
   - **N**: Create a new tuned vehicle config
   - **C**: Configure your BeamNG.drive path
   - **Q**: Quit

3. Select a map and vehicle, then the game launches automatically

## Keyboard Controls (In-Game)

These BeamNG shortcuts work with the mod:

| Shortcut | Action |
|----------|--------|
| Arrow Keys | Navigate menus |
| Enter | Select menu item |
| Escape | Go back / Close menu |
| E | Open radial menu |

## Vehicle Tuning

The launcher lets you customize vehicles without needing to see the game's menus.

### Tune an Existing Config

1. Press **T** in the launcher menu
2. Select a vehicle config from the list
3. Choose what to modify:
   - **Engine** - Swap to a different engine (V8, I6, electric, diesel, etc.)
   - **Transmission** - Manual, automatic, CVT, DCT, or sequential
   - **Turbo** - Add turbochargers (small, medium, large, twin)
   - **Supercharger** - Add supercharger (stages 1-4)
   - **ECU** - Stock, sport, race, or economy tuning
   - **Internals** - Engine internal upgrades
   - **Radiator** - Cooling upgrades
4. Save your changes
5. Launch the game with your tuned config

### Create a New Config

1. Press **N** in the launcher menu
2. Select a base vehicle
3. Enter a name for your config
4. Configure the tuning options
5. Save - creates a new config file

### Available Engines

| Engine | Description |
|--------|-------------|
| 4.1L I6 Gavril | Inline 6, smooth power |
| 4.5L V8 Gavril | Classic V8 |
| 5.5L V8 Gavril | Larger V8 |
| 6.9L V8 Ultra-Thrust | Big block V8 |
| 3.9L I6 Bruckell | Modern inline 6 |
| 5.1L V8 Bruckell | Performance V8 |
| 7.3L V8 Thunder | Massive V8 |
| Electric Motor | Silent, instant torque |
| Semi Truck Diesel | Maximum torque |

### Available Transmissions

| Transmission | Description |
|--------------|-------------|
| Manual 4-Speed | Basic manual |
| Manual Race | Close ratio manual |
| Automatic | Traditional auto |
| CVT | Continuously variable |
| DCT | Dual clutch automatic |
| Sequential | Racing sequential |

## Troubleshooting

### No Speech Output

1. Make sure the helper is running (`python main.py`)
2. Make sure your screen reader is running
3. Try running the helper with debug mode: `python main.py --debug`
4. Check that port 4445 is not blocked by your firewall

### Helper Won't Start

1. Make sure Python is installed: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. If port 4445 is in use, try a different port: `python main.py --port 4446`

### Mod Not Loading in BeamNG

1. Verify the mod is in the correct folder:
   ```
   %LocalAppData%\BeamNG.drive\mods\unpacked\blind_accessibility\
   ```
2. Press the tilde key (~) in BeamNG to open the console and check for errors
3. Try reloading Lua with Ctrl+L

### Launcher Can't Find BeamNG

1. Press **C** in the launcher to configure the BeamNG path
2. Enter the full path to your BeamNG installation, for example:
   ```
   C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive
   ```

### No Menu Announcements

1. The mod may take a moment to initialize after the game loads
2. Try navigating to a different menu and back
3. Check the BeamNG console for errors

## How It Works

The mod uses a two-component architecture because BeamNG sandboxes its Lua environment and doesn't allow direct access to screen reader DLLs.

```
BeamNG.drive (Lua mod)
    |
    | UDP packets (port 4445)
    v
Helper App (Python)
    |
    | Screen reader API
    v
NVDA / JAWS / SAPI
```

1. The Lua mod inside BeamNG captures UI events and menu changes
2. It sends this information via UDP to the helper app
3. The helper app receives the packets and speaks through your screen reader

## Configuration

### Helper App Settings

Edit `helper/config.py` to customize:

```python
UDP_PORT = 4445           # Port to listen on
SCREEN_READER = "auto"    # "auto", "nvda", "jaws", or "sapi"
INTERRUPT_SPEECH = True   # Interrupt ongoing speech for new items
SPEECH_RATE = 200         # Speech rate for SAPI
```

### Command Line Options

```
python main.py --port 4446    # Use different port
python main.py --debug        # Show debug output
python main.py --test         # Test speech and exit
```

## File Structure

```
beamng_blind_accessibility/
├── helper/                    # Python helper application
│   ├── main.py               # Entry point
│   ├── speech.py             # Screen reader interface
│   ├── udp_listener.py       # UDP packet handling
│   ├── config.py             # Settings
│   └── requirements.txt      # Python dependencies
├── launcher/                  # Accessible launcher
│   ├── accessible_launcher.py # Main launcher
│   └── run_launcher.bat      # Launch script
└── mods/unpacked/blind_accessibility/  # BeamNG mod
    ├── lua/ge/extensions/    # Lua game extension
    ├── scripts/              # Mod scripts
    └── ui/modules/           # UI integration
```

## Contributing

Contributions are welcome! This project aims to make BeamNG.drive accessible to everyone.

Areas that could use help:
- AI state announcements
- Additional UI element detection
- Support for more game modes
- Testing with different screen readers

## Credits

- BeamNG.drive by BeamNG GmbH
- [Tolk](https://github.com/dkager/tolk) screen reader library
- [cytolk](https://pypi.org/project/cytolk/) Python bindings
- AgentY for the Tracked Wydra and Engine Swap mods
- Developed with assistance from Claude AI

## License

This mod is provided free for accessibility purposes. Feel free to modify and distribute.
