"""
End-to-end test for BeamNG Blind Accessibility Helper

Tests the full pipeline: UDP packet -> listener -> speech output
"""

import socket
import time
import threading

import config
import speech
import udp_listener


def send_test_packet(msg_type, payload, delay=0):
    """Send a test packet to the listener."""
    time.sleep(delay)

    header = b'BNBA'
    msg_type_byte = bytes([msg_type])
    payload_bytes = payload.encode('utf-8')
    length = len(payload_bytes)
    length_bytes = bytes([length >> 8, length & 0xFF])

    packet = header + msg_type_byte + length_bytes + payload_bytes

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(packet, (config.UDP_IP, config.UDP_PORT))
    sock.close()
    print(f"[Test] Sent: {payload}")


def run_test():
    print("=" * 50)
    print("BeamNG Blind Accessibility - End-to-End Test")
    print("=" * 50)
    print()

    # Initialize speech
    print("[Test] Initializing speech...")
    if not speech.init():
        print("[Test] FAILED: Speech initialization failed!")
        return False

    print(f"[Test] Using screen reader: {speech.get_screen_reader()}")
    print()

    # Start UDP listener
    print("[Test] Starting UDP listener...")
    if not udp_listener.start():
        print("[Test] FAILED: UDP listener failed to start!")
        speech.cleanup()
        return False

    print(f"[Test] Listening on {config.UDP_IP}:{config.UDP_PORT}")
    print()

    # Give listener time to start
    time.sleep(0.5)

    # Send test packets
    print("[Test] Sending test packets...")
    print()

    # Test 1: Menu event
    send_test_packet(config.MSG_TYPE_MENU, "Main Menu|1|5")
    time.sleep(2)

    # Test 2: Another menu item
    send_test_packet(config.MSG_TYPE_MENU, "Play|2|5")
    time.sleep(2)

    # Test 3: Alert
    send_test_packet(config.MSG_TYPE_ALERT, "Vehicle spawned: ETK 800|1")
    time.sleep(2)

    # Test 4: Status
    send_test_packet(config.MSG_TYPE_STATUS, "Loading complete")
    time.sleep(2)

    # Test 5: Dialog
    send_test_packet(config.MSG_TYPE_DIALOG, "Confirm|Are you sure you want to exit?|Yes,No")
    time.sleep(3)

    # Cleanup
    print()
    print("[Test] Cleaning up...")
    udp_listener.stop()
    speech.cleanup()

    print()
    print("=" * 50)
    print("Test complete! Did you hear the announcements?")
    print("=" * 50)

    return True


if __name__ == "__main__":
    run_test()
