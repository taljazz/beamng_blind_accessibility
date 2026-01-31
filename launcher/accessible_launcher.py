"""
BeamNG.drive Accessible Launcher
Provides a screen reader friendly interface to launch BeamNG with specific maps and vehicles.
Includes vehicle tuning by editing .pc config files directly.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Try to import cytolk for NVDA support
try:
    import cytolk
    from cytolk import tolk
    TOLK_AVAILABLE = True
except ImportError:
    TOLK_AVAILABLE = False
    print("Warning: cytolk not available. Install with: pip install cytolk")

# Configuration
CONFIG_FILE = Path(__file__).parent / "launcher_config.json"

# Audio channel settings (maps to BeamNG's game-settings.cs)
AUDIO_CHANNELS = {
    "1": ("Master Volume", "AudioChannelMaster", "Controls all audio"),
    "2": ("Music Volume", "AudioChannelMusic", "Background music"),
    "3": ("Effects Volume", "AudioChannelEffects", "General sound effects"),
    "4": ("UI Volume", "AudioChannelUi", "Menu and interface sounds"),
    "5": ("GUI Volume", "AudioChannelGui", "GUI interaction sounds"),
    "6": ("Environment Volume", "AudioChannelEnvironment", "Weather, wind, etc."),
    "7": ("Ambience Volume", "AudioChannelAmbience", "Background ambient sounds"),
    "8": ("Messages Volume", "AudioChannelMessages", "Voice messages and notifications"),
    "9": ("Engine/Power Volume", "AudioChannelPower", "Engine and drivetrain sounds"),
    "10": ("Collision Volume", "AudioChannelCollision", "Crash and impact sounds"),
    "11": ("Surface Volume", "AudioChannelSurface", "Tire and road surface sounds"),
    "12": ("Transmission Volume", "AudioChannelTransmission", "Gear shifting sounds"),
    "13": ("Turbo/Supercharger Volume", "AudioChannelForcedInduction", "Turbo and supercharger whine"),
    "14": ("Suspension Volume", "AudioChannelSuspension", "Suspension creaks and sounds"),
    "15": ("Aero Volume", "AudioChannelAero", "Wind and aerodynamic sounds"),
    "16": ("Subwoofer/LFE Volume", "AudioChannelLfe", "Low frequency bass effects"),
    "17": ("Intercom Volume", "AudioChannelIntercom", "Radio and intercom sounds"),
    "18": ("Other Volume", "AudioChannelOther", "Miscellaneous sounds"),
}

# Default BeamNG paths to check
DEFAULT_STEAM_PATHS = [
    r"C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive",
    r"C:\Program Files\Steam\steamapps\common\BeamNG.drive",
    r"D:\Steam\steamapps\common\BeamNG.drive",
    r"D:\SteamLibrary\steamapps\common\BeamNG.drive",
    r"E:\Steam\steamapps\common\BeamNG.drive",
    r"E:\SteamLibrary\steamapps\common\BeamNG.drive",
]

# BeamNG user data path
BEAMNG_USER_PATH = Path(os.environ.get('LOCALAPPDATA', '')) / "BeamNG" / "BeamNG.drive"

# Available maps with friendly names
MAPS = {
    "1": ("West Coast USA", "west_coast_usa"),
    "2": ("East Coast USA", "east_coast_usa"),
    "3": ("Italy", "italy"),
    "4": ("Utah", "utah"),
    "5": ("Grid Map", "gridmap_v2"),
    "6": ("Small Grid", "smallgrid"),
    "7": ("Jungle Rock Island", "jungle_rock_island"),
    "8": ("Hirochi Raceway", "hirochi_raceway"),
    "9": ("Johnson Valley", "johnson_valley"),
    "10": ("Industrial Site", "industrial"),
    "11": ("Derby Arenas", "derby"),
    "12": ("Driver Training", "driver_training"),
    "13": ("Cliff", "cliff"),
    "14": ("Small Island", "small_island"),
    "15": ("Automation Test Track", "automation_test_track"),
}

# Available vehicles organized by category
VEHICLES = {
    "1": ("Hirochi Sunburst (sedan)", "sunburst", None),
    "2": ("ETK 800-Series (wagon)", "etk800", None),
    "3": ("ETK I-Series (classic sedan)", "etki", None),
    "4": ("Bruckell LeGran (sedan)", "legran", None),
    "5": ("Bruckell Bastion (modern sedan)", "bastion", None),
    "6": ("Ibishu Pessima (sedan)", "pessima", None),
    "7": ("Soliad Wendover (wagon)", "wendover", None),
    "8": ("ETK K-Series (coupe)", "etkk", None),
    "9": ("Ibishu 200BX (sports coupe)", "200bx", None),
    "10": ("Hirochi SBR4 (sports car)", "sbr4", None),
    "11": ("Civetta Bolide (race car)", "bolide", None),
    "12": ("Civetta Scintilla (supercar)", "scintilla", None),
    "13": ("Gavril Barstow (muscle car)", "barstow", None),
    "14": ("Bruckell Moonhawk (muscle car)", "moonhawk", None),
    "15": ("Ibishu Covet (hatchback)", "covet", None),
    "16": ("Ibishu Pigeon (three-wheeler)", "pigeon", None),
    "17": ("Ibishu Wigeon (three-wheeler van)", "wigeon", None),
    "18": ("Autobello Piccolina (microcar)", "piccolina", None),
    "19": ("Gavril D-Series (pickup truck)", "pickup", None),
    "20": ("Gavril Roamer (SUV)", "roamer", None),
    "21": ("Ibishu Hopper (off-road)", "hopper", None),
    "22": ("Ibishu Miramar (full-size)", "miramar", None),
    "23": ("Gavril H-Series (van)", "van", None),
    "24": ("Gavril Grand Marshal (police car)", "grandmarshal", None),
    "25": ("Gavril T-Series (semi truck)", "t75", None),
    "26": ("Gavril MD-Series (medium duty truck)", "md", None),
    "27": ("Wentward DT40L (bus)", "citybus", None),
    "28": ("Hirochi HT-55 (haul truck, dump truck)", "ht55", None),
    "29": ("Hirochi WL-40 (wheel loader)", "wl40", None),
    "30": ("SP Dunekicker (dune buggy)", "dunekicker", None),
    "31": ("SP Rockbasher (rock crawler)", "rockbasher", None),
    "32": ("Autobello Stambecco (off-road utility)", "stambecco", None),
    "33": ("FPU Wydra (military off-road, wheeled)", "atv", None),
    "34": ("Burnside Special (classic)", "burnside", None),
    "35": ("Gavril Bluebuck (classic)", "bluebuck", None),
    "36": ("Bruckell Nine (classic)", "nine", None),
    "37": ("Soliad Lansdale (classic)", "lansdale", None),
    "38": ("Hirochi Aurata (helicopter)", "aurata", None),
    # Modded vehicles
    "39": ("FPU Wydra TRACKED - Base (mod)", "atv", "atv/base_tracks_agenty.pc"),
    "40": ("FPU Wydra TRACKED - Tank Style (mod)", "atv", "atv/tank_tracks_agenty.pc"),
    "41": ("FPU Wydra TRACKED - Police (mod)", "atv", "atv/police_tracks_agenty.pc"),
}

# =============================================================================
# TUNING DATA - Available parts from the AgentY tuning mod
# =============================================================================

# Engine swaps (engineswap_sample slot)
ENGINES = {
    # Gavril engines
    "1": ("4.1L I6 Gavril", "sample_gavril_engine_i6"),
    "2": ("4.5L V8 Gavril", "sample_gavril_engine_v8"),
    "3": ("5.5L V8 Gavril", "sample_gavril_engine_v8_large"),
    "4": ("6.9L V8 Gavril Ultra-Thrust", "sample_gavril_engine_v8_very_large"),
    "5": ("Diesel V8 Gavril", "sample_gavril_engine_v8d"),
    "6": ("Diesel I6 Gavril", "sample_gavril_engine_i6d"),
    # Bruckell engines
    "7": ("3.9L I6 Bruckell Econo Six", "sample_bruckell_engine_I6_39_new"),
    "8": ("5.1L V8 Bruckell Solace Eight", "sample_bruckell_engine_v8_51_new"),
    "9": ("6.2L V8 Bruckell Luxe Eight", "sample_bruckell_engine_v8_62_new"),
    "10": ("7.3L V8 Bruckell Thunder Eight", "sample_bruckell_engine_v8_73_new"),
    "11": ("6.5L V8 Bruckell (Bastion)", "sample_bruckell_engine_V8_65"),
    # Barstow/Moonhawk V8s
    "12": ("4.2L V8 Barstow 289", "sample_barstow_engine_v8_289"),
    "13": ("5.3L V8 Barstow 353", "sample_barstow_engine_v8_353"),
    "14": ("6.5L V8 Barstow 423", "sample_barstow_engine_v8_423"),
    "15": ("7.2L V8 Moonhawk 440", "sample_moonhawk_engine_440"),
    # ETK engines
    "16": ("2.4L I6 ETK", "sample_etk_engine_i6_24"),
    "17": ("3.0L I6 ETK", "sample_etk_engine_i6_30"),
    "18": ("3.0L I6 Turbo ETK", "sample_etk_engine_i6_30t"),
    "19": ("4.4L V8 ETK", "sample_etk_engine_v8_44"),
    # Ibishu engines
    "20": ("1.5L I4 Sunburst", "sample_ibishu_engine_15_dohc"),
    "21": ("1.8L I4 Pessima", "sample_ibishu_engine_18_sohc"),
    "22": ("2.5L I4 Hopper", "sample_ibishu_engine_I4_25"),
    "23": ("0.7L I3 Pigeon", "sample_ibishu_engine_I3_07"),
    # Special engines
    "24": ("Electric Motor (SBR)", "sample_emotor_sbr"),
    "25": ("Electric Motor Sport (SBR)", "sample_emotor_sbr_sport"),
    "26": ("Semi Truck Diesel", "sample_semi_engine"),
    "27": ("Bus Diesel", "sample_citybus_engine"),
    "28": ("FPU Wydra 4.5L V8", "sample_fpu_engine_v8"),
    # Remove engine
    "0": ("Remove/Default Engine", ""),
}

# Transmission swaps (transmissionswap_sample slot)
TRANSMISSIONS = {
    "1": ("Manual 4-Speed", "sample_stransmission_M"),
    "2": ("Manual High Efficiency", "sample_stransmission_M_efficiency"),
    "3": ("Manual Sport", "sample_stransmission_M_sport"),
    "4": ("Manual ETK ttSport", "sample_stransmission_M_ttsport"),
    "5": ("Manual Race", "sample_stransmission_M_race"),
    "6": ("Manual Centrifugal Clutch", "sample_stransmission_M_centrifugal"),
    "7": ("Manual Semi Truck", "sample_stransmission_M_semi_new"),
    "8": ("Automatic", "sample_stransmission_A"),
    "9": ("Automatic Sport", "sample_stransmission_A_sport"),
    "10": ("CVT", "sample_stransmission_CVT"),
    "11": ("DCT (Dual Clutch)", "sample_stransmission_DCT"),
    "12": ("Sequential", "sample_stransmission_SEQ"),
    "0": ("Remove/Default Transmission", ""),
}

# Turbocharger swaps (turboswap_sample slot)
TURBOS = {
    "1": ("Small Turbo", "generic_turbo_s"),
    "2": ("Medium Turbo", "generic_turbo_m"),
    "3": ("Large Turbo", "generic_turbo_l"),
    "4": ("Small Twin Turbo", "generic_turbo_s_twin"),
    "5": ("Medium Twin Turbo", "generic_turbo_m_twin"),
    "6": ("Large Twin Turbo", "generic_turbo_l_twin"),
    "7": ("Race Turbo", "generic_turbo_race"),
    "8": ("Diesel Turbo Small", "generic_turbo_d_s"),
    "9": ("Diesel Turbo Large", "generic_turbo_d_l"),
    "0": ("Remove Turbo", ""),
}

# Supercharger swaps (scswap_sample slot)
SUPERCHARGERS = {
    "1": ("Supercharger Stage 1", "generic_supercharger_stage1"),
    "2": ("Supercharger Stage 2", "generic_supercharger_stage2"),
    "3": ("Supercharger Stage 3", "generic_supercharger_stage3"),
    "4": ("Supercharger Stage 4 (Race)", "generic_supercharger_stage4"),
    "0": ("Remove Supercharger", ""),
}

# ECU swaps (ecuswap_sample slot)
ECUS = {
    "1": ("Stock ECU", "generic_engine_ecu_stock"),
    "2": ("Sport ECU", "generic_engine_ecu_sport"),
    "3": ("Race ECU", "generic_engine_ecu_race"),
    "4": ("Economy ECU", "generic_engine_ecu_economy"),
    "0": ("Remove/Default ECU", ""),
}

# Engine internals (internalsswap_sample slot)
INTERNALS = {
    "1": ("Stock Internals", "generic_engine_internals"),
    "2": ("Sport Internals", "generic_engine_internals_sport"),
    "3": ("Race Internals", "generic_engine_internals_race"),
    "4": ("Ultra Internals", "generic_engine_internals_ultra"),
    "0": ("Remove/Default Internals", ""),
}

# Radiator swaps (radiatorswap_sample slot)
RADIATORS = {
    "1": ("Stock Radiator", "radiatorswap_stock"),
    "2": ("Sport Radiator", "radiatorswap_sport"),
    "3": ("Race Radiator", "radiatorswap_race"),
    "4": ("OP Radiator (Never Overheat)", "radiatorswap_op"),
    "0": ("Remove/Default Radiator", ""),
}

# =============================================================================
# TRACKED WYDRA SPECIFIC PARTS (FPU Wydra / ATV with AgentY Tracks)
# =============================================================================

# Body types (atv_body slot)
WYDRA_BODIES = {
    "1": ("Standard 8x8 Body (wheeled)", "atv_body_8x8"),
    "2": ("Pressured 8x8 Body (for tracks)", "atv_body_8x8_pressured_agenty"),
    "0": ("Remove/Default Body", ""),
}

# Axle hubs (atv_axlehubs slot)
WYDRA_AXLE_HUBS = {
    "1": ("Standard Axle Hubs", "atv_axlehubs"),
    "2": ("Lifted Axle Hubs", "atv_axlehubs_lifted"),
    "3": ("Track Axle Hubs", "atv_axlehubs_tracks_agenty"),
    "0": ("Remove/Default", ""),
}

# Paint/skin designs (paint_design slot)
WYDRA_PAINTS = {
    "1": ("Military Camo", "atv_skin_camo_agenty"),
    "2": ("Polish Police", "atv_skin_polishpolice_agenty"),
    "3": ("Woods Camo", "atv_skin_woods"),
    "0": ("No Paint/Default", ""),
}

# Headlights (atv_headlight_L and atv_headlight_R slots)
WYDRA_HEADLIGHTS = {
    "1": ("Standard Headlights", "standard"),
    "2": ("Round Headlights", "round"),
    "0": ("No Headlights", "none"),
}

# Track setup - applies all track-related parts at once
WYDRA_TRACK_SETUP = {
    "1": ("Full Track Setup (Recommended)", "full_tracks"),
    "2": ("Wheels Only (Remove Tracks)", "wheels_only"),
}

# Parts that make up the full track setup
TRACK_PARTS = {
    "atv_track_L_agenty": "atv_track_L_agenty",
    "atv_track_R_agenty": "atv_track_R_agenty",
    "atv_sprocket_L_agenty": "atv_sprocket_L_agenty",
    "atv_sprocket_R_agenty": "atv_sprocket_R_agenty",
    "atv_sprockethub_tracks_agenty": "atv_sprockethub_tracks_agenty",
    "atv_idler_L_agenty": "atv_idler_L_agenty",
    "atv_idler_R_agenty": "atv_idler_R_agenty",
    "atv_idlerhub_tracks_agenty": "atv_idlerhub_tracks_agenty",
    "atv_roadwheel_1_agenty": "atv_roadwheel_1_agenty",
    "atv_roadwheel_2_agenty": "atv_roadwheel_2_agenty",
    "atv_roadwheel_3_agenty": "atv_roadwheel_3_agenty",
    "atv_roadwheel_4_agenty": "atv_roadwheel_4_agenty",
    "atv_roadwheelhub_1_tracks_agenty": "atv_roadwheelhub_1_tracks_agenty",
    "atv_roadwheelhub_2_tracks_agenty": "atv_roadwheelhub_2_tracks_agenty",
    "atv_roadwheelhub_3_tracks_agenty": "atv_roadwheelhub_3_tracks_agenty",
    "atv_roadwheelhub_4_tracks_agenty": "atv_roadwheelhub_4_tracks_agenty",
    "atv_wheeldata_1_agenty": "atv_wheeldata_1_agenty",
    "atv_wheeldata_2_agenty": "atv_wheeldata_2_agenty",
    "atv_wheeldata_3_agenty": "atv_wheeldata_3_agenty",
    "atv_wheeldata_4_agenty": "atv_wheeldata_4_agenty",
}

# Transmission for tracked vehicle
WYDRA_TRANSMISSIONS = {
    "1": ("High-Low (Stock Tracked)", "atv_transmission_highlow"),
    "2": ("Standard ATV", "atv_transmission"),
    "0": ("Use Engine Swap Transmission", ""),
}

class AccessibleLauncher:
    def __init__(self):
        self.beamng_path = None
        self.tolk_initialized = False
        self.load_config()
        self.init_tolk()

    def init_tolk(self):
        """Initialize Tolk for screen reader support."""
        if TOLK_AVAILABLE:
            try:
                tolk.load()
                self.tolk_initialized = True
            except Exception as e:
                print(f"Warning: Could not initialize Tolk: {e}")

    def speak(self, text, interrupt=True):
        """Speak text via screen reader."""
        print(text)
        if self.tolk_initialized:
            try:
                tolk.speak(text, interrupt=interrupt)
            except Exception:
                pass

    def load_config(self):
        """Load configuration from file."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.beamng_path = config.get('beamng_path')
            except Exception:
                pass
        if not self.beamng_path:
            self.beamng_path = self.find_beamng()

    def save_config(self):
        """Save configuration to file."""
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'beamng_path': self.beamng_path}, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")

    def get_game_settings_path(self):
        """Get the path to BeamNG's game-settings.cs file."""
        if BEAMNG_USER_PATH.exists():
            for folder in sorted(BEAMNG_USER_PATH.iterdir(), reverse=True):
                if folder.is_dir() and (folder.name == 'current' or folder.name.replace('.', '').isdigit()):
                    settings_path = folder / "settings" / "game-settings.cs"
                    if settings_path.exists():
                        return settings_path
        return None

    def load_game_settings(self):
        """Load BeamNG's game-settings.cs file and parse audio settings."""
        settings_path = self.get_game_settings_path()
        if not settings_path:
            return {}

        audio_settings = {}
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('$pref::SFX::AudioChannel'):
                        # Parse: $pref::SFX::AudioChannelMaster = "1.000000";
                        parts = line.split('=')
                        if len(parts) == 2:
                            key = parts[0].strip().replace('$pref::SFX::', '')
                            value = parts[1].strip().rstrip(';').strip('"')
                            try:
                                audio_settings[key] = float(value)
                            except ValueError:
                                audio_settings[key] = 1.0
        except Exception as e:
            self.speak(f"Error loading game settings: {e}")

        return audio_settings

    def save_audio_setting(self, channel_key, value):
        """Save a single audio setting to game-settings.cs."""
        settings_path = self.get_game_settings_path()
        if not settings_path:
            self.speak("Could not find game settings file.")
            return False

        try:
            # Read all lines
            with open(settings_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Find and update the setting
            setting_line = f'$pref::SFX::{channel_key}'
            found = False
            new_lines = []

            for line in lines:
                if line.strip().startswith(setting_line):
                    new_lines.append(f'$pref::SFX::{channel_key} = "{value:.6f}";\n')
                    found = True
                else:
                    new_lines.append(line)

            # If setting wasn't found, add it
            if not found:
                new_lines.append(f'$pref::SFX::{channel_key} = "{value:.6f}";\n')

            # Write back
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            return True
        except Exception as e:
            self.speak(f"Error saving audio setting: {e}")
            return False

    def audio_settings_menu(self):
        """Show audio settings menu."""
        self.speak("Audio Settings Menu")
        self.speak("Adjust BeamNG audio volumes. Changes take effect next game launch.")

        # Load current settings
        current_settings = self.load_game_settings()

        while True:
            self.speak("Audio Channels:")
            for key, (name, channel_key, description) in AUDIO_CHANNELS.items():
                current_value = current_settings.get(channel_key, 1.0)
                percent = int(current_value * 100)
                self.speak(f"{key}: {name} - {percent}%", interrupt=False)

            self.speak("A: Adjust All Volumes at Once")
            self.speak("M: Mute All (set to 0%)")
            self.speak("R: Reset All to Default (80%)")
            self.speak("Q: Back to Main Menu")

            choice = self.get_input("Select channel to adjust or action:").lower()

            if choice == 'q':
                return
            elif choice == 'a':
                self.adjust_all_volumes(current_settings)
            elif choice == 'm':
                self.mute_all_volumes(current_settings)
            elif choice == 'r':
                self.reset_all_volumes(current_settings)
            elif choice in AUDIO_CHANNELS:
                name, channel_key, description = AUDIO_CHANNELS[choice]
                self.adjust_single_volume(name, channel_key, description, current_settings)
            else:
                self.speak("Invalid choice.")

    def adjust_single_volume(self, name, channel_key, description, current_settings):
        """Adjust a single audio channel volume."""
        current_value = current_settings.get(channel_key, 1.0)
        current_percent = int(current_value * 100)

        self.speak(f"{name}: {description}")
        self.speak(f"Current volume: {current_percent}%")
        self.speak("Enter new volume (0-100), or:")
        self.speak("  +10 to increase by 10%")
        self.speak("  -10 to decrease by 10%")
        self.speak("  'q' to cancel")

        while True:
            input_val = self.get_input("New volume:")

            if input_val.lower() == 'q':
                return

            try:
                if input_val.startswith('+'):
                    new_percent = current_percent + int(input_val[1:])
                elif input_val.startswith('-'):
                    new_percent = current_percent - int(input_val[1:])
                else:
                    new_percent = int(input_val)

                # Clamp to valid range
                new_percent = max(0, min(200, new_percent))  # Allow up to 200% for boost
                new_value = new_percent / 100.0

                if self.save_audio_setting(channel_key, new_value):
                    current_settings[channel_key] = new_value
                    self.speak(f"{name} set to {new_percent}%")
                return

            except ValueError:
                self.speak("Invalid input. Enter a number like 50, +10, or -10.")

    def adjust_all_volumes(self, current_settings):
        """Adjust all volumes at once."""
        self.speak("Adjust All Volumes")
        self.speak("This will set all audio channels to the same level.")
        self.speak("Enter volume (0-100) or 'q' to cancel:")

        input_val = self.get_input("Volume for all channels:")

        if input_val.lower() == 'q':
            return

        try:
            new_percent = int(input_val)
            new_percent = max(0, min(200, new_percent))
            new_value = new_percent / 100.0

            success_count = 0
            for key, (name, channel_key, _) in AUDIO_CHANNELS.items():
                if self.save_audio_setting(channel_key, new_value):
                    current_settings[channel_key] = new_value
                    success_count += 1

            self.speak(f"Set {success_count} audio channels to {new_percent}%")

        except ValueError:
            self.speak("Invalid input. Enter a number like 50.")

    def mute_all_volumes(self, current_settings):
        """Mute all audio channels."""
        self.speak("Muting all audio channels...")

        success_count = 0
        for key, (name, channel_key, _) in AUDIO_CHANNELS.items():
            if self.save_audio_setting(channel_key, 0.0):
                current_settings[channel_key] = 0.0
                success_count += 1

        self.speak(f"Muted {success_count} audio channels. Set to 0%.")

    def reset_all_volumes(self, current_settings):
        """Reset all audio channels to default (80%)."""
        self.speak("Resetting all audio channels to 80%...")

        success_count = 0
        for key, (name, channel_key, _) in AUDIO_CHANNELS.items():
            # Master defaults to 100%, others to 80%
            default_value = 1.0 if channel_key == "AudioChannelMaster" else 0.8
            if self.save_audio_setting(channel_key, default_value):
                current_settings[channel_key] = default_value
                success_count += 1

        self.speak(f"Reset {success_count} audio channels to defaults.")

    def find_beamng(self):
        """Try to find BeamNG installation."""
        for path in DEFAULT_STEAM_PATHS:
            exe_path = Path(path) / "Bin64" / "BeamNG.drive.x64.exe"
            if exe_path.exists():
                return path
        return None

    def get_input(self, prompt):
        """Get input with screen reader announcement."""
        self.speak(prompt)
        return input().strip()

    def show_menu(self, title, options, return_full=False):
        """Display a menu and get selection."""
        self.speak(title)
        for key, item in options.items():
            name = item[0]
            self.speak(f"{key}: {name}", interrupt=False)

        while True:
            choice = self.get_input("Enter number or 'q' to go back:")
            if choice.lower() == 'q':
                return None
            if choice in options:
                item = options[choice]
                self.speak(f"Selected: {item[0]}")
                if return_full:
                    return item
                return item[1]
            self.speak("Invalid choice. Try again.")

    def configure_beamng_path(self):
        """Configure BeamNG installation path."""
        self.speak("Current BeamNG path: " + (self.beamng_path or "Not set"))
        self.speak("Enter new path or press Enter to auto-detect:")
        new_path = input().strip()

        if not new_path:
            found = self.find_beamng()
            if found:
                self.beamng_path = found
                self.speak(f"Found BeamNG at: {found}")
                self.save_config()
            else:
                self.speak("Could not auto-detect BeamNG.")
        else:
            exe_path = Path(new_path) / "Bin64" / "BeamNG.drive.x64.exe"
            if exe_path.exists():
                self.beamng_path = new_path
                self.speak("Path set successfully.")
                self.save_config()
            else:
                self.speak(f"BeamNG executable not found at {exe_path}")

    def get_mods_path(self):
        """Get the current BeamNG mods path."""
        # Try to find the current version folder
        if BEAMNG_USER_PATH.exists():
            # Look for version folders (0.32, 0.33, current, etc.)
            for folder in sorted(BEAMNG_USER_PATH.iterdir(), reverse=True):
                if folder.is_dir() and (folder.name == 'current' or folder.name.replace('.', '').isdigit()):
                    mods_path = folder / "mods"
                    if mods_path.exists():
                        return mods_path
        return None

    def find_tunable_configs(self):
        """Find all .pc vehicle configs that can be tuned."""
        configs = []
        mods_path = self.get_mods_path()

        if not mods_path:
            return configs

        # Search in unpacked mods and temp folders
        search_paths = [
            mods_path / "unpacked",
            mods_path / "temp_tuning",
        ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            # Find all .pc files
            for pc_file in search_path.rglob("*.pc"):
                # Get relative path from vehicles folder
                try:
                    parts = pc_file.parts
                    if 'vehicles' in parts:
                        vehicles_idx = parts.index('vehicles')
                        rel_path = "/".join(parts[vehicles_idx + 1:])
                        vehicle_name = parts[vehicles_idx + 1] if vehicles_idx + 1 < len(parts) else "unknown"
                        config_name = pc_file.stem

                        configs.append({
                            'path': pc_file,
                            'rel_path': rel_path,
                            'vehicle': vehicle_name,
                            'name': config_name,
                            'display': f"{vehicle_name} - {config_name}"
                        })
                except Exception:
                    pass

        return sorted(configs, key=lambda x: x['display'])

    def load_pc_config(self, path):
        """Load a .pc config file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.speak(f"Error loading config: {e}")
            return None

    def save_pc_config(self, path, config):
        """Save a .pc config file."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            self.speak(f"Error saving config: {e}")
            return False

    def get_current_part(self, config, slot_name):
        """Get the current part in a slot."""
        if 'parts' in config and slot_name in config['parts']:
            return config['parts'][slot_name]
        return ""

    def set_part(self, config, slot_name, part_name):
        """Set a part in the config."""
        if 'parts' not in config:
            config['parts'] = {}
        config['parts'][slot_name] = part_name

    def tuning_category_menu(self, config, category_name, slot_name, parts_dict):
        """Show a tuning category menu and apply selection."""
        current = self.get_current_part(config, slot_name)
        current_name = "None/Default"

        # Find current part name
        for key, (name, part_id) in parts_dict.items():
            if part_id == current:
                current_name = name
                break

        self.speak(f"Current {category_name}: {current_name}")
        self.speak(f"Select new {category_name}:")

        for key, (name, part_id) in parts_dict.items():
            self.speak(f"{key}: {name}", interrupt=False)

        while True:
            choice = self.get_input("Enter number or 'q' to cancel:")
            if choice.lower() == 'q':
                return False
            if choice in parts_dict:
                name, part_id = parts_dict[choice]
                self.set_part(config, slot_name, part_id)
                self.speak(f"{category_name} set to: {name}")
                return True
            self.speak("Invalid choice.")

    def wydra_track_setup_menu(self, config):
        """Apply or remove full track setup for Wydra."""
        self.speak("Track Setup for Wydra")
        self.speak("Note: If using AgentY Tracked Wydra mod, tracks are automatic.")
        self.speak("Only use this to explicitly override track parts.")
        self.speak("1: Force Track Setup (explicitly set all track parts)")
        self.speak("2: Force Wheel Setup (remove track parts)")
        self.speak("3: Use Default (let base vehicle decide - recommended)")

        while True:
            choice = self.get_input("Enter choice or 'q' to cancel:")
            if choice.lower() == 'q':
                return False
            if choice == '1':
                # Apply all track parts explicitly
                for slot, part in TRACK_PARTS.items():
                    self.set_part(config, slot, part)
                # Also set body and axle hubs for tracks
                self.set_part(config, "atv_body", "atv_body_8x8_pressured_agenty")
                self.set_part(config, "atv_axlehubs", "atv_axlehubs_tracks_agenty")
                self.speak("Full track setup applied!")
                return True
            elif choice == '2':
                # Remove track parts (set to empty)
                for slot in TRACK_PARTS.keys():
                    self.set_part(config, slot, "")
                # Set body and axle hubs for wheels
                self.set_part(config, "atv_body", "atv_body_8x8")
                self.set_part(config, "atv_axlehubs", "atv_axlehubs")
                self.speak("Tracks removed, wheel setup applied!")
                return True
            elif choice == '3':
                # Remove any explicit track overrides, let base vehicle handle it
                for slot in TRACK_PARTS.keys():
                    if slot in config.get('parts', {}):
                        del config['parts'][slot]
                # Remove body/axle overrides too
                for slot in ['atv_body', 'atv_axlehubs']:
                    if slot in config.get('parts', {}):
                        del config['parts'][slot]
                self.speak("Track settings cleared - base vehicle will decide.")
                return True
            self.speak("Invalid choice.")

    def wydra_headlights_menu(self, config):
        """Configure headlights for Wydra (affects both left and right)."""
        self.speak("Headlight Configuration")
        self.speak("1: Standard Headlights")
        self.speak("2: Round Headlights")
        self.speak("0: No Headlights")

        while True:
            choice = self.get_input("Enter choice or 'q' to cancel:")
            if choice.lower() == 'q':
                return False
            if choice == '1':
                self.set_part(config, "atv_headlight_L", "atv_headlight_L")
                self.set_part(config, "atv_headlight_R", "atv_headlight_R")
                self.speak("Standard headlights set!")
                return True
            elif choice == '2':
                self.set_part(config, "atv_headlight_L", "atv_headlight_L_round")
                self.set_part(config, "atv_headlight_R", "atv_headlight_R_round")
                self.speak("Round headlights set!")
                return True
            elif choice == '0':
                self.set_part(config, "atv_headlight_L", "")
                self.set_part(config, "atv_headlight_R", "")
                self.speak("Headlights removed!")
                return True
            self.speak("Invalid choice.")

    def tuning_menu(self):
        """Main vehicle tuning menu - edits .pc files directly."""
        self.speak("Vehicle Tuning Menu")
        self.speak("Scanning for tunable vehicle configs...")

        configs = self.find_tunable_configs()

        if not configs:
            self.speak("No tunable vehicle configs found.")
            self.speak("Make sure you have mods with .pc files in your mods folder.")
            return

        self.speak(f"Found {len(configs)} vehicle configs.")

        # Build menu
        config_menu = {}
        for i, cfg in enumerate(configs, 1):
            config_menu[str(i)] = (cfg['display'], cfg)

        # Select vehicle config
        self.speak("Select a vehicle config to tune:")
        for key, (display, _) in config_menu.items():
            self.speak(f"{key}: {display}", interrupt=False)

        while True:
            choice = self.get_input("Enter number or 'q' to go back:")
            if choice.lower() == 'q':
                return
            if choice in config_menu:
                break
            self.speak("Invalid choice.")

        selected = config_menu[choice][1]
        self.speak(f"Selected: {selected['display']}")

        # Load the config
        config = self.load_pc_config(selected['path'])
        if not config:
            return

        # Check if this is a Wydra/ATV vehicle
        is_wydra = config.get('model') == 'atv' or config.get('mainPartName') == 'atv'

        # Tuning category loop
        while True:
            self.speak("Tuning Categories:")
            self.speak("1: Engine Swap")
            self.speak("2: Transmission Swap")
            self.speak("3: Turbocharger")
            self.speak("4: Supercharger")
            self.speak("5: ECU")
            self.speak("6: Engine Internals")
            self.speak("7: Radiator")
            if is_wydra:
                self.speak("--- Wydra/ATV Specific ---")
                self.speak("8: Track Setup (add/remove tracks)")
                self.speak("9: Body Type")
                self.speak("10: Axle Hubs")
                self.speak("11: Paint/Skin")
                self.speak("12: Headlights")
                self.speak("13: Wydra Transmission")
            self.speak("S: Save Changes")
            self.speak("Q: Back (discard unsaved changes)")

            choice = self.get_input("Select category:").lower()

            if choice == '1':
                self.tuning_category_menu(config, "Engine", "engineswap_sample", ENGINES)
            elif choice == '2':
                self.tuning_category_menu(config, "Transmission", "transmissionswap_sample", TRANSMISSIONS)
            elif choice == '3':
                self.tuning_category_menu(config, "Turbocharger", "turboswap_sample", TURBOS)
            elif choice == '4':
                self.tuning_category_menu(config, "Supercharger", "scswap_sample", SUPERCHARGERS)
            elif choice == '5':
                self.tuning_category_menu(config, "ECU", "ecuswap_sample", ECUS)
            elif choice == '6':
                self.tuning_category_menu(config, "Engine Internals", "internalsswap_sample", INTERNALS)
            elif choice == '7':
                self.tuning_category_menu(config, "Radiator", "radiatorswap_sample", RADIATORS)
            elif choice == '8' and is_wydra:
                self.wydra_track_setup_menu(config)
            elif choice == '9' and is_wydra:
                self.tuning_category_menu(config, "Body Type", "atv_body", WYDRA_BODIES)
            elif choice == '10' and is_wydra:
                self.tuning_category_menu(config, "Axle Hubs", "atv_axlehubs", WYDRA_AXLE_HUBS)
            elif choice == '11' and is_wydra:
                self.tuning_category_menu(config, "Paint/Skin", "paint_design", WYDRA_PAINTS)
            elif choice == '12' and is_wydra:
                self.wydra_headlights_menu(config)
            elif choice == '13' and is_wydra:
                self.tuning_category_menu(config, "Wydra Transmission", "atv_transmission", WYDRA_TRANSMISSIONS)
            elif choice == 's':
                if self.save_pc_config(selected['path'], config):
                    self.speak("Changes saved successfully!")
                    self.speak(f"Config saved to: {selected['path']}")
            elif choice == 'q':
                return
            else:
                self.speak("Invalid choice.")

    def create_new_config(self):
        """Create a new tuned vehicle config from scratch."""
        self.speak("Create New Vehicle Config")

        # Select base vehicle
        self.speak("Select base vehicle:")
        vehicle_info = self.show_menu("Base Vehicles:", VEHICLES, return_full=True)
        if not vehicle_info:
            return

        vehicle_name, vehicle_code, _ = vehicle_info

        # Get config name
        config_name = self.get_input("Enter name for new config (no spaces):")
        if not config_name:
            self.speak("Cancelled.")
            return

        config_name = config_name.replace(" ", "_").lower()

        # Create base config
        config = {
            "format": 2,
            "mainPartName": vehicle_code,
            "model": vehicle_code,
            "parts": {
                "n2o_system": "AgentY_engine_swaps",  # Enable engine swap system
                "engineswap_sample": "",
                "transmissionswap_sample": "",
                "turboswap_sample": "",
                "scswap_sample": "",
                "ecuswap_sample": "",
                "internalsswap_sample": "",
                "radiatorswap_sample": "",
            }
        }

        # Determine save path
        mods_path = self.get_mods_path()
        if not mods_path:
            self.speak("Could not find mods folder.")
            return

        # Save to blind_accessibility mod folder
        save_dir = mods_path / "unpacked" / "blind_accessibility.zip" / "vehicles" / vehicle_code
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / f"{config_name}.pc"

        # Apply tuning
        self.speak("Now configure your tuning options.")

        while True:
            self.speak("Tuning Categories:")
            self.speak("1: Engine Swap")
            self.speak("2: Transmission Swap")
            self.speak("3: Turbocharger")
            self.speak("4: Supercharger")
            self.speak("5: ECU")
            self.speak("6: Engine Internals")
            self.speak("7: Radiator")
            self.speak("S: Save and Finish")
            self.speak("Q: Cancel")

            choice = self.get_input("Select category:").lower()

            if choice == '1':
                self.tuning_category_menu(config, "Engine", "engineswap_sample", ENGINES)
            elif choice == '2':
                self.tuning_category_menu(config, "Transmission", "transmissionswap_sample", TRANSMISSIONS)
            elif choice == '3':
                self.tuning_category_menu(config, "Turbocharger", "turboswap_sample", TURBOS)
            elif choice == '4':
                self.tuning_category_menu(config, "Supercharger", "scswap_sample", SUPERCHARGERS)
            elif choice == '5':
                self.tuning_category_menu(config, "ECU", "ecuswap_sample", ECUS)
            elif choice == '6':
                self.tuning_category_menu(config, "Engine Internals", "internalsswap_sample", INTERNALS)
            elif choice == '7':
                self.tuning_category_menu(config, "Radiator", "radiatorswap_sample", RADIATORS)
            elif choice == 's':
                if self.save_pc_config(save_path, config):
                    self.speak("New config created successfully!")
                    self.speak(f"Saved to: {save_path}")
                    self.speak(f"Use vehicle config: {vehicle_code}/{config_name}.pc")
                return
            elif choice == 'q':
                self.speak("Cancelled.")
                return

    def launch_freeroam(self):
        """Launch BeamNG in freeroam mode."""
        if not self.beamng_path:
            self.speak("BeamNG path not configured.")
            self.configure_beamng_path()
            if not self.beamng_path:
                return

        # Select map
        self.speak("Select a map for freeroam:")
        map_code = self.show_menu("Available Maps:", MAPS)
        if not map_code:
            return

        # Select vehicle
        self.speak("Select a vehicle:")
        vehicle_info = self.show_menu("Available Vehicles:", VEHICLES, return_full=True)
        if not vehicle_info:
            return

        vehicle_name, vehicle_code, vehicle_config = vehicle_info

        # Build command
        exe_path = Path(self.beamng_path) / "Bin64" / "BeamNG.drive.x64.exe"
        args = [str(exe_path), "-level", f"{map_code}/main"]

        if vehicle_config:
            args.extend(["-vehicleConfig", vehicle_config])
        else:
            args.extend(["-vehicle", vehicle_code])

        self.speak(f"Launching BeamNG with {map_code} and {vehicle_name}...")

        try:
            subprocess.Popen(args, cwd=str(Path(self.beamng_path) / "Bin64"))
            self.speak("BeamNG is starting.")
        except Exception as e:
            self.speak(f"Error launching: {e}")

    def quick_launch(self, map_code, vehicle_code, vehicle_config=None):
        """Quick launch with specific map and vehicle."""
        if not self.beamng_path:
            self.speak("BeamNG path not configured.")
            return

        exe_path = Path(self.beamng_path) / "Bin64" / "BeamNG.drive.x64.exe"
        args = [str(exe_path), "-level", f"{map_code}/main"]

        if vehicle_config:
            args.extend(["-vehicleConfig", vehicle_config])
        else:
            args.extend(["-vehicle", vehicle_code])

        map_name = next((name for key, (name, code) in MAPS.items() if code == map_code), map_code)
        vehicle_name = next((name for key, (name, code, *_) in VEHICLES.items() if code == vehicle_code), vehicle_code)

        self.speak(f"Quick launching: {map_name} with {vehicle_name}")

        try:
            subprocess.Popen(args, cwd=str(Path(self.beamng_path) / "Bin64"))
        except Exception as e:
            self.speak(f"Error: {e}")

    def launch_custom_config(self):
        """Launch with a custom tuned config."""
        if not self.beamng_path:
            self.speak("BeamNG path not configured.")
            return

        # Find configs
        configs = self.find_tunable_configs()
        if not configs:
            self.speak("No custom configs found.")
            return

        # Select config
        config_menu = {}
        for i, cfg in enumerate(configs, 1):
            config_menu[str(i)] = (cfg['display'], cfg)

        self.speak("Select a custom config to launch:")
        for key, (display, _) in config_menu.items():
            self.speak(f"{key}: {display}", interrupt=False)

        while True:
            choice = self.get_input("Enter number or 'q' to cancel:")
            if choice.lower() == 'q':
                return
            if choice in config_menu:
                break
            self.speak("Invalid choice.")

        selected = config_menu[choice][1]

        # Select map
        map_code = self.show_menu("Select Map:", MAPS)
        if not map_code:
            return

        # Launch
        exe_path = Path(self.beamng_path) / "Bin64" / "BeamNG.drive.x64.exe"
        args = [
            str(exe_path),
            "-level", f"{map_code}/main",
            "-vehicleConfig", selected['rel_path']
        ]

        self.speak(f"Launching with {selected['display']}...")

        try:
            subprocess.Popen(args, cwd=str(Path(self.beamng_path) / "Bin64"))
        except Exception as e:
            self.speak(f"Error: {e}")

    def main_menu(self):
        """Show main menu."""
        while True:
            self.speak("BeamNG Accessible Launcher - Main Menu")
            self.speak("1: Launch Freeroam (select map and vehicle)")
            self.speak("2: Quick Launch - Grid Map with Pickup")
            self.speak("3: Quick Launch - West Coast with Sunburst")
            self.speak("4: Quick Launch - Utah with Rock Crawler")
            self.speak("5: Quick Launch - Grid with Tracked Wydra (mod)")
            self.speak("6: Launch Custom Tuned Config")
            self.speak("T: Tune Existing Vehicle Config")
            self.speak("N: Create New Tuned Config")
            self.speak("A: Audio Settings")
            self.speak("C: Configure BeamNG Path")
            self.speak("Q: Quit")

            choice = self.get_input("Enter choice:").lower()

            if choice == '1':
                self.launch_freeroam()
            elif choice == '2':
                self.quick_launch("gridmap_v2", "pickup")
            elif choice == '3':
                self.quick_launch("west_coast_usa", "sunburst")
            elif choice == '4':
                self.quick_launch("utah", "rockbasher")
            elif choice == '5':
                self.quick_launch("gridmap_v2", "atv", "atv/base_tracks_agenty.pc")
            elif choice == '6':
                self.launch_custom_config()
            elif choice == 't':
                self.tuning_menu()
            elif choice == 'n':
                self.create_new_config()
            elif choice == 'a':
                self.audio_settings_menu()
            elif choice == 'c':
                self.configure_beamng_path()
            elif choice == 'q':
                self.speak("Goodbye!")
                break
            else:
                self.speak("Invalid choice.")

    def cleanup(self):
        """Clean up resources."""
        if self.tolk_initialized:
            try:
                tolk.unload()
            except Exception:
                pass


def main():
    launcher = AccessibleLauncher()
    try:
        launcher.main_menu()
    finally:
        launcher.cleanup()


if __name__ == "__main__":
    main()
