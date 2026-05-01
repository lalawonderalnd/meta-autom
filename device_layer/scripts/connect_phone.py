#!/usr/bin/env python3
"""Helper script to enable Wi-Fi ADB on a USB-connected phone."""

import argparse
import subprocess
import sys


def find_usb_devices() -> list[str]:
    """Find all USB-connected Android devices."""
    result = subprocess.run(
        ["adb", "devices"],
        capture_output=True,
        text=True,
    )
    devices = []
    for line in result.stdout.splitlines()[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device" and ":" not in parts[0]:
            devices.append(parts[0])
    return devices


def enable_wifi_adb(serial: str) -> bool:
    """Enable Wi-Fi ADB on a USB-connected device."""
    print(f"Enabling Wi-Fi ADB on {serial}...")

    # Enable TCP/IP mode on port 5555
    result = subprocess.run(
        ["adb", "-s", serial, "tcpip", "5555"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False

    print(result.stdout.strip())
    return True


def get_device_ip(serial: str) -> str | None:
    """Get the Wi-Fi IP address of a device."""
    result = subprocess.run(
        ["adb", "-s", serial, "shell", "ip", "-f", "inet", "addr", "show", "wlan0"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Try alternative command for older Android versions
        result = subprocess.run(
            ["adb", "-s", serial, "shell", "ifconfig", "wlan0"],
            capture_output=True,
            text=True,
        )

    output = result.stdout
    # Parse IP from output
    for line in output.splitlines():
        if "inet " in line:
            parts = line.split()
            for part in parts:
                if "/" in part:
                    ip = part.split("/")[0]
                    if ip.startswith("192.168.") or ip.startswith("10."):
                        return ip

    return None


def connect_wifi(serial: str, ip: str, port: int = 5555) -> bool:
    """Connect to a device via Wi-Fi ADB."""
    print(f"Connecting to {ip}:{port}...")

    result = subprocess.run(
        ["adb", "connect", f"{ip}:{port}"],
        capture_output=True,
        text=True,
    )

    print(result.stdout.strip())
    return "connected" in result.stdout.lower() or "already connected" in result.stdout.lower()


def main():
    parser = argparse.ArgumentParser(description="Enable Wi-Fi ADB on USB-connected phones")
    parser.add_argument(
        "--serial",
        help="USB serial of the device (auto-detected if not provided)",
    )
    parser.add_argument(
        "--connect",
        action="store_true",
        help="Automatically connect via Wi-Fi after enabling",
    )
    args = parser.parse_args()

    # Find devices
    devices = find_usb_devices()

    if not devices:
        print("No USB-connected Android devices found.")
        print("Make sure:")
        print("  1. USB debugging is enabled on the device")
        print("  2. Device is connected via USB")
        print("  3. You've authorized this computer on the device")
        sys.exit(1)

    print(f"Found {len(devices)} USB-connected device(s):")
    for i, dev in enumerate(devices):
        print(f"  {i + 1}. {dev}")

    # Select device
    if args.serial:
        if args.serial not in devices:
            print(f"Error: Device {args.serial} not found")
            sys.exit(1)
        serial = args.serial
    else:
        if len(devices) == 1:
            serial = devices[0]
        else:
            print("\nPlease specify --serial to select a device")
            sys.exit(1)

    # Enable Wi-Fi ADB
    if not enable_wifi_adb(serial):
        print("Failed to enable Wi-Fi ADB")
        sys.exit(1)

    # Wait for device to switch
    print("Waiting for device to switch to TCP/IP mode...")
    import time
    time.sleep(2)

    # Get IP and optionally connect
    if args.connect:
        ip = get_device_ip(serial)
        if not ip:
            print("Could not determine device IP address")
            print("Please manually connect with: adb connect <DEVICE_IP>:5555")
            sys.exit(1)

        print(f"Device IP: {ip}")

        if connect_wifi(serial, ip):
            print("\nSuccess! You can now disconnect USB and use Wi-Fi ADB.")
            print(f"Connect with: adb connect {ip}:5555")
        else:
            print("Failed to connect via Wi-Fi")
            sys.exit(1)
    else:
        ip = get_device_ip(serial)
        if ip:
            print(f"\nDevice IP: {ip}")
            print(f"Connect with: adb connect {ip}:5555")
        else:
            print("\nCould not determine device IP.")
            print("Run 'adb shell ip addr show wlan0' manually to find it.")


if __name__ == "__main__":
    main()
