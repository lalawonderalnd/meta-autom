"""
Sensor Injection - Synthetic sensor data generation for anti-detection.

Generates realistic accelerometer, gyroscope, and magnetometer data
to fool anti-bot systems that check for sensor presence and patterns.
"""

import math
import random
import time
from datetime import datetime
from typing import Optional


class SensorInjector:
    """
    Synthetic sensor data generator for Android devices.
    
    Generates realistic sensor readings to avoid detection by apps
    that check for sensor presence or analyze movement patterns.
    """
    
    def __init__(self):
        # Baseline noise levels for stationary device
        self.accelerometer_noise = 0.02  # m/s²
        self.gyroscope_noise = 0.001     # rad/s
        self.magnetometer_noise = 0.1    # μT
        
        # Earth's gravity
        self.gravity = 9.80665  # m/s²
        
        # Typical magnetic field strength (varies by location)
        self.mag_field_strength = 50.0  # μT
        
    def generate_accelerometer_reading(
        self,
        is_moving: bool = False,
        movement_type: str = "stationary"
    ) -> dict:
        """
        Generate a realistic accelerometer reading.
        
        Args:
            is_moving: Whether the device is in motion
            movement_type: Type of movement (stationary, walking, shaking, tilting)
            
        Returns:
            Dict with x, y, z acceleration values in m/s²
        """
        if not is_moving or movement_type == "stationary":
            # Stationary device: only gravity + small noise
            # Assume device is lying flat on surface
            base_x = 0.0 + random.gauss(0, self.accelerometer_noise)
            base_y = 0.0 + random.gauss(0, self.accelerometer_noise)
            base_z = self.gravity + random.gauss(0, self.accelerometer_noise)
            
        elif movement_type == "walking":
            # Walking pattern: periodic oscillation
            t = time.time()
            step_frequency = 2.0  # Hz (typical walking cadence)
            amplitude = 0.5  # m/s²
            
            base_x = amplitude * math.sin(2 * math.pi * step_frequency * t)
            base_y = amplitude * math.cos(2 * math.pi * step_frequency * t) * 0.5
            base_z = self.gravity + amplitude * math.sin(2 * math.pi * step_frequency * t) * 0.3
            
            # Add noise
            base_x += random.gauss(0, self.accelerometer_noise)
            base_y += random.gauss(0, self.accelerometer_noise)
            base_z += random.gauss(0, self.accelerometer_noise)
            
        elif movement_type == "tilting":
            # Device being tilted/rotated
            t = time.time()
            tilt_angle = math.sin(t * 0.5) * 30  # ±30 degrees over 4 seconds
            
            # Convert angle to acceleration components
            rad = math.radians(tilt_angle)
            base_x = self.gravity * math.sin(rad)
            base_y = 0.0
            base_z = self.gravity * math.cos(rad)
            
            # Add noise
            base_x += random.gauss(0, self.accelerometer_noise * 2)
            base_y += random.gauss(0, self.accelerometer_noise)
            base_z += random.gauss(0, self.accelerometer_noise * 2)
            
        elif movement_type == "shaking":
            # Rapid back-and-forth movement
            t = time.time()
            shake_frequency = 5.0  # Hz
            amplitude = 2.0  # m/s²
            
            base_x = amplitude * math.sin(2 * math.pi * shake_frequency * t) * random.random()
            base_y = amplitude * math.cos(2 * math.pi * shake_frequency * t) * random.random()
            base_z = self.gravity + amplitude * math.sin(2 * math.pi * shake_frequency * t * 1.3) * random.random()
            
        else:
            # Default to stationary
            base_x = 0.0
            base_y = 0.0
            base_z = self.gravity
        
        return {
            "x": round(base_x, 6),
            "y": round(base_y, 6),
            "z": round(base_z, 6),
            "timestamp": datetime.utcnow().isoformat(),
            "accuracy": "high",
        }
    
    def generate_gyroscope_reading(
        self,
        is_rotating: bool = False,
        rotation_axis: str = "all"
    ) -> dict:
        """
        Generate a realistic gyroscope reading.
        
        Args:
            is_rotating: Whether the device is rotating
            rotation_axis: Which axis is rotating (x, y, z, all)
            
        Returns:
            Dict with x, y, z angular velocity values in rad/s
        """
        if not is_rotating:
            # Stationary device: minimal noise
            base_x = random.gauss(0, self.gyroscope_noise)
            base_y = random.gauss(0, self.gyroscope_noise)
            base_z = random.gauss(0, self.gyroscope_noise)
            
        else:
            # Rotating device
            rotation_speed = 0.5  # rad/s (gentle rotation)
            
            if rotation_axis == "x":
                base_x = rotation_speed + random.gauss(0, self.gyroscope_noise)
                base_y = random.gauss(0, self.gyroscope_noise)
                base_z = random.gauss(0, self.gyroscope_noise)
            elif rotation_axis == "y":
                base_x = random.gauss(0, self.gyroscope_noise)
                base_y = rotation_speed + random.gauss(0, self.gyroscope_noise)
                base_z = random.gauss(0, self.gyroscope_noise)
            elif rotation_axis == "z":
                base_x = random.gauss(0, self.gyroscope_noise)
                base_y = random.gauss(0, self.gyroscope_noise)
                base_z = rotation_speed + random.gauss(0, self.gyroscope_noise)
            else:  # all
                base_x = rotation_speed * 0.7 + random.gauss(0, self.gyroscope_noise)
                base_y = rotation_speed * 0.5 + random.gauss(0, self.gyroscope_noise)
                base_z = rotation_speed * 0.3 + random.gauss(0, self.gyroscope_noise)
        
        return {
            "x": round(base_x, 6),
            "y": round(base_y, 6),
            "z": round(base_z, 6),
            "timestamp": datetime.utcnow().isoformat(),
            "accuracy": "high",
        }
    
    def generate_magnetometer_reading(
        self,
        near_interference: bool = False
    ) -> dict:
        """
        Generate a realistic magnetometer (compass) reading.
        
        Args:
            near_interference: Whether there's magnetic interference nearby
            
        Returns:
            Dict with x, y, z magnetic field values in μT
        """
        if near_interference:
            # Interference causes erratic readings
            base_x = random.gauss(0, self.mag_field_strength * 0.5)
            base_y = random.gauss(0, self.mag_field_strength * 0.5)
            base_z = random.gauss(self.mag_field_strength, self.mag_field_strength * 0.3)
        else:
            # Normal Earth magnetic field
            # Assume device is oriented north-south
            base_x = self.mag_field_strength * 0.6 + random.gauss(0, self.magnetometer_noise)
            base_y = self.mag_field_strength * 0.3 + random.gauss(0, self.magnetometer_noise)
            base_z = self.mag_field_strength * 0.4 + random.gauss(0, self.magnetometer_noise)
        
        return {
            "x": round(base_x, 3),
            "y": round(base_y, 3),
            "z": round(base_z, 3),
            "timestamp": datetime.utcnow().isoformat(),
            "accuracy": "medium" if near_interference else "high",
        }
    
    def generate_sensor_sequence(
        self,
        duration_seconds: float = 5.0,
        sample_rate_hz: int = 60,
        movement_pattern: str = "natural_idle"
    ) -> list[dict]:
        """
        Generate a sequence of sensor readings over time.
        
        Args:
            duration_seconds: How long the sequence should be
            sample_rate_hz: Samples per second
            movement_pattern: Pattern type (natural_idle, picked_up, walking, pocket)
            
        Returns:
            List of sensor reading dicts
        """
        readings = []
        total_samples = int(duration_seconds * sample_rate_hz)
        interval = 1.0 / sample_rate_hz
        
        start_time = time.time()
        
        for i in range(total_samples):
            elapsed = i * interval
            progress = elapsed / duration_seconds
            
            if movement_pattern == "natural_idle":
                # Device sitting on table with minor vibrations
                is_moving = random.random() < 0.1  # 10% chance of micro-movement
                accel = self.generate_accelerometer_reading(is_moving, "stationary")
                gyro = self.generate_gyroscope_reading(False)
                mag = self.generate_magnetometer_reading(False)
                
            elif movement_pattern == "picked_up":
                # Device being picked up
                if progress < 0.2:
                    # Initial lift
                    accel = self.generate_accelerometer_reading(True, "tilting")
                    gyro = self.generate_gyroscope_reading(True, "all")
                elif progress < 0.5:
                    # Holding steady
                    accel = self.generate_accelerometer_reading(False, "stationary")
                    gyro = self.generate_gyroscope_reading(False)
                else:
                    # Putting down
                    accel = self.generate_accelerometer_reading(True, "tilting")
                    gyro = self.generate_gyroscope_reading(True, "x")
                mag = self.generate_magnetometer_reading(False)
                
            elif movement_pattern == "walking":
                # Device being carried while walking
                accel = self.generate_accelerometer_reading(True, "walking")
                gyro = self.generate_gyroscope_reading(True, "all")
                mag = self.generate_magnetometer_reading(random.random() < 0.2)
                
            elif movement_pattern == "pocket":
                # Device in pocket - more chaotic movement
                if progress < 0.3:
                    accel = self.generate_accelerometer_reading(True, "walking")
                    gyro = self.generate_gyroscope_reading(True, "all")
                elif progress < 0.7:
                    # Sitting in pocket
                    accel = self.generate_accelerometer_reading(False, "stationary")
                    gyro = self.generate_gyroscope_reading(False)
                else:
                    # Being taken out
                    accel = self.generate_accelerometer_reading(True, "tilting")
                    gyro = self.generate_gyroscope_reading(True, "all")
                mag = self.generate_magnetometer_reading(True)  # Pocket interference
                
            else:
                # Default
                accel = self.generate_accelerometer_reading()
                gyro = self.generate_gyroscope_reading()
                mag = self.generate_magnetometer_reading()
            
            readings.append({
                "accelerometer": accel,
                "gyroscope": gyro,
                "magnetometer": mag,
                "sequence_time": elapsed,
            })
        
        return readings
    
    def inject_via_adb(self, device_serial: str, pattern: str = "natural_idle"):
        """
        Inject sensor data via ADB (requires root or special permissions).
        
        Note: This is a placeholder for actual implementation.
        Real sensor injection requires:
        - Root access OR
        - Custom ROM with sensor injection support OR
        - Hardware-level emulation
        
        Args:
            device_serial: ADB device serial
            pattern: Movement pattern to simulate
        """
        # Generate sensor sequence
        readings = self.generate_sensor_sequence(
            duration_seconds=10.0,
            sample_rate_hz=30,
            movement_pattern=pattern
        )
        
        # In a real implementation, this would use ADB to inject the readings
        # Example (pseudo-code):
        # for reading in readings:
        #     adb_command = f"adb -s {device_serial} shell service call sensorservice ..."
        #     execute adb_command
        
        return {
            "device_serial": device_serial,
            "pattern": pattern,
            "readings_generated": len(readings),
            "note": "Actual injection requires root/custom ROM",
        }
    
    def validate_sensor_presence(self, sensor_data: list[dict]) -> dict:
        """
        Validate that sensor data looks realistic (for testing).
        
        Args:
            sensor_data: List of sensor readings
            
        Returns:
            Validation results
        """
        if not sensor_data:
            return {"valid": False, "reason": "No data provided"}
        
        # Check for reasonable ranges
        for reading in sensor_data:
            accel = reading.get("accelerometer", {})
            gyro = reading.get("gyroscope", {})
            mag = reading.get("magnetometer", {})
            
            # Accelerometer should be around 9.8 m/s² when stationary
            total_accel = math.sqrt(
                accel.get("x", 0)**2 + 
                accel.get("y", 0)**2 + 
                accel.get("z", 0)**2
            )
            
            if abs(total_accel - self.gravity) > 2.0:
                return {
                    "valid": False,
                    "reason": f"Unrealistic acceleration: {total_accel:.2f} m/s²",
                }
            
            # Gyroscope should be near zero when not rotating
            total_gyro = math.sqrt(
                gyro.get("x", 0)**2 + 
                gyro.get("y", 0)**2 + 
                gyro.get("z", 0)**2
            )
            
            if total_gyro > 1.0:  # More than ~57 degrees/sec
                return {
                    "valid": False,
                    "reason": f"Excessive rotation: {total_gyro:.2f} rad/s",
                }
        
        return {
            "valid": True,
            "readings_checked": len(sensor_data),
            "message": "Sensor data appears realistic",
        }
