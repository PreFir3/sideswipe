"""
Hand landmark detection using MediaPipe.

Detects hand position and all 21 hand landmarks from webcam video.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


@dataclass
class HandDetection:
    """Container for hand detection results."""
    landmarks: np.ndarray  # 21 x 2 array of normalized (0-1) coordinates
    handedness: str  # "Left" or "Right"
    confidence: float  # Detection confidence 0-1
    present: bool  # Whether hand is detected in frame


class HandDetector:
    """
    Detects hands and their landmarks in video frames.
    
    Uses MediaPipe's hand detection model to identify:
    - Hand presence and position
    - All 21 hand landmarks
    - Hand orientation (left/right)
    - Detection confidence scores
    """
    
    # Hand landmark indices for reference
    LANDMARK_WRIST = 0
    LANDMARK_THUMB_TIP = 4
    LANDMARK_INDEX_TIP = 8
    LANDMARK_MIDDLE_TIP = 12
    LANDMARK_RING_TIP = 16
    LANDMARK_PINKY_TIP = 20
    
    # Finger tip indices for counting
    FINGER_TIPS = [4, 8, 12, 16, 20]
    # Finger PIP (middle knuckle) indices
    FINGER_PIPS = [3, 7, 11, 15, 19]
    
    # Hand landmark connections (for visualization)
    CONNECTIONS = [
        # Thumb
        (0, 1), (1, 2), (2, 3), (3, 4),
        # Index finger
        (0, 5), (5, 6), (6, 7), (7, 8),
        # Middle finger
        (0, 9), (9, 10), (10, 11), (11, 12),
        # Ring finger
        (0, 13), (13, 14), (14, 15), (15, 16),
        # Pinky
        (0, 17), (17, 18), (18, 19), (19, 20),
    ]
    
    def __init__(
        self,
        detection_confidence: float = 0.85,
        tracking_confidence: float = 0.8,
        max_num_hands: int = 2,
        model_complexity: int = 1
    ):
        """
        Initialize hand detector with MediaPipe.
        
        Args:
            detection_confidence: Confidence threshold for detection (0-1)
            tracking_confidence: Confidence threshold for tracking (0-1)
            max_num_hands: Maximum number of hands to detect
            model_complexity: 0 (lite) or 1 (full) - affects accuracy vs speed
        """
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence
        self.max_num_hands = max_num_hands
        
        # Initialize MediaPipe hand detection
        # For version 0.10.33, we need to handle model loading differently
        self.hands = None
        self._init_detector()
    
    def _init_detector(self) -> None:
        """Initialize the hand detector with appropriate MediaPipe model."""
        import urllib.request
        import os
        
        model_path = "hand_landmarker.task"
        model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        
        # Download model if not exists
        if not os.path.exists(model_path):
            try:
                print("Downloading MediaPipe hand landmark model...")
                urllib.request.urlretrieve(model_url, model_path)
                print(f"✓ Model downloaded to {model_path}")
            except Exception as e:
                print(f"Warning: Could not download model: {e}")
        
        # Try to create hand landmarker
        try:
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=self.max_num_hands,
                min_hand_detection_confidence=self.detection_confidence,      # Higher = more stable tracking
                min_hand_presence_confidence=self.tracking_confidence,      # Higher = more stable
                min_tracking_confidence=self.tracking_confidence            # Higher = more stable
            )
            self.hands = vision.HandLandmarker.create_from_options(options)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize hand detector: {e}")
    
    def detect(self, frame: np.ndarray) -> List[HandDetection]:
        """
        Detect hands and landmarks in a video frame.
        
        Args:
            frame: Input video frame (BGR format, as from OpenCV)
            
        Returns:
            List of HandDetection objects (empty if no hands detected)
        """
        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to MediaPipe Image format
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Run hand detection
        results = self.hands.detect(mp_image)
        
        detections = []
        
        if results.hand_landmarks:
            for hand_landmarks, hand_info in zip(results.hand_landmarks, results.handedness):
                # Extract normalized coordinates (0-1)
                landmark_array = np.array([
                    [lm.x, lm.y] for lm in hand_landmarks
                ])
                
                # Get handedness label
                hand_label = hand_info[0].category_name if hand_info else "Unknown"
                hand_confidence = hand_info[0].score if hand_info else 0.0
                
                detection = HandDetection(
                    landmarks=landmark_array,
                    handedness=hand_label,
                    confidence=hand_confidence,
                    present=True
                )
                detections.append(detection)
        else:
            # No hands detected - return empty hand
            detections = [HandDetection(
                landmarks=np.empty((21, 2)),
                handedness="None",
                confidence=0.0,
                present=False
            )]
        
        return detections
    
    def get_finger_count(self, landmarks: np.ndarray) -> int:
        """
        Count how many fingers are extended (open) in a hand.
        
        Algorithm:
        - Thumb: Check if tip X is farther from wrist than PIP
        - Other fingers: Check if tip Y is above PIP (higher up on frame)
        
        Args:
            landmarks: Hand landmarks (21 x 2 array, normalized 0-1)
            
        Returns:
            Number of extended fingers (0-5)
        """
        if landmarks.size == 0:
            return 0
        
        count = 0
        
        # Thumb (check horizontal position)
        if landmarks[self.LANDMARK_THUMB_TIP][0] < landmarks[self.FINGER_PIPS[0]][0]:
            count += 1
        
        # Other four fingers (check vertical position)
        for tip_idx, pip_idx in zip(self.FINGER_TIPS[1:], self.FINGER_PIPS[1:]):
            # Finger is extended if tip is above (smaller Y) than PIP
            if landmarks[tip_idx][1] < landmarks[pip_idx][1]:
                count += 1
        
        return count
    
    def get_hand_center(self, landmarks: np.ndarray) -> Tuple[float, float]:
        """
        Calculate hand center position (average of all landmarks).
        
        Args:
            landmarks: Hand landmarks (21 x 2 array)
            
        Returns:
            Tuple of (x, y) center position (normalized 0-1)
        """
        if landmarks.size == 0:
            return (0.0, 0.0)
        
        return (np.mean(landmarks[:, 0]), np.mean(landmarks[:, 1]))
    
    def get_palm_center(self, landmarks: np.ndarray) -> Tuple[float, float]:
        """
        Calculate palm center position (average of first 4 landmarks).
        
        Args:
            landmarks: Hand landmarks (21 x 2 array)
            
        Returns:
            Tuple of (x, y) palm center (normalized 0-1)
        """
        if landmarks.size == 0:
            return (0.0, 0.0)
        
        # Palm is roughly landmarks 0-4 (wrist + base of thumb/index)
        palm_points = landmarks[:5]
        return (np.mean(palm_points[:, 0]), np.mean(palm_points[:, 1]))
    
    def get_index_finger_tip(self, landmarks: np.ndarray) -> Tuple[float, float]:
        """
        Get index finger tip position (landmark 8).
        
        Args:
            landmarks: Hand landmarks (21 x 2 array)
            
        Returns:
            Tuple of (x, y) index tip position (normalized 0-1)
        """
        if landmarks.size == 0:
            return (0.0, 0.0)
        
        return tuple(landmarks[self.LANDMARK_INDEX_TIP])
    
    def get_hand_distance(
        self,
        hand1_landmarks: np.ndarray,
        hand2_landmarks: np.ndarray
    ) -> float:
        """
        Calculate distance between two hands (palm centers).
        
        Args:
            hand1_landmarks: First hand landmarks (21 x 2)
            hand2_landmarks: Second hand landmarks (21 x 2)
            
        Returns:
            Distance as normalized value (0-1.414 approximately)
        """
        if hand1_landmarks.size == 0 or hand2_landmarks.size == 0:
            return float('inf')
        
        center1 = self.get_palm_center(hand1_landmarks)
        center2 = self.get_palm_center(hand2_landmarks)
        
        dx = center1[0] - center2[0]
        dy = center1[1] - center2[1]
        
        return np.sqrt(dx**2 + dy**2)
    
    def get_hand_velocity(
        self,
        current_landmarks: np.ndarray,
        previous_landmarks: np.ndarray
    ) -> Tuple[float, float]:
        """
        Calculate hand velocity between frames.
        
        Args:
            current_landmarks: Hand landmarks current frame (21 x 2)
            previous_landmarks: Hand landmarks previous frame (21 x 2)
            
        Returns:
            Tuple of (velocity_x, velocity_y) in normalized coordinates
        """
        if current_landmarks.size == 0 or previous_landmarks.size == 0:
            return (0.0, 0.0)
        
        current_center = self.get_hand_center(current_landmarks)
        previous_center = self.get_hand_center(previous_landmarks)
        
        vel_x = current_center[0] - previous_center[0]
        vel_y = current_center[1] - previous_center[1]
        
        return (vel_x, vel_y)
    
    def denormalize_landmarks(
        self,
        landmarks: np.ndarray,
        frame_width: int,
        frame_height: int
    ) -> np.ndarray:
        """
        Convert normalized landmarks (0-1) to pixel coordinates.
        
        Args:
            landmarks: Normalized landmarks (21 x 2)
            frame_width: Video frame width in pixels
            frame_height: Video frame height in pixels
            
        Returns:
            Landmarks in pixel coordinates
        """
        if landmarks.size == 0:
            return landmarks
        
        pixel_landmarks = landmarks.copy()
        pixel_landmarks[:, 0] *= frame_width
        pixel_landmarks[:, 1] *= frame_height
        
        return pixel_landmarks
    
    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'hands'):
            self.hands.close()
