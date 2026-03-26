"""
Clap Activation gesture recognition.

Detects hand claps for system on/off control.
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class ClapState(Enum):
    """Enumeration of clap gesture states."""
    IDLE = "idle"
    HANDS_APPROACHING = "hands_approaching"
    HANDS_CONTACT = "hands_contact"
    SINGLE_CLAP_DETECTED = "single_clap"
    DOUBLE_CLAP_DETECTED = "double_clap"


@dataclass
class ClapGesture:
    """Container for clap detection results."""
    state: ClapState
    clap_count: int  # 1 or 2
    is_confirmed: bool  # Whether clap gesture confirmed
    distance: float  # Current hand distance
    confidence: float  # 0-1


class ClapDetector:
    """
    Detects clap gestures (single or double) for system activation.
    
    Algorithm:
    1. Track distance between hands
    2. Detect rapid decrease (hands approaching)
    3. Detect rapid increase (hands separating after contact)
    4. Count claps and detect single vs double clap
    5. Return gesture when confirmed
    
    Very sensitive gesture - high thresholds needed to avoid false triggers.
    """
    
    def __init__(
        self,
        max_palm_distance: float = 0.15,
        velocity_threshold: float = 0.5,
        clap_frame_window: int = 15,
        double_clap_window: float = 0.8,
        single_clap_delay: float = 1.5,
        cooldown: float = 1.0,
        fps: int = 30
    ):
        """
        Initialize clap detector.
        
        Args:
            max_palm_distance: Maximum distance for hands to be considered in contact (normalized)
            velocity_threshold: Minimum hand velocity for clap (normalized/frame)
            clap_frame_window: Frames to monitor for clap motion
            double_clap_window: Time window between claps for double clap (seconds)
            single_clap_delay: Delay before confirming single clap (seconds)
            cooldown: Cooldown after clap (seconds)
            fps: Expected frames per second
        """
        self.max_palm_distance = max_palm_distance
        self.velocity_threshold = velocity_threshold
        self.clap_frame_window = clap_frame_window
        self.double_clap_window = double_clap_window
        self.single_clap_delay = single_clap_delay
        self.cooldown = cooldown
        self.fps = fps
        
        # State tracking
        self.state = ClapState.IDLE
        self.current_distance = 0
        self.previous_distance = 0
        self.frame_count = 0
        self.clap_count = 0
        self.first_clap_frame = None
        self.second_clap_frame = None
        self.cooldown_counter = 0
    
    def add_hand_distance(self, distance: float) -> ClapGesture:
        """
        Add hand distance measurement from hand detection.
        
        Args:
            distance: Distance between hand centers (normalized 0-1)
            
        Returns:
            ClapGesture with detection results
        """
        self.frame_count += 1
        self.previous_distance = self.current_distance
        self.current_distance = distance
        
        # Decrement cooldown
        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
        
        # Calculate velocity (rate of distance change)
        velocity = self.current_distance - self.previous_distance
        abs_velocity = abs(velocity)
        
        # State machine for clap detection
        is_confirmed = False
        clap_count = 0
        confidence = 0
        
        if self.cooldown_counter == 0:
            # Detect hands approaching (distance decreasing rapidly)
            if (self.state in [ClapState.IDLE, ClapState.HANDS_CONTACT] and
                velocity < -self.velocity_threshold and
                self.current_distance < self.max_palm_distance):
                
                self.state = ClapState.HANDS_APPROACHING
            
            # Detect contact and record clap
            elif (self.state == ClapState.HANDS_APPROACHING and
                  self.current_distance < self.max_palm_distance):
                
                self.state = ClapState.HANDS_CONTACT
                self.clap_count += 1
                self.frame_count = 0
                
                # Record timing
                if self.clap_count == 1:
                    self.first_clap_frame = self.frame_count
                elif self.clap_count == 2:
                    self.second_clap_frame = self.frame_count
            
            # Detect hands separating (distance increasing after contact)
            elif (self.state == ClapState.HANDS_CONTACT and
                  velocity > self.velocity_threshold):
                
                self.state = ClapState.IDLE
                
                # Determine single vs double clap
                if self.clap_count == 1:
                    # Wait for potential second clap
                    if self.frame_count > int(self.single_clap_delay * self.fps):
                        # Single clap confirmed
                        is_confirmed = True
                        clap_count = 1
                        confidence = 0.9
                        self.clap_count = 0
                        self.cooldown_counter = int(self.cooldown * self.fps)
                
                elif self.clap_count == 2:
                    # Double clap confirmed
                    clap_time = (self.second_clap_frame - self.first_clap_frame) / self.fps
                    
                    if clap_time <= self.double_clap_window:
                        is_confirmed = True
                        clap_count = 2
                        confidence = 0.95
                        self.clap_count = 0
                        self.cooldown_counter = int(self.cooldown * self.fps)
            
            # Reset if too much time without clap completion
            elif (self.state == ClapState.HANDS_APPROACHING and
                  self.frame_count > self.clap_frame_window):
                self.state = ClapState.IDLE
                self.clap_count = 0
        
        return ClapGesture(
            state=self.state,
            clap_count=clap_count if is_confirmed else 0,
            is_confirmed=is_confirmed,
            distance=distance,
            confidence=confidence
        )
    
    def reset(self) -> None:
        """Reset the detector."""
        self.state = ClapState.IDLE
        self.frame_count = 0
        self.clap_count = 0
        self.cooldown_counter = 0
    
    def set_sensitivity(self, velocity_threshold: float) -> None:
        """
        Adjust sensitivity by changing velocity threshold.
        
        Args:
            velocity_threshold: New threshold
        """
        self.velocity_threshold = velocity_threshold
    
    def get_clap_count(self) -> int:
        """Get number of claps detected since last reset."""
        return self.clap_count
