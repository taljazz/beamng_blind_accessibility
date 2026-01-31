"""
BeamNG Blind Accessibility Helper

Main entry point for the external helper application that provides
NVDA/screen reader support for the BeamNG Blind Accessibility mod.

Usage:
    python main.py

The helper listens for UDP packets from the BeamNG mod and speaks
the content through the active screen reader (NVDA, JAWS, or SAPI).
"""

import sys
import time
import signal
import argparse

import config
import speech
import udp_listener


def print_banner():
    """Print startup banner."""
    print("=" * 60)
    print("  BeamNG Blind Accessibility Helper")
    print("=" * 60)
    print()


def print_config():
    """Print current configuration."""
    print(f"Configuration:")
    print(f"  UDP Address: {config.UDP_IP}:{config.UDP_PORT}")
    print(f"  Screen Reader: {config.SCREEN_READER}")
    print(f"  Interrupt Speech: {config.INTERRUPT_SPEECH}")
    print(f"  Debug Mode: {config.DEBUG_MODE}")
    print()


def setup_signal_handlers(shutdown_callback):
    """Set up signal handlers for clean shutdown."""
    def handler(signum, frame):
        print("\nShutdown signal received...")
        shutdown_callback()
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="BeamNG Blind Accessibility Helper"
    )
    parser.add_argument(
        "--port", type=int, default=config.UDP_PORT,
        help=f"UDP port to listen on (default: {config.UDP_PORT})"
    )
    parser.add_argument(
        "--debug", action="store_true", default=config.DEBUG_MODE,
        help="Enable debug output"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Run a quick speech test and exit"
    )
    args = parser.parse_args()

    # Apply command line overrides
    config.UDP_PORT = args.port
    config.DEBUG_MODE = args.debug

    print_banner()
    print_config()

    # Initialize speech system
    print("Initializing speech system...")
    if not speech.init():
        print("ERROR: Failed to initialize speech system!")
        print("Make sure NVDA is running or pyttsx3 is installed.")
        sys.exit(1)

    screen_reader = speech.get_screen_reader()
    print(f"Using screen reader: {screen_reader}")
    print()

    # Test mode
    if args.test:
        print("Running speech test...")
        speech.speak("BeamNG Blind Accessibility helper is working correctly.")
        time.sleep(3)
        print("Test complete.")
        speech.cleanup()
        return

    # Set up shutdown handler
    def shutdown():
        print("Shutting down...")
        udp_listener.stop()
        speech.cleanup()
        print("Goodbye!")

    setup_signal_handlers(shutdown)

    # Start UDP listener
    print("Starting UDP listener...")
    if not udp_listener.start():
        print("ERROR: Failed to start UDP listener!")
        speech.cleanup()
        sys.exit(1)

    # Announce startup
    speech.speak(f"BeamNG Blind Accessibility helper started. Using {screen_reader}.")

    print()
    print("=" * 60)
    print("  Helper is running. Waiting for BeamNG...")
    print("  Press Ctrl+C to stop.")
    print("=" * 60)
    print()

    # Main loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
