#!/usr/bin/env python3
"""Helper script to print pool state for ops."""

import argparse
import sys
from datetime import datetime, timezone

from accfarm_device.adb_client import AdbClient
from accfarm_device.device import Device, DeviceStatus
from accfarm_device.health import HealthChecker
from uuid import uuid4


def print_farm_status(adb_host: str = "127.0.0.1", adb_port: int = 5037):
    """Print the current state of the device farm."""
    adb_client = AdbClient(host=adb_host, port=adb_port)
    health_checker = HealthChecker()

    # Get connected devices
    try:
        devices = adb_client.list_devices()
    except Exception as e:
        print(f"Error connecting to ADB server: {e}", file=sys.stderr)
        print("Make sure ADB server is running: adb start-server")
        sys.exit(1)

    if not devices:
        print("No devices connected via ADB")
        return

    print("=" * 70)
    print("ACCFARM DEVICE STATUS")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"ADB Server: {adb_host}:{adb_port}")
    print(f"Total Devices: {len(devices)}")
    print()

    online_count = 0
    offline_count = 0
    total_clones = 0

    for adb_device in devices:
        serial = adb_device.serial
        is_wifi = ":" in serial

        # Create Device wrapper
        device = Device(
            id=uuid4(),
            serial=serial,
            name=serial,
            ip=serial.split(":")[0] if is_wifi else None,
            adb_port=int(serial.split(":")[1]) if is_wifi and ":" in serial.split(":")[1] else 5555,
            status=DeviceStatus.ONLINE,
        )
        device.set_adb_client(adb_client)

        # Check health
        try:
            is_online = adb_client.check_connection(serial)
        except Exception:
            is_online = False

        if is_online:
            online_count += 1
            status_str = "🟢 ONLINE"
        else:
            offline_count += 1
            status_str = "🔴 OFFLINE"

        print(f"┌─ Device: {serial}")
        print(f"│  Status: {status_str}")
        print(f"│  Connection: {'Wi-Fi' if is_wifi else 'USB'}")

        if is_online:
            try:
                # Get device info
                device.refresh_info()

                if device.manufacturer:
                    print(f"│  Model: {device.manufacturer} {device.model}")
                if device.android_version:
                    print(f"│  Android: {device.android_version}")

                # Get health stats
                health = health_checker.check(device)

                if health.battery_level is not None:
                    battery_icon = "🔋" if health.battery_charging else "🪫"
                    print(f"│  Battery: {battery_icon} {health.battery_level}%{' (charging)' if health.battery_charging else ''}")

                if health.temperature_c is not None:
                    temp_icon = "🌡️"
                    print(f"│  Temperature: {temp_icon} {health.temperature_c}°C")

                if health.screen_on:
                    print(f"│  Screen: 📱 ON")
                else:
                    print(f"│  Screen: 📱 OFF")

                if health.foreground_app:
                    print(f"│  Foreground: {health.foreground_app}")

                if health.atx_agent_running:
                    print(f"│  ATX Agent: ✅ Running")
                else:
                    print(f"│  ATX Agent: ❌ Not running")

                # List clones
                output = adb_client.shell(serial, "pm list packages | grep instagram", timeout=10)
                clones = [line.replace("package:", "").strip() for line in output.splitlines() if line.strip()]
                total_clones += len(clones)

                if clones:
                    print(f"│  Instagram Clones: {len(clones)}")
                    for clone in clones[:5]:  # Show first 5
                        print(f"│    - {clone}")
                    if len(clones) > 5:
                        print(f"│    ... and {len(clones) - 5} more")
                else:
                    print(f"│  Instagram Clones: 0")

            except Exception as e:
                print(f"│  Error getting details: {e}")
        else:
            print(f"│  (Device unreachable)")

        print("└─")
        print()

    print("=" * 70)
    print(f"Summary: {online_count} online, {offline_count} offline, {total_clones} total IG clones")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Print AccFarm device pool status")
    parser.add_argument(
        "--adb-host",
        default="127.0.0.1",
        help="ADB server host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--adb-port",
        type=int,
        default=5037,
        help="ADB server port (default: 5037)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    try:
        if args.json:
            # TODO: Implement JSON output
            print("JSON output not yet implemented", file=sys.stderr)
            sys.exit(1)
        else:
            print_farm_status(args.adb_host, args.adb_port)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
