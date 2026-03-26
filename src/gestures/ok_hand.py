"""
OK Hand gesture recognition.

Detects the "OK" hand gesture (thumb + index finger forming a circle).
Used for system activation/deactivation.
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class OKHandState(Enum):
    """States for OK hand gesture detection."""
    IDLE = "idle"
    OK_DETECTED = "ok_detected"
    OK_CONFIRMED = "ok_confirmed"


@dataclass
class OKHandGesture:
    """Container for OK hand gesture detection."""
    state: OKHandState = OKHandState.IDLE
    is_confirmed: bool = False
    confidence: float = 0.0
    frame_count: int = 0


class OKHandDetector:
    """
    Detects the OK hand gesture (thumb + index finger circle).
    
    Algorithm:
    1. Check if thumb tip and index tip are close (forming circle)
    2. Check if other fingers are extended (spread out)
    3. Hold for N frames to confirm
    """
    
    # Hand landmark indices
    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20
    THUMB_IP = 3
    INDEX_PIP = 6
    
    def __init__(self, circle_threshold: float = 0.05, confirm_frames: int = 10):
        """
        Initialize OK hand detector.
        
        Args:
            circle_threshold: Max distance between thumb and index tips (0-1 normalized)
            confirm_frames: Frames to hold gesture before confirming
        """
        self.circle_threshold = circle_threshold
        self.confirm_frames = confirm_frames
        self.gesture = OKHandGesture()
        self.frame_buffer = []
    
    def detect(self, landmarks: np.ndarray) -> OKHandGesture:
        """
        Detect OK hand gesture from hand landmarks.
        
        Args:
            landmarks: Hand landmarks (21 x 2, normalized 0-1)
            
        Returns:
            OKHandGesture with detection result
        """
        if landmarks.size == 0 or len(landmarks) < 21:
            self.gesture.state = OKHandState.IDLE
            self.gesture.is_confirmed = False
            self.frame_buffer = []
            return self.gesture
        
        # Get key points
        thumb_tip = landmarks[self.THUMB_TIP]
        index_tip = landmarks[self.INDEX_TIP]
        middle_tip = landmarks[self.MIDDLE_TIP]
        ring_tip = landmarks[self.RING_TIP]
        pinky_tip = landmarks[self.PINKY_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        
        # Check if thumb and index form a circle (STRICT threshold)
        thumb_index_distance = np.linalg.norm(thumb_tip - index_tip)
        is_circle = thumb_index_distance < self.circle_threshold
        
        # STRICT: Check if other fingers are clearly extended (not in a fist)
        # Fingers should be notably above thumb base position
        middle_extended = middle_tip[1] < (thumb_ip[1] - 0.08)
        ring_extended = ring_tip[1] < (thumb_ip[1] - 0.08)
        pinky_extended = pinky_tip[1] < (thumb_ip[1] - 0.08)
        
        # Require at least 2 fingers clearly extended
        fingers_extended = sum([middle_extended, ring_extended, pinky_extended]) >= 2
        
        # Determine if OK gesture is present
        is_ok = is_circle and fingers_extended
        
        # DEBUG: Print detection info periodically (less verbose)
        if len(self.frame_buffer) % 60 == 0 and len(self.frame_buffer) > 0:
            print(f"[OK_HAND] Distance: {thumb_index_distance:.3f} (threshold: {self.circle_threshold}), "
                  f"Extended fingers: {sum([middle_extended, ring_extended, pinky_extended])}/3, "
                  f"OK detected: {is_ok}, Confirmed: {sum(self.frame_buffer)}/{len(self.frame_buffer)}")
        
        if is_ok:
            self.frame_buffer.append(True)
            self.gesture.state = OKHandState.OK_DETECTED
            # Confidence based on how close thumb and index are (closer = more confident)
            self.gesture.confidence = max(0.5, 1.0 - (thumb_index_distance / self.circle_threshold))
        else:
            self.frame_buffer.append(False)
            self.gesture.state = OKHandState.IDLE
            self.gesture.confidence = 0.0
        
        # Keep only recent frames
        if len(self.frame_buffer) > self.confirm_frames:
            self.frame_buffer.pop(0)
        
        # Check if gesture is confirmed (held for N frames with high consistency)
        confirmed_count = sum(self.frame_buffer)
        if len(self.frame_buffer) == self.confirm_frames and confirmed_count >= (self.confirm_frames - 1):
            # Allow 1 frame of dropout for robustness
            self.gesture.state = OKHandState.OK_CONFIRMED
            self.gesture.is_confirmed = True
            self.gesture.frame_count = self.confirm_frames
            # Reset after confirmation
            self.frame_buffer = []
        else:
            self.gesture.is_confirmed = False
            self.gesture.frame_count = confirmed_count
        
        return self.gesture
    
    def reset(self):
        """Reset gesture state."""
        self.gesture = OKHandGesture()
        self.frame_buffer = []
