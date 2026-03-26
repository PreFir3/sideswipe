"""
Head Tilt gesture recognition.

Detects head tilt (up/down) for scrolling control.
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class ScrollDirection(Enum):
    """Enumeration of scroll directions."""
    UP = "up"
    DOWN = "down"
    NONE = "none"


@dataclass
class HeadTiltGesture:
    """Container for head tilt detection results."""
    scroll_direction: ScrollDirection
    head_angle: float  # Degrees from neutral
    scroll_speed: float  # Pixels per frame
    is_active: bool  # Whether scrolling should be triggered
    confidence: float  # 0-1


class HeadTiltDetector:
    """
    Detects head tilt (up/down) for scrolling.
    
    Algorithm:
    1. Calibrate neutral head position on startup
    2. Track head pitch angle deviation
    3. Detect angle threshold crossing
    4. Map angle to scroll speed
    5. Return scroll direction and speed
    
    Requires ML-trained head model for individual calibration.
    """
    
    def __init__(
        self,
        angle_threshold: float = 15.0,
        scroll_speed_max: float = 20.0,
        scroll_acceleration: float = 1.2,
        reset_timeout: float = 2.0,
        smoothing_frames: int = 5,
        fps: int = 30
    ):
        """
        Initialize head tilt detector.
        
        Args:
            angle_threshold: Angle in degrees to trigger scroll
            scroll_speed_max: Maximum scroll pixels per frame
            scroll_acceleration: Multiplier for scroll speed with angle
            reset_timeout: Seconds of no head movement before reset
            smoothing_frames: Frames to smooth angle calculations
            fps: Expected frames per second
        """
        self.angle_threshold = angle_threshold
        self.scroll_speed_max = scroll_speed_max
        self.scroll_acceleration = scroll_acceleration
        self.reset_timeout = reset_timeout
        self.smoothing_frames = smoothing_frames
        self.fps = fps
        
        # State tracking
        self.neutral_angle = 0.0  # Calibrated neutral pitch
        self.frame_count = 0
        self.reset_counter = 0
        self.angle_history = []
    
    def calibrate_neutral_position(self, pitch_angle: float) -> None:
        """
        Calibrate neutral head position.
        
        Should be called once at startup while user looks straight ahead.
        
        Args:
            pitch_angle: Current head pitch angle (degrees)
        """
        self.neutral_angle = pitch_angle
        self.reset_counter = int(self.reset_timeout * self.fps)
    
    def add_head_angle(self, pitch_angle: float) -> HeadTiltGesture:
        """
        Add head pitch angle measurement from face detection.
        
        Args:
            pitch_angle: Current head pitch angle in degrees
            (negative = tilted up, positive = tilted down)
            
        Returns:
            HeadTiltGesture with scroll direction and speed
        """
        self.frame_count += 1
        
        # Calculate deviation from neutral
        angle_deviation = pitch_angle - self.neutral_angle
        
        # Add to history for smoothing
        self.angle_history.append(angle_deviation)
        if len(self.angle_history) > self.smoothing_frames:
            self.angle_history.pop(0)
        
        # Calculate smoothed angle
        smoothed_angle = np.mean(self.angle_history)
        
        # Determine scroll direction
        scroll_direction = ScrollDirection.NONE
        is_active = False
        scroll_speed = 0.0
        confidence = 0.0
        
        if abs(smoothed_angle) >= self.angle_threshold:
            # Threshold crossed - start scrolling
            is_active = True
            self.reset_counter = int(self.reset_timeout * self.fps)
            
            if smoothed_angle < 0:
                # Head tilted up
                scroll_direction = ScrollDirection.UP
            else:
                # Head tilted down
                scroll_direction = ScrollDirection.DOWN
            
            # Calculate scroll speed proportional to angle
            # Angle beyond threshold maps to scroll speed
            excess_angle = abs(smoothed_angle) - self.angle_threshold
            speed_factor = min(excess_angle / (self.angle_threshold * 2), 1.0)
            scroll_speed = speed_factor * self.scroll_speed_max * self.scroll_acceleration
            confidence = min(speed_factor, 1.0)
        else:
            # Below threshold - decrement reset counter
            if self.reset_counter > 0:
                self.reset_counter -= 1
            else:
                # Reset to neutral
                self.neutral_angle = pitch_angle
        
        return HeadTiltGesture(
            scroll_direction=scroll_direction,
            head_angle=smoothed_angle,
            scroll_speed=scroll_speed,
            is_active=is_active,
            confidence=confidence
        )
    
    def reset(self) -> None:
        """Reset the detector."""
        self.frame_count = 0
        self.reset_counter = 0
        self.angle_history = []
    
    def set_sensitivity(self, angle_threshold: float) -> None:
        """
        Adjust sensitivity by changing angle threshold.
        
        Args:
            angle_threshold: New angle threshold in degrees
        """
        self.angle_threshold = angle_threshold
    
    def set_max_scroll_speed(self, speed: float) -> None:
        """
        Adjust maximum scroll speed.
        
        Args:
            speed: New max speed in pixels per frame
        """
        self.scroll_speed_max = speed
    
    def get_neutral_angle(self) -> float:
        """Get calibrated neutral angle."""
        return self.neutral_angle
    
    def set_neutral_angle(self, angle: float) -> None:
        """Set neutral angle manually."""
        self.neutral_angle = angle
