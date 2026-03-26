"""
Frame buffer and temporal filtering utilities for gesture stability.

Provides smoothing and multi-frame averaging to prevent false triggers.
"""

from collections import deque
from typing import List, Tuple, Optional, Any
import numpy as np


class FrameBuffer:
    """
    Circular buffer for storing recent frame data for temporal analysis.
    
    Used for smoothing hand landmarks, head positions, and other tracked data
    across multiple frames to avoid sensitivity to single-frame noise.
    """
    
    def __init__(self, max_size: int = 10):
        """
        Initialize the frame buffer.
        
        Args:
            max_size: Maximum number of frames to store
        """
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
    
    def append(self, data: Any) -> None:
        """Add data to the buffer."""
        self.buffer.append(data)
    
    def get_all(self) -> List[Any]:
        """Get all data in the buffer."""
        return list(self.buffer)
    
    def get_latest(self, n: int = 1) -> List[Any]:
        """Get the last n frames."""
        return list(self.buffer)[-n:]
    
    def is_full(self) -> bool:
        """Check if buffer is at max capacity."""
        return len(self.buffer) == self.max_size
    
    def size(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)
    
    def clear(self) -> None:
        """Clear all data."""
        self.buffer.clear()


class LandmarkSmoother:
    """
    Smooths hand/face landmarks across frames using exponential moving average.
    
    Reduces jitter from MediaPipe detection while preserving real movement.
    """
    
    def __init__(self, smoothing_factor: float = 0.7):
        """
        Initialize the smoother.
        
        Args:
            smoothing_factor: 0-1, higher = more smoothing (default 0.7)
        """
        self.smoothing_factor = smoothing_factor
        self.last_landmarks = None
    
    def smooth(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Apply exponential moving average smoothing to landmarks.
        
        Args:
            landmarks: Array of landmark positions (N x 2 or N x 3)
            
        Returns:
            Smoothed landmark array
        """
        if self.last_landmarks is None:
            self.last_landmarks = landmarks.copy()
            return landmarks
        
        # Apply EMA: new = factor * current + (1 - factor) * previous
        smoothed = (
            self.smoothing_factor * landmarks +
            (1 - self.smoothing_factor) * self.last_landmarks
        )
        
        self.last_landmarks = smoothed.copy()
        return smoothed
    
    def reset(self) -> None:
        """Reset smoothing state."""
        self.last_landmarks = None


class MotionDetector:
    """
    Detects motion patterns in tracked points across frames.
    
    Calculates velocity, acceleration, and direction of movement.
    """
    
    def __init__(self, buffer_size: int = 5):
        """
        Initialize motion detector.
        
        Args:
            buffer_size: Frames to keep for motion analysis
        """
        self.position_buffer = FrameBuffer(buffer_size)
    
    def add_position(self, x: float, y: float) -> None:
        """Add a position (x, y) to the buffer."""
        self.position_buffer.append((x, y))
    
    def get_velocity(self) -> Optional[Tuple[float, float]]:
        """
        Calculate velocity (px/frame) in x and y directions.
        
        Returns:
            Tuple of (velocity_x, velocity_y) or None if insufficient data
        """
        if self.position_buffer.size() < 2:
            return None
        
        positions = self.position_buffer.get_all()
        last_pos = positions[-1]
        prev_pos = positions[-2]
        
        vel_x = last_pos[0] - prev_pos[0]
        vel_y = last_pos[1] - prev_pos[1]
        
        return (vel_x, vel_y)
    
    def get_acceleration(self) -> Optional[Tuple[float, float]]:
        """
        Calculate acceleration (px/frame²) in x and y directions.
        
        Returns:
            Tuple of (accel_x, accel_y) or None if insufficient data
        """
        if self.position_buffer.size() < 3:
            return None
        
        positions = self.position_buffer.get_all()
        vel_now = (positions[-1][0] - positions[-2][0],
                   positions[-1][1] - positions[-2][1])
        vel_prev = (positions[-2][0] - positions[-3][0],
                    positions[-2][1] - positions[-3][1])
        
        accel_x = vel_now[0] - vel_prev[0]
        accel_y = vel_now[1] - vel_prev[1]
        
        return (accel_x, accel_y)
    
    def get_total_displacement(self) -> Optional[float]:
        """
        Calculate total displacement from first to last position.
        
        Returns:
            Euclidean distance or None if insufficient data
        """
        if self.position_buffer.size() < 2:
            return None
        
        positions = self.position_buffer.get_all()
        first_pos = positions[0]
        last_pos = positions[-1]
        
        dx = last_pos[0] - first_pos[0]
        dy = last_pos[1] - first_pos[1]
        
        return np.sqrt(dx**2 + dy**2)
    
    def get_direction(self) -> Optional[str]:
        """
        Determine primary direction of movement.
        
        Returns:
            Direction string: "left", "right", "up", "down", or None
        """
        displacement = self.get_total_displacement()
        if displacement is None or displacement < 5:
            return None
        
        positions = self.position_buffer.get_all()
        dx = positions[-1][0] - positions[0][0]
        dy = positions[-1][1] - positions[0][1]
        
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        if abs_dx > abs_dy:
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"
    
    def reset(self) -> None:
        """Reset the motion detector."""
        self.position_buffer.clear()


class ThresholdValidator:
    """
    Validates that detected gestures meet minimum requirements.
    
    Ensures gestures are intentional and not accidental noise.
    """
    
    @staticmethod
    def validate_movement(
        displacement: float,
        min_displacement: float,
        velocity: float,
        min_velocity: float
    ) -> bool:
        """
        Validate a movement meets displacement and velocity thresholds.
        
        Args:
            displacement: Total distance moved (pixels)
            min_displacement: Minimum required (pixels)
            velocity: Current movement speed (px/frame)
            min_velocity: Minimum required (px/frame)
            
        Returns:
            True if both thresholds met
        """
        return displacement >= min_displacement and velocity >= min_velocity
    
    @staticmethod
    def validate_count_stability(
        values: List[int],
        confidence_threshold: float = 0.8
    ) -> Optional[int]:
        """
        Validate a series of counts (e.g., finger counts) for stability.
        
        Args:
            values: List of count values
            confidence_threshold: 0-1, how consistent values must be
            
        Returns:
            Most common value if confident enough, else None
        """
        if not values:
            return None
        
        # Find most common value
        from collections import Counter
        counts = Counter(values)
        most_common_value, frequency = counts.most_common(1)[0]
        
        # Check confidence
        confidence = frequency / len(values)
        
        return most_common_value if confidence >= confidence_threshold else None
    
    @staticmethod
    def validate_angle(
        angle: float,
        threshold: float
    ) -> bool:
        """
        Validate angle meets threshold.
        
        Args:
            angle: Angle in degrees (absolute value)
            threshold: Maximum allowed angle
            
        Returns:
            True if within threshold
        """
        return abs(angle) >= threshold


class GestureStateTracker:
    """
    Tracks the state of gestures across frames.
    
    Helps distinguish between gesture start, ongoing, and end states.
    """
    
    def __init__(self):
        """Initialize state tracker."""
        self.states = {}  # gesture_name -> state_data
    
    def set_state(self, gesture: str, state: str, **kwargs) -> None:
        """
        Set state for a gesture.
        
        Args:
            gesture: Name of gesture
            state: State (e.g., "idle", "in_progress", "detected")
            **kwargs: Additional state data
        """
        self.states[gesture] = {
            "state": state,
            "frame_count": self.states.get(gesture, {}).get("frame_count", 0) + 1,
            **kwargs
        }
    
    def get_state(self, gesture: str) -> Optional[dict]:
        """Get state for a gesture."""
        return self.states.get(gesture)
    
    def reset_state(self, gesture: str) -> None:
        """Reset state for a gesture."""
        if gesture in self.states:
            self.states[gesture] = {"state": "idle", "frame_count": 0}
    
    def reset_all(self) -> None:
        """Reset all states."""
        for gesture in self.states:
            self.states[gesture] = {"state": "idle", "frame_count": 0}
