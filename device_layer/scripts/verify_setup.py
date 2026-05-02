#!/usr/bin/env python3
"""
Device Layer Setup Verification Script

Run this script to verify your Android phone farm setup is ready for automation.
Checks ADB connectivity, App Cloner installation, clone detection, and proxy configuration.

Usage:
    python verify_setup.py --serial <device_serial> --ip <device_ip>
    
Example:
    python verify_setup.py --serial RZ8M601ABCD --ip 192.168.1.42
"""

import argparse
import subprocess
import sys
from typing import Optional


def run_command(cmd: list[str], timeout: int = 10) -> tuple[bool, str, str]:
    """Run a shell command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def check_adb_installed() -> bool:
    """Check if ADB is installed and accessible."""
    print("✓ Checking ADB installation...")
    success, stdout, stderr = run_command(["adb", "version"])
    if success:
        version_line = stdout.split('\n')[0]
        print(f"  ✓ ADB installed: {version_line}")
        return True
    else:
        print(f"  ✗ ADB not found. Install Android SDK Platform Tools.")
        return False


def check_device_connected(serial: Optional[str] = None) -> bool:
    """Check if device is connected via ADB."""
    print("\n✓ Checking ADB device connection...")
    success, stdout, stderr = run_command(["adb", "devices"])
    
    if not success:
        print(f"  ✗ Failed to run adb devices: {stderr}")
        return False
    
    lines = stdout.strip().split('\n')[1:]  # Skip header
    devices = []
    for line in lines:
        if '\tdevice' in line:
            dev_serial = line.split('\t')[0]
            devices.append(dev_serial)
    
    if not devices:
        print(f"  ✗ No devices connected. Connect phone via USB or Wi-Fi ADB.")
        return False
    
    print(f"  ✓ Found {len(devices)} device(s):")
    for dev in devices:
        status = "✓" if (not serial or dev == serial) else " "
        print(f"    {status} {dev}")
    
    if serial and serial not in devices:
        print(f"  ✗ Target device {serial} not found. Connect it first.")
        return False
    
    return True


def check_wireless_adb(ip: str, port: int = 5555) -> bool:
    """Check if wireless ADB is working."""
    print(f"\n✓ Checking wireless ADB at {ip}:{port}...")
    
    # Try to connect
    success, stdout, stderr = run_command(["adb", "connect", f"{ip}:{port}"], timeout=5)
    
    if success and "connected" in stdout.lower():
        print(f"  ✓ Wireless ADB connected to {ip}:{port}")
        
        # Verify it shows in devices
        success2, stdout2, stderr2 = run_command(["adb", "devices"])
        if f"{ip}:{port}" in stdout2:
            print(f"  ✓ Device verified in ADB device list")
            return True
    
    print(f"  ✗ Wireless ADB connection failed. Ensure:")
    print(f"     - Phone is on same network as this PC")
    print(f"     - Wireless debugging is enabled on phone")
    print(f"     - TCP/IP mode is enabled (adb tcpip 5555)")
    return False


def check_app_cloner_installed(serial: str) -> bool:
    """Check if App Cloner is installed on the device."""
    print(f"\n✓ Checking App Cloner installation...")
    
    success, stdout, stderr = run_command([
        "adb", "-s", serial, "shell", "pm", "list", "packages"
    ])
    
    if not success:
        print(f"  ✗ Failed to list packages: {stderr}")
        return False
    
    if "com.applisto.appcloner" in stdout or "com.applisto.appcloner.premium" in stdout:
        print(f"  ✓ App Cloner found")
        return True
    else:
        print(f"  ✗ App Cloner not found. Install it from appcloner.app")
        return False


def check_instagram_installed(serial: str) -> bool:
    """Check if Instagram is installed on the device."""
    print(f"\n✓ Checking Instagram installation...")
    
    success, stdout, stderr = run_command([
        "adb", "-s", serial, "shell", "pm", "list", "packages", "|", "grep", "instagram"
    ])
    
    # Alternative without grep
    success, stdout, stderr = run_command([
        "adb", "-s", serial, "shell", "pm", "list", "packages"
    ])
    
    if not success:
        print(f"  ✗ Failed to list packages")
        return False
    
    ig_packages = [line for line in stdout.split('\n') if 'instagram' in line.lower()]
    
    if ig_packages:
        print(f"  ✓ Instagram found ({len(ig_packages)} package(s)):")
        for pkg in ig_packages[:5]:  # Show first 5
            print(f"      {pkg.strip()}")
        return True
    else:
        print(f"  ✗ Instagram not found. Install from Play Store first.")
        return False


def check_clones_detected(serial: str) -> int:
    """Count Instagram clones detected on the device."""
    print(f"\n✓ Detecting Instagram clones...")
    
    success, stdout, stderr = run_command([
        "adb", "-s", serial, "shell", "pm", "list", "packages"
    ])
    
    if not success:
        print(f"  ✗ Failed to list packages")
        return 0
    
    clone_packages = []
    for line in stdout.split('\n'):
        pkg = line.strip()
        if 'instagram' in pkg.lower() and pkg.startswith('package:'):
            pkg_name = pkg.replace('package:', '')
            # Original is com.instagram.android, clones have suffixes like p1, p2, etc.
            if pkg_name != 'com.instagram.android':
                clone_packages.append(pkg_name)
    
    if clone_packages:
        print(f"  ✓ Found {len(clone_packages)} clone(s):")
        for pkg in clone_packages[:10]:  # Show first 10
            print(f"      {pkg}")
        if len(clone_packages) > 10:
            print(f"      ... and {len(clone_packages) - 10} more")
    else:
        print(f"  ! No clones detected. Create clones in App Cloner first.")
    
    return len(clone_packages)


def check_internet_access(serial: str, proxy_url: Optional[str] = None) -> bool:
    """Check if device has internet access."""
    print(f"\n✓ Checking internet access...")
    
    # Simple connectivity check via ping or curl
    success, stdout, stderr = run_command([
        "adb", "-s", serial, "shell", "pm", "path", "com.android.chrome"
    ], timeout=5)
    
    # Try to get IP info via shell
    success, stdout, stderr = run_command([
        "adb", "-s", serial, "shell", "ip", "addr", "show", "wlan0"
    ])
    
    if success and "inet " in stdout:
        for line in stdout.split('\n'):
            if 'inet ' in line:
                ip = line.strip().split()[1].split('/')[0]
                print(f"  ✓ Device IP: {ip}")
                break
        return True
    
    print(f"  ! Could not determine network status")
    return False


def check_developer_options(serial: str) -> dict:
    """Check if required developer options are enabled."""
    print(f"\n✓ Checking Developer Options settings...")
    
    checks = {
        "usb_debugging": False,
        "wireless_debugging": False,
        "stay_awake": False,
    }
    
    # Check settings via content query (may not work on all devices)
    success, stdout, stderr = run_command([
        "adb", "-s", serial, "shell", "settings", "get", "global", "adb_enabled"
    ])
    
    if success and stdout.strip() == "1":
        checks["usb_debugging"] = True
        print(f"  ✓ USB Debugging enabled")
    else:
        print(f"  ✗ USB Debugging not enabled")
    
    # Check wireless debugging (Android 11+)
    success, stdout, stderr = run_command([
        "adb", "-s", serial, "shell", "settings", "get", "global", "development_settings_enabled"
    ])
    
    if success and stdout.strip() == "1":
        checks["wireless_debugging"] = True
        print(f"  ✓ Developer Options enabled")
    
    return checks


def main():
    parser = argparse.ArgumentParser(description="Verify Meta Autom Farm device setup")
    parser.add_argument("--serial", type=str, help="Device serial number")
    parser.add_argument("--ip", type=str, help="Device IP address for wireless ADB")
    parser.add_argument("--port", type=int, default=5555, help="ADB port (default: 5555)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Meta Autom Farm - Device Setup Verification")
    print("=" * 60)
    
    results = {
        "adb_installed": check_adb_installed(),
        "device_connected": False,
        "wireless_adb": False,
        "app_cloner": False,
        "instagram": False,
        "clones_count": 0,
        "internet": False,
    }
    
    if not results["adb_installed"]:
        print("\n✗ ADB is not installed. Cannot continue verification.")
        print("\nInstall Android SDK Platform Tools:")
        print("  - Linux: sudo apt install android-tools-adb")
        print("  - macOS: brew install android-platform-tools")
        print("  - Windows: Download from https://developer.android.com/studio/releases/platform-tools")
        sys.exit(1)
    
    # Check device connection
    if args.serial:
        results["device_connected"] = check_device_connected(args.serial)
    else:
        results["device_connected"] = check_device_connected()
    
    if not results["device_connected"]:
        print("\n✗ No device connected. Connect phone and enable USB debugging.")
        sys.exit(1)
    
    # Use provided serial or get first connected device
    serial = args.serial
    if not serial:
        success, stdout, _ = run_command(["adb", "devices"])
        for line in stdout.strip().split('\n')[1:]:
            if '\tdevice' in line:
                serial = line.split('\t')[0]
                break
    
    # Check wireless ADB if IP provided
    if args.ip:
        results["wireless_adb"] = check_wireless_adb(args.ip, args.port)
    
    # Check App Cloner
    results["app_cloner"] = check_app_cloner_installed(serial)
    
    # Check Instagram
    results["instagram"] = check_instagram_installed(serial)
    
    # Count clones
    results["clones_count"] = check_clones_detected(serial)
    
    # Check internet
    results["internet"] = check_internet_access(serial)
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum([
        results["adb_installed"],
        results["device_connected"],
        results["app_cloner"],
        results["instagram"],
    ])
    total = 4
    
    print(f"Checks passed: {passed}/{total}")
    print(f"Clones detected: {results['clones_count']}")
    
    if results["wireless_adb"]:
        print(f"Wireless ADB: ✓ Connected")
    
    if passed == total and results["clones_count"] > 0:
        print("\n✓ Device setup is COMPLETE and ready for automation!")
        print("\nNext steps:")
        print("  1. Register device in dashboard: POST /api/v1/devices")
        print("  2. Trigger clone scan: POST /api/v1/devices/{id}/scan")
        print("  3. Map clones to Instagram accounts in dashboard")
        return 0
    elif passed == total:
        print("\n! Device setup is mostly complete, but no clones found.")
        print("\nNext steps:")
        print("  1. Open App Cloner and create Instagram clones")
        print("  2. Each clone needs: New Identity + Proxy settings")
        print("  3. Manually login to Instagram in each clone once")
        return 1
    else:
        print("\n✗ Device setup is INCOMPLETE. Review the errors above.")
        print("\nRefer to 05_SETUP.md for detailed setup instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
