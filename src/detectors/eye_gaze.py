"""
Eye gaze verification module.

Provides safety layer to ensure user is looking at screen before processing gestures.
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class GazeState(Enum):
    """Enumeration of gaze validation states."""
    LOOKING_AT_SCREEN = "looking_at_screen"
    LOOKING_AWAY = "looking_away"
    UNKNOWN = "unknown"


@dataclass
class GazeVerification:
    """Container for gaze verification results."""
    state: GazeState
    gaze_angle: float  # Degrees from screen center
    horizontal_angle: float  # Degrees left/right
    vertical_angle: float  # Degrees up/down
    confidence: float  # 0-1
    is_valid: bool  # Whether gaze is within acceptable range


class EyeGazeValidator:
    """
    Validates that user is looking at the screen before processing gestures.
    
    This is a safety layer to prevent accidental gesture triggers when
    the user is not paying attention to the system.
    """
    
    def __init__(
        self,
        max_gaze_angle: float = 30.0,
        validation_frames: int = 5
    ):
        """
        Initialize gaze validator.
        
        Args:
            max_gaze_angle: Maximum angle from screen center (degrees)
            validation_frames: Frames required to confirm gaze validation
        """
        self.max_gaze_angle = max_gaze_angle
        self.validation_frames = validation_frames
        self.gaze_valid_count = 0
        self.last_gaze_state = GazeState.UNKNOWN
    
    def validate_from_head_angles(
        self,
        pitch: float,
        yaw: float
    ) -> GazeVerification:
        """
        Validate gaze using head pitch and yaw angles.
        
        Args:
            pitch: Head pitch angle in degrees (up/down)
            yaw: Head yaw angle in degrees (left/right)
            
        Returns:
            GazeVerification object with validation results
        """
        # Calculate total gaze angle from screen center
        total_angle = np.sqrt(pitch**2 + yaw**2)
        
        # Determine if valid
        is_valid = total_angle <= self.max_gaze_angle
        
        # Update validation frame counter
        if is_valid:
            self.gaze_valid_count = min(
                self.gaze_valid_count + 1,
                self.validation_frames
            )
        else:
            self.gaze_valid_count = max(self.gaze_valid_count - 1, 0)
        
        # Determine state
        if self.gaze_valid_count >= self.validation_frames:
            state = GazeState.LOOKING_AT_SCREEN
        elif self.gaze_valid_count == 0:
            state = GazeState.LOOKING_AWAY
        else:
            state = GazeState.UNKNOWN
        
        self.last_gaze_state = state
        
        return GazeVerification(
            state=state,
            gaze_angle=total_angle,
            horizontal_angle=yaw,
            vertical_angle=pitch,
            confidence=min(self.gaze_valid_count / self.validation_frames, 1.0),
            is_valid=(state == GazeState.LOOKING_AT_SCREEN)
        )
    
    def validate_from_eye_position(
        self,
        eye_center: Tuple[float, float],
        screen_width: float = 1.0,
        screen_height: float = 1.0
    ) -> GazeVerification:
        """
        Validate gaze using eye center position.
        
        Args:
            eye_center: Eye center position (normalized x, y)
            screen_width: Screen width (normalized, default 1.0)
            screen_height: Screen height (normalized, default 1.0)
            
        Returns:
            GazeVerification object
        """
        # Calculate angle from screen center
        # Assuming eye at (0.5, 0.5) is looking at center
        center_x = screen_width / 2
        center_y = screen_height / 2
        
        # Calculate angle (simplified: tan(angle) ≈ distance_from_center / depth)
        # Approximate depth based on typical viewing distance
        viewing_depth = 0.5  # arbitrary units
        
        horiz_angle = np.degrees(np.arctan(
            (eye_center[0] - center_x) / viewing_depth
        ))
        vert_angle = np.degrees(np.arctan(
            (eye_center[1] - center_y) / viewing_depth
        ))
        
        total_angle = np.sqrt(horiz_angle**2 + vert_angle**2)
        is_valid = total_angle <= self.max_gaze_angle
        
        # Update validation frame counter
        if is_valid:
            self.gaze_valid_count = min(
                self.gaze_valid_count + 1,
                self.validation_frames
            )
        else:
            self.gaze_valid_count = max(self.gaze_valid_count - 1, 0)
        
        # Determine state
        if self.gaze_valid_count >= self.validation_frames:
            state = GazeState.LOOKING_AT_SCREEN
        elif self.gaze_valid_count == 0:
            state = GazeState.LOOKING_AWAY
        else:
            state = GazeState.UNKNOWN
        
        self.last_gaze_state = state
        
        return GazeVerification(
            state=state,
            gaze_angle=total_angle,
            horizontal_angle=horiz_angle,
            vertical_angle=vert_angle,
            confidence=min(self.gaze_valid_count / self.validation_frames, 1.0),
            is_valid=(state == GazeState.LOOKING_AT_SCREEN)
        )
    
    def is_valid(self) -> bool:
        """
        Get current gaze validation state.
        
        Returns:
            True if user is confirmed looking at screen
        """
        return self.last_gaze_state == GazeState.LOOKING_AT_SCREEN
    
    def get_state(self) -> GazeState:
        """Get current gaze state."""
        return self.last_gaze_state
    
    def reset(self) -> None:
        """Reset validation counter."""
        self.gaze_valid_count = 0
        self.last_gaze_state = GazeState.UNKNOWN
    
    def set_max_angle(self, angle: float) -> None:
        """Adjust maximum allowed gaze angle."""
        self.max_gaze_angle = angle
    
    def set_validation_frames(self, frames: int) -> None:
        """Adjust number of frames required for validation."""
        self.validation_frames = frames
