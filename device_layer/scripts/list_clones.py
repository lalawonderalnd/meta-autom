#!/usr/bin/env python3
"""Helper script to list all Instagram clones on connected devices."""

import argparse
import sys

from accfarm_device.adb_client import AdbClient
from accfarm_device.device import Device, DeviceStatus
from uuid import uuid4


def list_all_clones(adb_host: str = "127.0.0.1", adb_port: int = 5037):
    """List all Instagram clones on all connected devices."""
    adb_client = AdbClient(host=adb_host, port=adb_port)

    # Get connected devices
    devices = adb_client.list_devices()

    if not devices:
        print("No devices connected via ADB")
        return

    print(f"Found {len(devices)} connected device(s)\n")

    for adb_device in devices:
        serial = adb_device.serial
        print(f"Device: {serial}")
        print("-" * 50)

        # Create Device wrapper
        device = Device(
            id=uuid4(),
            serial=serial,
            name=serial,
            ip=None,  # Not needed for USB
            adb_port=5555,
            status=DeviceStatus.ONLINE,
        )
        device.set_adb_client(adb_client)

        try:
            # List Instagram packages
            output = adb_client.shell(serial, "pm list packages | grep instagram")

            if not output.strip():
                print("  No Instagram clones found")
            else:
                packages = [line.replace("package:", "").strip() for line in output.splitlines() if line.strip()]

                for pkg in packages:
                    clone_info = get_clone_info(adb_client, serial, pkg)
                    print(f"  - {pkg}")
                    if clone_info.get("version_name"):
                        print(f"      Version: {clone_info['version_name']}")
                    if clone_info.get("label"):
                        print(f"      Label: {clone_info['label']}")
                    if clone_info.get("launch_activity"):
                        print(f"      Launch: {clone_info['launch_activity']}")

        except Exception as e:
            print(f"  Error: {e}")

        print()


def get_clone_info(adb_client: AdbClient, serial: str, package: str) -> dict:
    """Get detailed info about a clone package."""
    info = {}

    try:
        # Get version name and label
        output = adb_client.shell(
            serial,
            f"dumpsys package {package} | grep -E 'versionName|label'",
            timeout=10,
        )

        for line in output.splitlines():
            if "versionName=" in line:
                info["version_name"] = line.split("=")[1].strip()
            elif "label=" in line:
                info["label"] = line.split("=")[1].strip()

        # Detect launch activity
        output = adb_client.shell(
            serial,
            f"dumpsys package {package} | grep -A 1 'android.intent.action.MAIN'",
            timeout=10,
        )

        lines = output.splitlines()
        for i, line in enumerate(lines):
            if "android.intent.action.MAIN" in line and i + 1 < len(lines):
                next_line = lines[i + 1]
                if "/" in next_line:
                    activity = next_line.strip().split("/")[-1].split(" ")[0]
                    info["launch_activity"] = f"{package}.{activity}"
                    break

        if "launch_activity" not in info:
            info["launch_activity"] = f"{package}.activity.MainTabActivity"

    except Exception as e:
        info["error"] = str(e)

    return info


def main():
    parser = argparse.ArgumentParser(description="List Instagram clones on connected devices")
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
    args = parser.parse_args()

    try:
        list_all_clones(args.adb_host, args.adb_port)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
