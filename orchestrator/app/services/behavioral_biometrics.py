"""
Behavioral Biometrics Engine for Meta Autom Farm.

Generates human-like touch patterns, scroll behaviors, and interaction timing
to avoid detection by Instagram's anti-automation systems.
"""

import random
import math
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class InteractionType(Enum):
    """Types of interactions."""
    TAP = "tap"
    SCROLL = "scroll"
    SWIPE = "swipe"
    LONG_PRESS = "long_press"
    PINCH = "pinch"
    TYPE = "type"


@dataclass
class TouchPoint:
    """A single point in a touch trajectory."""
    x: float
    y: float
    pressure: float  # 0.0 to 1.0
    timestamp: float  # milliseconds since start
    size: float  # contact area


@dataclass
class Gesture:
    """A complete gesture with multiple touch points."""
    interaction_type: InteractionType
    points: List[TouchPoint]
    duration_ms: int
    start_x: float
    start_y: float
    end_x: Optional[float] = None
    end_y: Optional[float] = None


class HumanizationProfile:
    """
    User-specific behavioral profile.
    
    Each Instagram account should have its own profile that persists
    across sessions to maintain consistent behavioral fingerprints.
    """
    
    def __init__(
        self,
        user_id: str,
        age_range: str = "25-34",
        handedness: str = "right",
        clumsiness: float = 0.02,
        speed_variance: float = 0.15,
        attention_span: str = "medium"
    ):
        self.user_id = user_id
        self.age_range = age_range
        self.handedness = handedness
        self.clumsiness = clumsiness  # Probability of misclicks
        self.speed_variance = speed_variance  # Variation in movement speed
        self.attention_span = attention_span  # short, medium, long
        
        # Seed random with user_id for reproducibility
        self._rng = random.Random(hash(user_id) % (2**32))
        
        # Generate persistent traits
        self.base_speed = self._generate_base_speed()
        self.pressure_profile = self._generate_pressure_profile()
        self.scroll_pattern = self._generate_scroll_pattern()
        
    def _generate_base_speed(self) -> float:
        """Generate base movement speed based on profile."""
        # Younger users tend to be faster
        speed_map = {
            "18-24": 1.2,
            "25-34": 1.0,
            "35-44": 0.9,
            "45-54": 0.8,
            "55+": 0.7
        }
        base = speed_map.get(self.age_range, 1.0)
        
        # Handedness affects speed slightly
        if self.handedness == "left":
            base *= 0.95
            
        return base * (0.8 + self._rng.random() * 0.4)  # ±20% variance
    
    def _generate_pressure_profile(self) -> Dict[str, float]:
        """Generate pressure characteristics."""
        return {
            "tap": 0.6 + self._rng.random() * 0.3,
            "scroll": 0.4 + self._rng.random() * 0.2,
            "long_press": 0.7 + self._rng.random() * 0.2,
            "variance": 0.05 + self._rng.random() * 0.1
        }
    
    def _generate_scroll_pattern(self) -> Dict[str, Any]:
        """Generate scroll behavior pattern."""
        return {
            "avg_flings_per_session": self._rng.randint(20, 60),
            "avg_scroll_distance": 100 + self._rng.random() * 200,
            "pause_probability": 0.1 + self._rng.random() * 0.2,
            "read_time_factor": 1.0 + self._rng.random() * 0.5,
            "backtrack_probability": 0.05 + self._rng.random() * 0.1
        }


class BehavioralBiometricsEngine:
    """
    Core engine for generating human-like interactions.
    
    Usage:
        engine = BehavioralBiometricsEngine()
        profile = HumanizationProfile("user_123")
        
        # Generate a tap gesture
        gesture = engine.generate_tap(profile, x=100, y=200)
        
        # Generate a scroll gesture
        gesture = engine.generate_scroll(profile, start_x=500, start_y=800, distance=-300)
        
        # Execute via ADB
        for point in gesture.points:
            adb_command = f"input swipe {point.x} {point.y} {point.x} {point.y} {int(point.timestamp)}"
    """
    
    def __init__(self):
        self.profiles: Dict[str, HumanizationProfile] = {}
    
    def get_or_create_profile(self, user_id: str, **kwargs) -> HumanizationProfile:
        """Get existing profile or create new one."""
        if user_id not in self.profiles:
            self.profiles[user_id] = HumanizationProfile(user_id, **kwargs)
        return self.profiles[user_id]
    
    def generate_tap(
        self,
        profile: HumanizationProfile,
        x: float,
        y: float,
        screen_width: int = 1080,
        screen_height: int = 2400
    ) -> Gesture:
        """
        Generate a human-like tap gesture.
        
        Includes:
        - Approach trajectory (finger doesn't appear instantly)
        - Pressure curve (press and release)
        - Micro-jitter (humans aren't perfectly steady)
        - Occasional misclicks (based on clumsiness)
        """
        rng = profile._rng
        points = []
        start_time = 0
        
        # Apply clumsiness - possibly miss the target
        if rng.random() < profile.clumsiness:
            offset_x = rng.gauss(0, 20)
            offset_y = rng.gauss(0, 20)
            x += offset_x
            y += offset_y
        
        # Constrain to screen
        x = max(50, min(screen_width - 50, x))
        y = max(50, min(screen_height - 50, y))
        
        # Approach phase - finger comes from above/below
        approach_distance = 50 + rng.random() * 100
        approach_angle = rng.uniform(math.pi, 2 * math.pi)  # From top half
        start_x = x + math.cos(approach_angle) * approach_distance
        start_y = y + math.sin(approach_angle) * approach_distance
        
        # Duration based on profile
        base_duration = 150 / profile.base_speed
        duration = int(base_duration * (1 + rng.gauss(0, profile.speed_variance)))
        
        # Generate approach points
        num_points = max(3, int(duration / 16))  # ~60fps
        for i in range(num_points):
            t = i / num_points
            px = start_x + (x - start_x) * t
            py = start_y + (y - start_y) * t
            
            # Add micro-jitter
            px += rng.gauss(0, 2)
            py += rng.gauss(0, 2)
            
            # Pressure increases during approach
            pressure = profile.pressure_profile["tap"] * (0.3 + 0.7 * t)
            pressure += rng.gauss(0, profile.pressure_profile["variance"])
            pressure = max(0.1, min(1.0, pressure))
            
            points.append(TouchPoint(
                x=round(px, 1),
                y=round(py, 1),
                pressure=round(pressure, 3),
                timestamp=start_time + (t * duration),
                size=8 + rng.random() * 4  # Contact area in mm²
            ))
        
        # Hold briefly
        hold_duration = 50 + rng.random() * 100
        points.append(TouchPoint(
            x=x,
            y=y,
            pressure=profile.pressure_profile["tap"],
            timestamp=points[-1].timestamp + hold_duration,
            size=10 + rng.random() * 3
        ))
        
        # Release phase
        release_duration = 50 + rng.random() * 50
        for i in range(3):
            t = (i + 1) / 3
            points.append(TouchPoint(
                x=x + rng.gauss(0, 1),
                y=y + rng.gauss(0, 1),
                pressure=profile.pressure_profile["tap"] * (1 - t),
                timestamp=points[-1].timestamp + (t * release_duration),
                size=max(5, 12 * (1 - t))
            ))
        
        return Gesture(
            interaction_type=InteractionType.TAP,
            points=points,
            duration_ms=int(points[-1].timestamp),
            start_x=start_x,
            start_y=start_y,
            end_x=x,
            end_y=y
        )
    
    def generate_scroll(
        self,
        profile: HumanizationProfile,
        start_x: float,
        start_y: float,
        distance: float,
        screen_width: int = 1080,
        screen_height: int = 2400
    ) -> Gesture:
        """
        Generate a human-like scroll gesture.
        
        Includes:
        - Variable speed (acceleration and deceleration)
        - Curved trajectory (not perfectly straight)
        - Pressure variation
        - Natural stopping point
        """
        rng = profile._rng
        points = []
        
        # Scroll characteristics
        is_down = distance > 0
        actual_distance = abs(distance)
        
        # Duration based on distance and profile
        base_duration = (actual_distance / 500) * 300 / profile.base_speed
        duration = int(base_duration * (1 + rng.gauss(0, profile.speed_variance)))
        
        # End position
        end_y = start_y + distance
        end_y = max(100, min(screen_height - 100, end_y))
        
        # Generate scroll path with easing
        num_points = max(5, int(duration / 16))
        
        for i in range(num_points + 1):
            t = i / num_points
            
            # Easing function (ease-out for natural feel)
            eased_t = 1 - math.pow(1 - t, 3)
            
            # Position with curve
            current_y = start_y + (end_y - start_y) * eased_t
            
            # Add slight horizontal wobble (humans don't scroll perfectly straight)
            wobble = math.sin(t * math.pi * 4) * 5 * rng.random()
            current_x = start_x + wobble
            
            # Speed varies - faster in middle, slower at edges
            speed_factor = 1 - abs(t - 0.5) * 0.3
            current_pressure = profile.pressure_profile["scroll"] * speed_factor
            current_pressure += rng.gauss(0, profile.pressure_profile["variance"])
            current_pressure = max(0.2, min(0.8, current_pressure))
            
            points.append(TouchPoint(
                x=round(current_x, 1),
                y=round(current_y, 1),
                pressure=round(current_pressure, 3),
                timestamp=int(t * duration),
                size=9 + rng.random() * 3
            ))
        
        return Gesture(
            interaction_type=InteractionType.SCROLL,
            points=points,
            duration_ms=duration,
            start_x=start_x,
            start_y=start_y,
            end_x=start_x,
            end_y=end_y
        )
    
    def generate_reading_pause(self, profile: HumanizationProfile) -> float:
        """
        Generate a realistic reading pause duration in milliseconds.
        
        Humans pause to read content before interacting.
        """
        rng = profile._rng
        
        # Base pause depends on attention span
        pause_map = {
            "short": 500,
            "medium": 1500,
            "long": 3000
        }
        base_pause = pause_map.get(profile.attention_span, 1500)
        
        # Add variance
        pause = base_pause * (0.5 + rng.random() * 1.5)
        
        # Occasional very long pauses (distracted moments)
        if rng.random() < 0.1:
            pause *= 3
            
        return int(pause)
    
    def generate_session_pattern(
        self,
        profile: HumanizationProfile,
        session_duration_minutes: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate a complete session pattern of interactions.
        
        Returns a sequence of actions with timing that mimics human behavior.
        """
        rng = profile._rng
        actions = []
        
        # Average flings per session from profile
        num_scrolls = profile.scroll_pattern["avg_flings_per_session"]
        
        # Distribute scrolls across session
        for i in range(num_scrolls):
            # Reading pause before scroll
            pause = self.generate_reading_pause(profile)
            actions.append({
                "type": "pause",
                "duration_ms": pause
            })
            
            # Occasional backtrack (scroll up after scrolling down)
            if rng.random() < profile.scroll_pattern["backtrack_probability"]:
                actions.append({
                    "type": "scroll",
                    "distance": rng.randint(50, 150),  # Scroll up
                    "start_x": rng.randint(400, 700),
                    "start_y": rng.randint(1000, 1800)
                })
            
            # Main scroll
            scroll_distance = rng.randint(200, 500) * (-1 if rng.random() > 0.3 else 1)
            actions.append({
                "type": "scroll",
                "distance": scroll_distance,
                "start_x": rng.randint(400, 700),
                "start_y": rng.randint(800, 2000)
            })
            
            # Occasional tap (liking, commenting, etc.)
            if rng.random() < 0.15:  # 15% chance per scroll
                actions.append({
                    "type": "tap",
                    "x": rng.randint(200, 900),
                    "y": rng.randint(400, 1600)
                })
        
        return actions
    
    def gesture_to_adb_commands(self, gesture: Gesture) -> List[str]:
        """
        Convert a gesture to ADB input commands.
        
        For taps: use `input tap x y`
        For scrolls: use `input swipe x1 y1 x2 y2 duration`
        """
        commands = []
        
        if gesture.interaction_type == InteractionType.TAP:
            # Simple tap
            final_point = gesture.points[-3]  # Before release
            commands.append(f"input tap {int(final_point.x)} {int(final_point.y)}")
            
        elif gesture.interaction_type == InteractionType.SCROLL:
            # Swipe with duration
            start = gesture.points[0]
            end = gesture.points[-1]
            duration = gesture.duration_ms
            commands.append(
                f"input swipe {int(start.x)} {int(start.y)} "
                f"{int(end.x)} {int(end.y)} {duration}"
            )
        
        return commands
    
    def add_human_delay(self, base_delay_ms: int, profile: HumanizationProfile) -> int:
        """
        Add human-like variance to a delay.
        
        Humans are never perfectly consistent in their timing.
        """
        rng = profile._rng
        variance = profile.speed_variance
        
        # Apply gaussian variance
        adjusted = base_delay_ms * (1 + rng.gauss(0, variance))
        
        # Ensure positive and reasonable
        return max(100, int(adjusted))


# Convenience functions for direct use
def generate_human_tap(
    x: float,
    y: float,
    user_id: str = "default",
    **profile_kwargs
) -> List[str]:
    """Generate ADB commands for a human-like tap."""
    engine = BehavioralBiometricsEngine()
    profile = engine.get_or_create_profile(user_id, **profile_kwargs)
    gesture = engine.generate_tap(profile, x, y)
    return engine.gesture_to_adb_commands(gesture)


def generate_human_scroll(
    start_x: float,
    start_y: float,
    distance: float,
    user_id: str = "default",
    **profile_kwargs
) -> List[str]:
    """Generate ADB commands for a human-like scroll."""
    engine = BehavioralBiometricsEngine()
    profile = engine.get_or_create_profile(user_id, **profile_kwargs)
    gesture = engine.generate_scroll(profile, start_x, start_y, distance)
    return engine.gesture_to_adb_commands(gesture)
