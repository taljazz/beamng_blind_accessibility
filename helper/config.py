"""
BeamNG Blind Accessibility Helper - Configuration
"""

# UDP Configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 4445
BUFFER_SIZE = 4096

# Screen Reader Configuration
SCREEN_READER = "auto"  # "nvda", "jaws", "sapi", "auto"
INTERRUPT_SPEECH = True
SPEECH_RATE = 200  # Words per minute for SAPI fallback

# Message Type Constants (must match Lua protocol)
MSG_TYPE_MENU = 0x01
MSG_TYPE_VEHICLE = 0x02
MSG_TYPE_ALERT = 0x03
MSG_TYPE_DIALOG = 0x04
MSG_TYPE_STATUS = 0x05

# Verbosity
ANNOUNCE_VEHICLE_TELEMETRY = False  # Set True to hear speed/rpm updates
TELEMETRY_INTERVAL = 2.0  # Seconds between telemetry announcements

# Logging
DEBUG_MODE = True
LOG_FILE = "beamng_accessibility.log"
