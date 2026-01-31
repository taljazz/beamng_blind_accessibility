# BeamNG.drive Blind Accessibility Mod

A comprehensive accessibility mod for BeamNG.drive that enables screen reader support (NVDA, JAWS, SAPI) for blind and visually impaired users.

## Project Overview

This project provides blind accessibility for BeamNG.drive through a two-component architecture:

1. **BeamNG Mod (Lua/JavaScript)** - Captures UI events and sends them via UDP
2. **External Helper App (Python)** - Receives UDP packets and speaks through screen readers
3. **Accessible Launcher (Python)** - Screen reader friendly launcher with map/vehicle selection and vehicle tuning

## Architecture

```
+------------------------------------------+
|           BeamNG.drive                   |
|  +------------------------------------+  |
|  |  Accessibility Mod (Lua + JS)     |  |
|  |  - Menu state tracking            |  |
|  |  - UI event capture               |  |
|  |  - AI state monitoring            |  |
|  +----------------+-------------------+  |
|                   | UDP (Port 4445)      |
+-------------------+----------------------+
                    |
                    v
+------------------------------------------+
|  External Helper App (Python)            |
|  - Receives UDP packets                  |
|  - cytolk/Tolk -> NVDA/JAWS/SAPI         |
+------------------------------------------+

+------------------------------------------+
|  Accessible Launcher (Python)            |
|  - Screen reader friendly menus          |
|  - Map and vehicle selection             |
|  - Vehicle tuning (edits .pc files)      |
|  - Creates/modifies vehicle configs      |
+------------------------------------------+
        |
        v (file I/O)
+------------------------------------------+
|  Vehicle Config Files (.pc)              |
|  - JSON format                           |
|  - Parts selection (engine, trans, etc.) |
|  - Located in mods/unpacked/             |
+------------------------------------------+
```

## File Locations

### BeamNG Mod Files
Located in: `%LOCALAPPDATA%\BeamNG.BeamNG.drive\current\mods\unpacked\blind_accessibility.zip\`

| File | Purpose |
|------|---------|
| `lua/ge/extensions/blindAccessibility.lua` | Main game engine extension - handles UDP communication and event processing |
| `scripts/blind_accessibility/modScript.lua` | Mod entry point and registration |
| `scripts/blind_accessibility/extension.lua` | Extension registration |
| `ui/modules/blindAccessibilityService.js` | Auto-loading UI service - monitors DOM for navigation events |
| `ui/modules/accessibility/accessibility.js` | Accessibility AngularJS module |
| `ui/modules/apps/blindAccessibility/app.js` | UI app for deeper state capture |
| `ui/entrypoints/accessibility-service.js` | UI entrypoint for service loading |
| `vehicles/atv/tracked_wydra_v8.pc` | Custom vehicle config for tracked Wydra with V8 |

### Helper Application Files
Located in: `C:\Coding Projects\beamng_blind_accessibility\helper\`

| File | Purpose |
|------|---------|
| `main.py` | Entry point - initializes speech and UDP listener |
| `speech.py` | Screen reader interface (cytolk/pyttsx3) |
| `udp_listener.py` | UDP packet reception and parsing |
| `config.py` | Configuration settings |
| `test_e2e.py` | End-to-end tests |

### Launcher Files
Located in: `C:\Coding Projects\beamng_blind_accessibility\launcher\`

| File | Purpose |
|------|---------|
| `accessible_launcher.py` | Main launcher with menu navigation and tuning |
| `run_launcher.bat` | Batch file to activate conda and run launcher |
| `launcher_config.json` | Saved BeamNG path configuration |

## UDP Protocol

### Port 4445 - Mod to Helper (Announcements)

**Packet Format:**
```
Header: "BNBA" (4 bytes)
Type: 1 byte
Length: 2 bytes (big-endian)
Payload: UTF-8 text
```

**Message Types:**
| Type | Value | Description |
|------|-------|-------------|
| MENU | 0x01 | Menu navigation text |
| VEHICLE | 0x02 | Vehicle telemetry |
| ALERT | 0x03 | High-priority alerts |
| DIALOG | 0x04 | Dialog box content |
| STATUS | 0x05 | Status messages |

## AI State Announcements

The mod automatically monitors and announces AI state changes when you use BeamNG's built-in controls.

### Announced Events

| Event | Announcement |
|-------|--------------|
| AI enabled on player vehicle | "AI enabled, traffic mode" (or chase/flee/random/etc.) |
| AI disabled on player vehicle | "AI disabled, manual control" |
| Traffic spawned | "Traffic spawned, 10 vehicles" |
| Traffic cleared | "Traffic cleared" |

### In-Game AI Controls

Use these built-in BeamNG keyboard shortcuts:

| Shortcut | Action |
|----------|--------|
| **Ctrl+Shift+I** | Toggle AI on player vehicle |
| **Ctrl+Shift+T** | Spawn AI traffic |
| **E** | Open radial menu (access AI options) |

When you use any of these controls, the mod will announce the change via your screen reader.

### AI Modes

| Mode | Description |
|------|-------------|
| `traffic` | Follow traffic rules, stay in lanes |
| `random` | Drive randomly around the map |
| `span` | Explore the entire road network |
| `chase` | Chase a target vehicle |
| `flee` | Flee from a target vehicle |
| `manual` | Drive to a waypoint |

## Vehicle Config Tuning

The launcher edits `.pc` vehicle config files directly (no game running needed).

### Config File Format (.pc)
```json
{
  "format": 2,
  "mainPartName": "atv",
  "model": "atv",
  "parts": {
    "n2o_system": "AgentY_engine_swaps",
    "engineswap_sample": "sample_gavril_engine_v8",
    "transmissionswap_sample": "sample_stransmission_M",
    "turboswap_sample": "",
    "scswap_sample": "",
    "ecuswap_sample": "",
    "internalsswap_sample": "",
    "radiatorswap_sample": ""
  }
}
```

### Available Engine Swaps
| ID | Engine | Part Name |
|----|--------|-----------|
| 1 | 4.1L I6 Gavril | sample_gavril_engine_i6 |
| 2 | 4.5L V8 Gavril | sample_gavril_engine_v8 |
| 3 | 5.5L V8 Gavril | sample_gavril_engine_v8_large |
| 4 | 6.9L V8 Gavril Ultra-Thrust | sample_gavril_engine_v8_very_large |
| 7 | 3.9L I6 Bruckell | sample_bruckell_engine_I6_39_new |
| 8 | 5.1L V8 Bruckell | sample_bruckell_engine_v8_51_new |
| 10 | 7.3L V8 Bruckell Thunder | sample_bruckell_engine_v8_73_new |
| 14 | 6.5L V8 Barstow 423 | sample_barstow_engine_v8_423 |
| 24 | Electric Motor (SBR) | sample_emotor_sbr |
| 26 | Semi Truck Diesel | sample_semi_engine |

### Available Transmissions
| ID | Transmission | Part Name |
|----|--------------|-----------|
| 1 | Manual 4-Speed | sample_stransmission_M |
| 5 | Manual Race | sample_stransmission_M_race |
| 8 | Automatic | sample_stransmission_A |
| 10 | CVT | sample_stransmission_CVT |
| 11 | DCT (Dual Clutch) | sample_stransmission_DCT |
| 12 | Sequential | sample_stransmission_SEQ |

### Forced Induction
**Turbochargers (turboswap_sample):**
- generic_turbo_s/m/l (Small/Medium/Large)
- generic_turbo_s_twin/m_twin/l_twin (Twin turbos)
- generic_turbo_race

**Superchargers (scswap_sample):**
- generic_supercharger_stage1/2/3/4

## Installation

### Prerequisites
- BeamNG.drive (Steam version)
- Python 3.8+ with conda (for launcher)
- NVDA screen reader (or JAWS, or fallback to Windows SAPI)

### Python Dependencies
```bash
pip install cytolk pyttsx3
```

### Mod Installation
1. Copy the `blind_accessibility.zip` folder to:
   `%LOCALAPPDATA%\BeamNG.BeamNG.drive\<version>\mods\unpacked\`

2. The mod auto-loads when BeamNG starts

### Required Mods for Full Features
- **agenty_tracked_wydra.zip** - Tracked vehicle conversion for FPU Wydra
- **engine_swap_mod.zip** - Universal engine swap support

## Usage

### Running the Helper
```bash
cd helper
python main.py
```

Options:
- `--port PORT` - UDP port (default: 4445)
- `--debug` - Enable debug output
- `--test` - Run speech test and exit

### Running the Launcher
```bash
cd launcher
run_launcher.bat
```

Or directly:
```bash
conda activate bng
python accessible_launcher.py
```

### Launcher Menu Options
1. Launch Freeroam - Select map and vehicle
2. Quick Launch - Grid Map with Pickup
3. Quick Launch - West Coast with Sunburst
4. Quick Launch - Utah with Rock Crawler
5. Quick Launch - Grid with Tracked Wydra (mod)
6. Launch Custom Tuned Config
T. Tune Existing Vehicle Config
N. Create New Tuned Config
C. Configure BeamNG Path
Q. Quit

### Vehicle Tuning (File-Based)
The tuning system edits `.pc` config files directly - no game running required.

**Tune Existing Config (T):**
1. Launcher scans for `.pc` files in mods folder
2. Select a vehicle config to tune
3. Choose tuning categories (Engine, Transmission, Turbo, etc.)
4. Select parts from available options
5. Save changes to the file
6. Launch the game with the tuned config

**Create New Config (N):**
1. Select a base vehicle
2. Enter a name for the config
3. Configure tuning options
4. Save - creates new `.pc` file in blind_accessibility mod

**Available Tuning Categories (All Vehicles):**
| # | Category | Options |
|---|----------|---------|
| 1 | Engine Swap | 28 engines (Gavril, Bruckell, ETK, Ibishu, Electric, etc.) |
| 2 | Transmission | 12 options (Manual, Automatic, CVT, DCT, Sequential) |
| 3 | Turbocharger | 9 options (Small/Medium/Large, Twin, Diesel) |
| 4 | Supercharger | 4 stages |
| 5 | ECU | Stock, Sport, Race, Economy |
| 6 | Engine Internals | Stock, Sport, Race, Ultra |
| 7 | Radiator | Stock, Sport, Race, OP (never overheat) |

### Wydra/ATV Specific Tuning (Options 8-13)

When tuning a Wydra (FPU ATV) config, additional options appear:

| # | Category | Options |
|---|----------|---------|
| 8 | Track Setup | Install full tracks OR remove tracks for wheels |
| 9 | Body Type | Standard 8x8, Pressured 8x8 (required for tracks) |
| 10 | Axle Hubs | Standard, Lifted, Track hubs |
| 11 | Paint/Skin | Military Camo, Polish Police, Woods Camo |
| 12 | Headlights | Standard, Round, None |
| 13 | Wydra Transmission | High-Low (for tracks), Standard ATV |

**Track Setup (Option 8)** is the easiest way to add/remove tracks. It automatically configures:
- Left & right tracks (`atv_track_L_agenty`, `atv_track_R_agenty`)
- Sprockets and hubs (`atv_sprocket_L/R_agenty`, `atv_sprockethub_tracks_agenty`)
- Idlers and hubs (`atv_idler_L/R_agenty`, `atv_idlerhub_tracks_agenty`)
- Road wheels 1-4 (`atv_roadwheel_1-4_agenty`)
- Road wheel hubs (`atv_roadwheelhub_1-4_tracks_agenty`)
- Wheel data (`atv_wheeldata_1-4_agenty`)
- Body type (pressured for tracks)
- Axle hubs (track-compatible)

### Wydra Part Reference

**Body Types (atv_body):**
| Part Name | Description |
|-----------|-------------|
| `atv_body_8x8` | Standard wheeled body |
| `atv_body_8x8_pressured_agenty` | Pressured body (required for tracks) |

**Axle Hubs (atv_axlehubs):**
| Part Name | Description |
|-----------|-------------|
| `atv_axlehubs` | Standard |
| `atv_axlehubs_lifted` | Lifted suspension |
| `atv_axlehubs_tracks_agenty` | For track setup |

**Paint Designs (paint_design):**
| Part Name | Description |
|-----------|-------------|
| `atv_skin_camo_agenty` | Military camouflage |
| `atv_skin_polishpolice_agenty` | Polish Police livery |
| `atv_skin_woods` | Woods/forest camo |

**Headlights:**
| Left | Right | Style |
|------|-------|-------|
| `atv_headlight_L` | `atv_headlight_R` | Standard |
| `atv_headlight_L_round` | `atv_headlight_R_round` | Round |

**Wydra Transmissions (atv_transmission):**
| Part Name | Description |
|-----------|-------------|
| `atv_transmission_highlow` | High-Low range (best for tracks) |
| `atv_transmission` | Standard ATV transmission |

### Example: Efficiency-Tuned Tracked Wydra (Ripsaw)

The "Ripsaw" config demonstrates a clean, minimal efficiency build:
```json
{
  "format": 2,
  "mainPartName": "atv",
  "model": "atv",
  "parts": {
    "n2o_system": "AgentY_engine_swaps",
    "engineswap_sample": "sample_gavril_engine_v8d",
    "transmissionswap_sample": "sample_stransmission_CVT",
    "turboswap_sample": "generic_turbo_d_s",
    "scswap_sample": "",
    "ecuswap_sample": "generic_engine_ecu_economy",
    "internalsswap_sample": "",
    "radiatorswap_sample": "radiatorswap_op"
  }
}
```

**This setup provides:**
- Diesel V8 for torque and fuel efficiency
- CVT transmission (realistic for tracked vehicles, keeps engine at optimal RPM)
- Small diesel turbo for boost
- Economy ECU for fuel savings
- OP radiator (tracks run hot)
- Tracks inherited from base vehicle (AgentY mod)

### Important: Config Best Practices

**DO use the simple approach:**
```json
"n2o_system": "AgentY_engine_swaps"  // Correct way to enable engine swaps
```

**DON'T use the complex approach:**
```json
"AgentY_engine_alt_slot": "AgentY_engine_alt_slot"  // Can cause conflicts!
```

**Key principles:**
1. Keep configs minimal - only override what you need to change
2. Let the base vehicle + mods handle tracks, body, etc.
3. Use `n2o_system: AgentY_engine_swaps` to enable engine swapping
4. Avoid explicitly listing all track parts unless necessary
5. For tracked Wydra, the AgentY mod provides tracks automatically

## How It Works

### UI Event Capture
The `blindAccessibilityService.js` module:
1. Loads automatically with BeamNG UI
2. Uses MutationObserver to watch for class changes
3. Detects elements with `.selected`, `.focused`, `.active` classes
4. Extracts text from `aria-label`, `title`, `textContent`
5. Calls the Lua extension via `bngApi.engineLua()`

### Lua Extension
The `blindAccessibility.lua` extension:
1. Receives announcements from UI via `announce()` function
2. Creates UDP packets with BNBA protocol
3. Sends to helper app on port 4445
4. Monitors AI state and announces changes
5. Hooks into BeamNG events (vehicle spawn, level load, etc.)

### Speech Output
The helper's `speech.py` module:
1. Tries cytolk first (for NVDA/JAWS)
2. Falls back to pyttsx3 (Windows SAPI)
3. Supports interrupt for rapid navigation
4. Rate-limited for telemetry data

## Key Code Locations

### Announcement Flow
1. UI detects navigation: `blindAccessibilityService.js:80-86`
2. Calls Lua: `blindAccessibilityService.js:30`
3. Lua sends UDP: `blindAccessibility.lua:85-112`
4. Helper receives: `udp_listener.py:68-79`
5. Speech output: `speech.py:82-113`

### Vehicle Tuning Flow
1. Launcher sends command: `accessible_launcher.py:160-170`
2. Lua receives on port 4446: `blindAccessibility.lua:659-690`
3. Part manager updates vehicle: `blindAccessibility.lua:538-567`

## Configuration

### Mod Config (Lua)
```lua
local config = {
    enabled = true,
    ip = "127.0.0.1",
    port = 4445,
    announcePosition = true,
    verbosity = "normal",
}
```

### Helper Config (Python)
```python
UDP_IP = "127.0.0.1"
UDP_PORT = 4445
SCREEN_READER = "auto"
INTERRUPT_SPEECH = True
SPEECH_RATE = 200
```

## Testing

### Manual Testing
1. Start helper: `python helper/main.py --debug`
2. Start launcher: `python launcher/accessible_launcher.py`
3. Launch BeamNG with any vehicle
4. Navigate menus with arrow keys
5. Verify announcements in helper output

### Test Tuning
1. Launch BeamNG with a vehicle
2. Open tuning menu (T) in launcher
3. Select engine preset
4. Verify vehicle respawns with new engine

### Test AI Announcements
1. Start helper: `python helper/main.py --debug`
2. Launch BeamNG with any vehicle on a map with roads
3. Press **Ctrl+Shift+I** to toggle AI on player vehicle
4. Verify you hear "AI enabled, traffic mode" (or similar)
5. Press **Ctrl+Shift+I** again to disable
6. Verify you hear "AI disabled, manual control"
7. Press **Ctrl+Shift+T** to spawn traffic
8. Verify you hear "Traffic spawned, X vehicles"

## Troubleshooting

### No Announcements
- Check helper is running
- Verify UDP port 4445 not blocked
- Check BeamNG console for mod errors
- Try `--debug` flag on helper

### Socket Library Not Loading
- BeamNG sandbox may block some functionality
- Check if `socket` library is available in BeamNG's Lua

### Tuning Not Working
- Ensure AgentY engine swap mod (temp_tuning) is installed
- Check that `n2o_system` is set to "AgentY_engine_swaps" in the .pc file
- Verify the .pc file is in the correct vehicles folder
- Make sure the config file is valid JSON

### No Configs Found
- Launcher searches in `mods/unpacked` and `mods/temp_tuning`
- Configs must be in a `vehicles/` subfolder
- File extension must be `.pc`

## Future Development (Phase 2)

### Driving Feedback
- Speed sonification (pitch = speed)
- Steering angle audio indicator
- Engine RPM tone
- Surface type sounds
- Collision proximity warnings
- Turn indicator system

### Implementation Notes
Use `electrics.values` for telemetry:
- `wheelspeed` - current speed
- `steering_input` - steering angle
- `rpm` - engine RPM
- `gear` - current gear

## Credits

- BeamNG.drive by BeamNG GmbH
- Tolk screen reader library
- cytolk Python bindings
- AgentY for Tracked Wydra mod
