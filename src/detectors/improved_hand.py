"""
Improved Hand Tracker for Natural Finger/Hand Movement Detection
Works with hands at any angle/position, not just flat/lowered hands
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


@dataclass
class RobustHandDetection:
    """Enhanced hand detection with more reliable tracking."""
    landmarks: np.ndarray          # 21 x 2 array of normalized coordinates
    handedness: str                # "Left" or "Right"
    confidence: float              # Detection confidence 0-1
    present: bool                  # Whether hand is detected
    hand_center: Tuple[float, float]  # Center of palm
    index_tip: Tuple[float, float]    # Index finger tip
    middle_tip: Tuple[float, float]   # Middle finger tip
    thumb_tip: Tuple[float, float]    # Thumb tip
    wrist: Tuple[float, float]        # Wrist position
    is_pointing: bool                 # Is hand pointing (index up)
    is_pinching: bool                 # Is hand pinching
    is_flat: bool                     # Is hand flat/open
    hand_velocity: Tuple[float, float] # Movement velocity


class ImprovedHandDetector:
    """
    Improved hand detection that works with natural hand movements.
    
    Key improvements:
    - Detects hands at any angle/rotation
    - Tracks individual finger positions
    - Robust to hand movement velocity
    - Detects multiple gesture states simultaneously
    """
    
    # Landmark indices
    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    INDEX_PIP = 6
    MIDDLE_TIP = 12
    MIDDLE_PIP = 10
    RING_TIP = 16
    PINKY_TIP = 20
    PALM_CENTER = 9
    
    # Gesture detection thresholds
    PINCH_THRESHOLD = 0.05       # Thumb-index distance
    POINT_INDEX_THRESHOLD = 0.03 # Index must be extended
    PALM_THRESHOLD = 0.08        # Palm openness
    
    def __init__(self, detection_confidence: float = 0.8, tracking_confidence: float = 0.8):
        """Initialize improved hand detector."""
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence
        
        # Initialize MediaPipe
        self.hands = None
        self._init_detector()
        
        # Tracking state
        self.previous_landmarks = None
        self.smooth_landmarks = None
    
    def _init_detector(self) -> None:
        """Initialize MediaPipe hand detector."""
        import urllib.request
        import os
        
        model_path = "hand_landmarker.task"
        model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        
        # Download model if needed
        if not os.path.exists(model_path):
            try:
                print("📥 Downloading hand model...")
                urllib.request.urlretrieve(model_url, model_path)
                print(f"✓ Model ready")
            except Exception as e:
                print(f"Warning: {e}")
        
        try:
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=2,
                min_hand_detection_confidence=self.detection_confidence,
                min_hand_presence_confidence=self.tracking_confidence,
                min_tracking_confidence=self.tracking_confidence
            )
            self.hands = vision.HandLandmarker.create_from_options(options)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize hand detector: {e}")
    
    def detect(self, frame: np.ndarray) -> List[RobustHandDetection]:
        """
        Detect hands with robust gesture recognition.
        
        Args:
            frame: Input frame (BGR from OpenCV)
            
        Returns:
            List of RobustHandDetection objects
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Run detection
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        results = self.hands.detect(mp_image)
        
        detections = []
        
        if results.hand_landmarks:
            for hand_landmarks, hand_info in zip(results.hand_landmarks, results.handedness):
                # Extract landmarks
                landmark_array = np.array([
                    [lm.x, lm.y] for lm in hand_landmarks
                ])
                
                # Smooth landmarks
                if self.previous_landmarks is not None:
                    smoothed = 0.7 * self.previous_landmarks + 0.3 * landmark_array
                else:
                    smoothed = landmark_array
                
                self.previous_landmarks = landmark_array
                
                # Get key positions
                hand_center = self._get_hand_center(smoothed)
                index_tip = tuple(smoothed[self.INDEX_TIP])
                middle_tip = tuple(smoothed[self.MIDDLE_TIP])
                thumb_tip = tuple(smoothed[self.THUMB_TIP])
                wrist = tuple(smoothed[self.WRIST])
                
                # Detect gesture states
                is_pointing = self._is_pointing(smoothed)
                is_pinching = self._is_pinching(smoothed)
                is_flat = self._is_palm_open(smoothed)
                
                # Calculate velocity
                velocity = self._calculate_velocity(smoothed)
                
                # Get handedness
                hand_label = hand_info[0].category_name if hand_info else "Unknown"
                hand_confidence = hand_info[0].score if hand_info else 0.0
                
                detection = RobustHandDetection(
                    landmarks=smoothed,
                    handedness=hand_label,
                    confidence=hand_confidence,
                    present=True,
                    hand_center=hand_center,
                    index_tip=index_tip,
                    middle_tip=middle_tip,
                    thumb_tip=thumb_tip,
                    wrist=wrist,
                    is_pointing=is_pointing,
                    is_pinching=is_pinching,
                    is_flat=is_flat,
                    hand_velocity=velocity
                )
                detections.append(detection)
        
        # No hands detected
        if not detections:
            detections = [RobustHandDetection(
                landmarks=np.empty((21, 2)),
                handedness="None",
                confidence=0.0,
                present=False,
                hand_center=(0, 0),
                index_tip=(0, 0),
                middle_tip=(0, 0),
                thumb_tip=(0, 0),
                wrist=(0, 0),
                is_pointing=False,
                is_pinching=False,
                is_flat=False,
                hand_velocity=(0, 0)
            )]
        
        return detections
    
    def _get_hand_center(self, landmarks: np.ndarray) -> Tuple[float, float]:
        """Get palm center position."""
        if landmarks.size == 0:
            return (0, 0)
        palm_points = landmarks[0:10]
        center_x = np.mean(palm_points[:, 0])
        center_y = np.mean(palm_points[:, 1])
        return (center_x, center_y)
    
    def _is_pointing(self, landmarks: np.ndarray) -> bool:
        """Detect pointing gesture (index extended, others closed)."""
        if landmarks.size == 0 or len(landmarks) < 21:
            return False
        
        # Index should be extended
        index_extended = landmarks[self.INDEX_TIP][1] < landmarks[self.INDEX_PIP][1] - 0.05
        
        # Other fingers should be closed
        middle_closed = landmarks[self.MIDDLE_TIP][1] > landmarks[self.MIDDLE_PIP][1]
        ring_closed = landmarks[self.RING_TIP][1] > landmarks[self.MIDDLE_PIP][1]
        pinky_closed = landmarks[self.PINKY_TIP][1] > landmarks[self.MIDDLE_PIP][1]
        
        return index_extended and middle_closed and ring_closed and pinky_closed
    
    def _is_pinching(self, landmarks: np.ndarray) -> bool:
        """Detect pinch gesture (thumb and index close)."""
        if landmarks.size == 0 or len(landmarks) < 21:
            return False
        
        thumb_tip = landmarks[self.THUMB_TIP]
        index_tip = landmarks[self.INDEX_TIP]
        
        distance = np.linalg.norm(thumb_tip - index_tip)
        return distance < self.PINCH_THRESHOLD
    
    def _is_palm_open(self, landmarks: np.ndarray) -> bool:
        """Detect open palm (all fingers extended)."""
        if landmarks.size == 0 or len(landmarks) < 21:
            return False
        
        fingers_pips = [
            landmarks[3],   # Thumb IP
            landmarks[6],   # Index PIP
            landmarks[10],  # Middle PIP
            landmarks[14],  # Ring PIP
            landmarks[18]   # Pinky PIP
        ]
        fingers_tips = [
            landmarks[4],   # Thumb TIP
            landmarks[8],   # Index TIP
            landmarks[12],  # Middle TIP
            landmarks[16],  # Ring TIP
            landmarks[20]   # Pinky TIP
        ]
        
        extended = 0
        for pip, tip in zip(fingers_pips, fingers_tips):
            if tip[1] < pip[1] - 0.05:
                extended += 1
        
        return extended >= 4
    
    def _calculate_velocity(self, landmarks: np.ndarray) -> Tuple[float, float]:
        """Calculate hand movement velocity."""
        if self.previous_landmarks is None or self.previous_landmarks.size == 0:
            return (0, 0)
        
        current_center = self._get_hand_center(landmarks)
        previous_center = self._get_hand_center(self.previous_landmarks)
        
        vel_x = current_center[0] - previous_center[0]
        vel_y = current_center[1] - previous_center[1]
        
        return (vel_x, vel_y)
    
    def close(self) -> None:
        """Cleanup."""
        if hasattr(self, 'hands'):
            self.hands.close()
