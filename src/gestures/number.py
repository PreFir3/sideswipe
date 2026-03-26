"""
Number selection gesture detection.

Detects when user holds up 1-5 fingers to switch tabs.
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass, field
from collections import deque

from config import NUMBER_SELECTION


@dataclass
class NumberGesture:
    """Container for number gesture detection result."""
    number: int  # 1-5 fingers detected
    confidence: float  # Detection confidence 0-1
    is_confirmed: bool = False
    frame_count: int = 0


class NumberDetector:
    """
    Detects number of extended fingers (1-5) for tab switching.
    
    Uses hand landmark positions to count extended fingers:
    - Stabilizes count over multiple frames to avoid jitter
    - Only confirms after consistent count for N frames
    - Validates finger extension state
    """
    
    def __init__(
        self,
        confidence_threshold: float = NUMBER_SELECTION["confidence_threshold"],
        frame_stability: int = NUMBER_SELECTION["stabilization_frames"],
        min_fingers: int = 1,
        max_fingers: int = 5
    ):
        """
        Initialize number detector.
        
        Args:
            confidence_threshold: Minimum confidence to register finger count
            frame_stability: Frames to hold count before confirming
            min_fingers: Minimum fingers to detect (usually 1)
            max_fingers: Maximum fingers to detect (usually 5)
        """
        self.confidence_threshold = confidence_threshold
        self.frame_stability = frame_stability
        self.min_fingers = min_fingers
        self.max_fingers = max_fingers
        
        # State tracking
        self.frame_history: deque = deque(maxlen=frame_stability)
        self.current_number = 0
        self.confirmation_frames = 0
        self.last_confirmed_number = 0
        
        # Lazy-load the finger counter function to avoid recreating HandDetector
        self._get_finger_count = None
    
    def detect(self, hand_detection) -> NumberGesture:
        """
        Detect number of extended fingers from hand detection.
        
        Args:
            hand_detection: HandDetection object from hand detector
            
        Returns:
            NumberGesture with detected number and confirmation status
        """
        gesture = NumberGesture(
            number=0,
            confidence=0.0,
            is_confirmed=False,
            frame_count=0
        )
        
        if not hand_detection.present or hand_detection.landmarks.size == 0:
            return gesture
        
        # Count fingers using landmark positions
        from detectors.hand import HandDetector
        detector = HandDetector()
        finger_count = detector.get_finger_count(hand_detection.landmarks)
        
        # Clamp to valid range
        finger_count = max(self.min_fingers, min(self.max_fingers, finger_count))
        
        # Add to history
        self.frame_history.append(finger_count)
        
        # Check if count is stable (all recent frames same)
        if len(self.frame_history) > 0:
            if all(f == self.frame_history[0] for f in self.frame_history):
                self.current_number = self.frame_history[0]
                self.confirmation_frames += 1
            else:
                self.confirmation_frames = 0
        
        gesture.number = self.current_number
        gesture.confidence = hand_detection.confidence
        gesture.frame_count = self.confirmation_frames
        
        # Confirm after stable frames
        if self.confirmation_frames >= self.frame_stability:
            if self.current_number != self.last_confirmed_number:
                gesture.is_confirmed = True
                self.last_confirmed_number = self.current_number
                self.confirmation_frames = 0
                self.frame_history.clear()
        
        return gesture
    
    def reset(self) -> None:
        """Reset detector state."""
        self.frame_history.clear()
        self.current_number = 0
        self.confirmation_frames = 0
        self.last_confirmed_number = 0
