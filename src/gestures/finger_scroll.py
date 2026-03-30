"""
Finger scroll gesture detection.

Detects finger movement (middle finger) for vertical scrolling.
"""

import numpy as np
from collections import deque
from dataclasses import dataclass
from enum import Enum

from config import FINGER_SCROLL


class ScrollDirection(Enum):
    """Scroll directions."""
    UP = "up"
    DOWN = "down"
    NONE = "none"


@dataclass
class FingerScrollGesture:
    """Container for finger scroll gesture."""
    direction: ScrollDirection = ScrollDirection.NONE
    distance: float = 0.0
    velocity: float = 0.0
    is_active: bool = False
    confidence: float = 0.0


class FingerScrollDetector:
    """
    Detects vertical finger scroll gestures.
    
    Uses middle finger Y position to detect up/down scrolling:
    - If finger moves up (Y decreases): scroll up
    - If finger moves down (Y increases): scroll down
    """
    
    # Hand landmark indices
    MIDDLE_TIP = 12
    MIDDLE_PIP = 10
    
    def __init__(
        self,
        min_movement: float = FINGER_SCROLL["min_movement"],
        smoothing_frames: int = FINGER_SCROLL["smoothing_frames"],
        activation_frames: int = FINGER_SCROLL["activation_frames"],
    ):
        """
        Initialize finger scroll detector.
        
        Args:
            min_movement: Minimum vertical movement to register (0-1 normalized)
            smoothing_frames: Frames to smooth movement
        """
        self.min_movement = min_movement
        self.smoothing_frames = smoothing_frames
        self.activation_frames = activation_frames
        self.position_history = deque(maxlen=smoothing_frames)
        self.gesture = FingerScrollGesture()
    
    def add_finger_position(self, y_pos: float) -> FingerScrollGesture:
        """
        Add finger Y position and detect scroll.
        
        Args:
            y_pos: Normalized Y position (0-1)
            
        Returns:
            FingerScrollGesture with scroll direction and velocity
        """
        # Add position to history
        self.position_history.append(y_pos)

        # Need a short stable run before detecting movement
        if len(self.position_history) < self.activation_frames:
            self.gesture.direction = ScrollDirection.NONE
            self.gesture.is_active = False
            return self.gesture

        positions = list(self.position_history)
        window_size = min(3, len(positions) // 2)
        if window_size < 2:
            self.gesture.direction = ScrollDirection.NONE
            self.gesture.is_active = False
            return self.gesture

        recent_avg = sum(positions[-window_size:]) / window_size
        previous_avg = sum(positions[-(window_size * 2):-window_size]) / window_size
        movement = recent_avg - previous_avg
        velocity = abs(movement)

        # Determine direction
        if movement < -self.min_movement:
            self.gesture.direction = ScrollDirection.UP
            self.gesture.distance = abs(movement)
            self.gesture.velocity = velocity
            self.gesture.is_active = True
            self.gesture.confidence = min(velocity / self.min_movement, 1.0)
        elif movement > self.min_movement:
            self.gesture.direction = ScrollDirection.DOWN
            self.gesture.distance = abs(movement)
            self.gesture.velocity = velocity
            self.gesture.is_active = True
            self.gesture.confidence = min(velocity / self.min_movement, 1.0)
        else:
            self.gesture.direction = ScrollDirection.NONE
            self.gesture.is_active = False
            self.gesture.confidence = 0.0
        
        return self.gesture
    
    def detect_from_landmarks(self, landmarks: np.ndarray) -> FingerScrollGesture:
        """
        Detect scroll gesture from hand landmarks.
        
        Args:
            landmarks: Hand landmarks (21 x 2, normalized 0-1)
            
        Returns:
            FingerScrollGesture
        """
        if landmarks.size == 0 or len(landmarks) < 13:
            return FingerScrollGesture()
        
        # Get middle finger tip Y position
        middle_tip_y = landmarks[self.MIDDLE_TIP][1]
        
        return self.add_finger_position(middle_tip_y)
    
    def reset(self):
        """Reset gesture state."""
        self.position_history = []
        self.gesture = FingerScrollGesture()
