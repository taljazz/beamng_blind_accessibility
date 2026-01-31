"""
BeamNG Blind Accessibility Helper - UDP Listener Module

Listens for UDP packets from the BeamNG mod and processes them.
"""

import socket
import struct
import threading
import time
import config
import speech

# Protocol constants
HEADER = b"BNBA"
HEADER_SIZE = 4
TYPE_SIZE = 1
LENGTH_SIZE = 2


class UDPListener:
    """Listens for accessibility packets from BeamNG."""

    def __init__(self, ip=None, port=None):
        self.ip = ip or config.UDP_IP
        self.port = port or config.UDP_PORT
        self.socket = None
        self.running = False
        self.thread = None
        self.last_telemetry_time = 0
        self.callbacks = {
            config.MSG_TYPE_MENU: self._handle_menu,
            config.MSG_TYPE_VEHICLE: self._handle_vehicle,
            config.MSG_TYPE_ALERT: self._handle_alert,
            config.MSG_TYPE_DIALOG: self._handle_dialog,
            config.MSG_TYPE_STATUS: self._handle_status,
        }

    def start(self):
        """Start listening for UDP packets."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.ip, self.port))
            self.socket.settimeout(1.0)  # Allow periodic checks for stop signal

            self.running = True
            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()

            print(f"[UDP] Listening on {self.ip}:{self.port}")
            return True

        except Exception as e:
            print(f"[UDP] Failed to start listener: {e}")
            return False

    def stop(self):
        """Stop listening."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.socket:
            self.socket.close()
            self.socket = None
        print("[UDP] Listener stopped")

    def _listen_loop(self):
        """Main listening loop."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(config.BUFFER_SIZE)
                self._process_packet(data)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[UDP] Error receiving: {e}")

    def _process_packet(self, data):
        """Process a received packet."""
        if len(data) < HEADER_SIZE + TYPE_SIZE + LENGTH_SIZE:
            if config.DEBUG_MODE:
                print(f"[UDP] Packet too short: {len(data)} bytes")
            return

        # Verify header
        header = data[:HEADER_SIZE]
        if header != HEADER:
            if config.DEBUG_MODE:
                print(f"[UDP] Invalid header: {header}")
            return

        # Extract message type and length
        msg_type = data[HEADER_SIZE]
        length = (data[HEADER_SIZE + 1] << 8) | data[HEADER_SIZE + 2]

        # Extract payload
        payload_start = HEADER_SIZE + TYPE_SIZE + LENGTH_SIZE
        payload = data[payload_start:payload_start + length].decode('utf-8', errors='replace')

        if config.DEBUG_MODE:
            print(f"[UDP] Received: type={msg_type}, len={length}, payload={payload[:50]}...")

        # Route to handler
        handler = self.callbacks.get(msg_type)
        if handler:
            handler(payload)
        else:
            print(f"[UDP] Unknown message type: {msg_type}")

    def _handle_menu(self, payload):
        """Handle menu navigation events."""
        # Payload format: "text|index|total" or just "text"
        parts = payload.split('|')
        text = parts[0] if parts else ""

        if len(parts) >= 3:
            try:
                index = int(parts[1])
                total = int(parts[2])
                if total > 0:
                    text = f"{text}, {index} of {total}"
            except ValueError:
                pass

        if text:
            speech.speak(text, interrupt=True)

    def _handle_vehicle(self, payload):
        """Handle vehicle telemetry updates."""
        if not config.ANNOUNCE_VEHICLE_TELEMETRY:
            return

        # Rate limit telemetry announcements
        current_time = time.time()
        if current_time - self.last_telemetry_time < config.TELEMETRY_INTERVAL:
            return
        self.last_telemetry_time = current_time

        # Payload format: "speed|rpm|gear|steering|surface"
        parts = payload.split('|')
        if len(parts) >= 4:
            try:
                speed = float(parts[0])
                rpm = int(parts[1])
                gear = parts[2]
                steering = float(parts[3])

                # Build announcement
                announcement = f"{int(speed)} kilometers per hour"
                if gear:
                    announcement += f", gear {gear}"

                speech.speak(announcement, interrupt=False)
            except ValueError as e:
                if config.DEBUG_MODE:
                    print(f"[UDP] Invalid telemetry data: {e}")

    def _handle_alert(self, payload):
        """Handle important alerts (always speak, high priority)."""
        # Payload format: "text|priority"
        parts = payload.split('|')
        text = parts[0] if parts else ""

        if text:
            # Alerts always interrupt
            speech.speak(text, interrupt=True)

    def _handle_dialog(self, payload):
        """Handle dialog box announcements."""
        # Payload format: "title|content|options"
        parts = payload.split('|')
        title = parts[0] if len(parts) > 0 else ""
        content = parts[1] if len(parts) > 1 else ""
        options = parts[2] if len(parts) > 2 else ""

        # Build announcement
        announcement = ""
        if title:
            announcement = f"Dialog: {title}. "
        if content:
            announcement += f"{content} "
        if options:
            announcement += f"Options: {options}"

        if announcement:
            speech.speak(announcement.strip(), interrupt=True)

    def _handle_status(self, payload):
        """Handle status updates."""
        if payload:
            speech.speak(payload, interrupt=False)


# Singleton instance
_listener = None


def get_listener():
    """Get the singleton listener instance."""
    global _listener
    if _listener is None:
        _listener = UDPListener()
    return _listener


def start():
    """Start the UDP listener."""
    return get_listener().start()


def stop():
    """Stop the UDP listener."""
    if _listener:
        _listener.stop()


# Test function
if __name__ == "__main__":
    print("Testing UDP listener...")
    speech.init()

    if start():
        print("Listener running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            stop()

    speech.cleanup()
