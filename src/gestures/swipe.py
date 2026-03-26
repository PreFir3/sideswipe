"""
Directional Swipe gesture recognition.

Detects left/right hand movements for window navigation.
"""

import numpy as np
from typing import Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class SwipeDirection(Enum):
    """Enumeration of swipe directions."""
    LEFT = "left"
    RIGHT = "right"
    NONE = "none"


@dataclass
class SwipeGesture:
    """Container for swipe gesture detection results."""
    direction: SwipeDirection
    displacement: float  # Total pixels moved
    duration: float  # Time taken (seconds)
    velocity: float  # pixels per frame
    is_confirmed: bool  # Whether gesture meets all criteria
    confidence: float  # 0-1


class SwipeDetector:
    """
    Detects directional swipe gestures (left/right) for window navigation.
    
    Algorithm:
    1. Track starting X position
    2. Monitor X movement across frames
    3. Confirm movement direction and magnitude
    4. Return swipe gesture when thresholds met
    """
    
    def __init__(
        self,
        min_x_movement: float = 100,
        time_window: float = 2.0,
        confirmation_frames: int = 3,
        cooldown: float = 0.5,
        fps: int = 30
    ):
        """
        Initialize swipe detector.
        
        Args:
            min_x_movement: Minimum pixels to move for swipe (default 100)
            time_window: Time window to complete swipe (seconds)
            confirmation_frames: Frames to confirm direction
            cooldown: Seconds between swipes
            fps: Expected frames per second
        """
        self.min_x_movement = min_x_movement
        self.time_window = time_window
        self.confirmation_frames = confirmation_frames
        self.cooldown = cooldown
        self.fps = fps
        
        # State tracking
        self.start_x = None
        self.start_frame = None
        self.current_x = None
        self.frame_count = 0
        self.confirmed_direction = None
        self.direction_confidence_count = 0
        self.last_swipe_time = 0
        self.cooldown_counter = 0
    
    def add_hand_position(
        self,
        x_pos: float,
        frame_index: int = 0
    ) -> SwipeGesture:
        """
        Add hand position and detect swipe.
        
        Args:
            x_pos: Normalized X position (0-1) or pixels
            frame_index: Current frame number (for timing)
            
        Returns:
            SwipeGesture with detection results
        """
        self.frame_count += 1
        self.current_x = x_pos
        
        # Decrement cooldown
        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
        
        # Initialize tracking
        if self.start_x is None:
            self.start_x = x_pos
            self.start_frame = frame_index
            return SwipeGesture(
                direction=SwipeDirection.NONE,
                displacement=0,
                duration=0,
                velocity=0,
                is_confirmed=False,
                confidence=0
            )
        
        # Calculate displacement
        displacement = x_pos - self.start_x
        abs_displacement = abs(displacement)
        duration = (self.frame_count - 1) / self.fps
        velocity = displacement / max(self.frame_count - 1, 1)
        
        # Determine direction
        if displacement < 0:
            current_direction = SwipeDirection.LEFT
        elif displacement > 0:
            current_direction = SwipeDirection.RIGHT
        else:
            current_direction = SwipeDirection.NONE
        
        # Build confidence in direction
        if current_direction == self.confirmed_direction:
            self.direction_confidence_count += 1
        else:
            self.direction_confidence_count = 0
            self.confirmed_direction = current_direction
        
        # Check for completed swipe
        is_confirmed = False
        confidence = 0
        
        if (abs_displacement >= self.min_x_movement and
            duration <= self.time_window and
            self.direction_confidence_count >= self.confirmation_frames and
            self.cooldown_counter == 0):
            
            is_confirmed = True
            confidence = min(abs_displacement / (self.min_x_movement * 2), 1.0)
            
            # Start cooldown
            self.cooldown_counter = int(self.cooldown * self.fps)
            self._reset_tracking()
        
        # Reset if time window exceeded
        elif duration > self.time_window:
            self._reset_tracking()
        
        return SwipeGesture(
            direction=current_direction if is_confirmed else SwipeDirection.NONE,
            displacement=abs_displacement,
            duration=duration,
            velocity=velocity,
            is_confirmed=is_confirmed,
            confidence=confidence
        )
    
    def _reset_tracking(self) -> None:
        """Reset swipe tracking state."""
        self.start_x = None
        self.start_frame = None
        self.frame_count = 0
        self.confirmed_direction = None
        self.direction_confidence_count = 0
    
    def reset(self) -> None:
        """Complete reset of the detector."""
        self._reset_tracking()
        self.cooldown_counter = 0
        self.last_swipe_time = 0
    
    def set_sensitivity(self, min_movement: float) -> None:
        """
        Adjust sensitivity by changing minimum movement threshold.
        
        Args:
            min_movement: New minimum pixels threshold
        """
        self.min_x_movement = min_movement
    
    def set_time_window(self, time_window: float) -> None:
        """
        Adjust time window for swipe completion.
        
        Args:
            time_window: New time window in seconds
        """
        self.time_window = time_window
