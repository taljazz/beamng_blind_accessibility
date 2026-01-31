"""
BeamNG Blind Accessibility Helper - Speech Output Module

Handles text-to-speech output via:
1. cytolk library (NVDA, JAWS, etc.)
2. Windows SAPI (fallback via pyttsx3)
"""

import config

# Global state
_tolk = None
_sapi_engine = None
_current_backend = None


def _init_cytolk():
    """Initialize cytolk for screen reader access."""
    global _tolk

    try:
        import cytolk.tolk as tolk
        tolk.load()
        tolk.try_sapi(True)  # Enable SAPI fallback

        if tolk.is_loaded():
            _tolk = tolk
            screen_reader = tolk.detect_screen_reader() or "SAPI"
            print(f"[Speech] cytolk initialized, detected: {screen_reader}")
            return True
        else:
            print("[Speech] cytolk loaded but not active")
            return False

    except ImportError:
        print("[Speech] cytolk not available")
        return False
    except Exception as e:
        print(f"[Speech] cytolk error: {e}")
        return False


def _init_sapi():
    """Initialize Windows SAPI as fallback."""
    global _sapi_engine

    try:
        import pyttsx3
        _sapi_engine = pyttsx3.init()
        _sapi_engine.setProperty('rate', config.SPEECH_RATE)
        print("[Speech] SAPI (pyttsx3) initialized")
        return True
    except ImportError:
        print("[Speech] pyttsx3 not available")
        return False
    except Exception as e:
        print(f"[Speech] SAPI error: {e}")
        return False


def init():
    """Initialize the speech system."""
    global _current_backend

    preferred = config.SCREEN_READER.lower()

    # Try backends in order of preference
    if preferred in ("auto", "nvda", "jaws"):
        if _init_cytolk():
            _current_backend = "cytolk"
            return True

    if preferred in ("auto", "sapi"):
        if _init_sapi():
            _current_backend = "sapi"
            return True

    print("[Speech] WARNING: No speech backend available!")
    return False


def speak(text, interrupt=None):
    """
    Speak text through the active screen reader.

    Args:
        text: The text to speak
        interrupt: Whether to interrupt current speech (default from config)
    """
    if not text:
        return False

    if interrupt is None:
        interrupt = config.INTERRUPT_SPEECH

    if config.DEBUG_MODE:
        print(f"[Speech] Speaking: {text}")

    try:
        if _current_backend == "cytolk" and _tolk:
            return _tolk.output(text, interrupt)

        elif _current_backend == "sapi" and _sapi_engine:
            if interrupt:
                _sapi_engine.stop()
            _sapi_engine.say(text)
            _sapi_engine.runAndWait()
            return True

    except Exception as e:
        print(f"[Speech] Error speaking: {e}")

    return False


def silence():
    """Stop current speech."""
    try:
        if _current_backend == "cytolk" and _tolk:
            return _tolk.silence()

        elif _current_backend == "sapi" and _sapi_engine:
            _sapi_engine.stop()
            return True

    except Exception as e:
        print(f"[Speech] Error silencing: {e}")

    return False


def get_screen_reader():
    """Get the name of the active screen reader."""
    try:
        if _current_backend == "cytolk" and _tolk:
            sr = _tolk.detect_screen_reader()
            return sr if sr else "SAPI"

        elif _current_backend == "sapi":
            return "SAPI"

    except Exception as e:
        print(f"[Speech] Error getting screen reader: {e}")

    return "Unknown"


def cleanup():
    """Clean up speech resources."""
    global _tolk, _sapi_engine

    try:
        if _tolk:
            _tolk.unload()
            _tolk = None
            print("[Speech] cytolk unloaded")

        if _sapi_engine:
            _sapi_engine.stop()
            print("[Speech] SAPI stopped")

    except Exception as e:
        print(f"[Speech] Cleanup error: {e}")


# Test function
if __name__ == "__main__":
    print("Testing speech module...")
    if init():
        print(f"Using: {get_screen_reader()}")
        speak("BeamNG Blind Accessibility speech test")
        import time
        time.sleep(2)
        speak("Test complete", interrupt=True)
        cleanup()
    else:
        print("Speech initialization failed")
