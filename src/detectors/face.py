"""
Face and head tracking using MediaPipe.

Detects face presence, head orientation, and facial landmarks.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


@dataclass
class FaceDetection:
    """Container for face detection results."""
    landmarks: np.ndarray  # N x 2 array of normalized (0-1) coordinates
    head_euler_angles: Tuple[float, float, float]  # (pitch, yaw, roll) in degrees
    confidence: float  # Detection confidence 0-1
    present: bool  # Whether face is detected


class FaceDetector:
    """
    Detects faces and head orientation using MediaPipe.
    
    Uses MediaPipe's face mesh detection to identify:
    - Face presence and landmarks
    - Head orientation (pitch, yaw, roll angles)
    - Eye position and gaze direction
    """
    
    # Key landmark indices
    LANDMARK_NOSE_TIP = 1
    LANDMARK_LEFT_EYE_INNER = 133
    LANDMARK_RIGHT_EYE_INNER = 362
    LANDMARK_MOUTH_LEFT = 61
    LANDMARK_MOUTH_RIGHT = 291
    
    def __init__(
        self,
        detection_confidence: float = 0.7,
        refine_landmarks: bool = True
    ):
        """
        Initialize face detector with MediaPipe.
        
        Args:
            detection_confidence: Confidence threshold for detection (0-1)
            refine_landmarks: Whether to refine landmarks (slower but more accurate)
        """
        self.detection_confidence = detection_confidence
        
        # Initialize MediaPipe face landmarker
        self.face_landmarker = None
        self._init_detector()
        
        # For head orientation calculation
        self._calibrate_neutral_angles()
    
    def _init_detector(self) -> None:
        """Initialize the face detector with appropriate MediaPipe model."""
        import urllib.request
        import os
        
        model_path = "face_landmarker.task"
        model_url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
        
        # Download model if not exists
        if not os.path.exists(model_path):
            try:
                print("Downloading MediaPipe face landmark model...")
                urllib.request.urlretrieve(model_url, model_path)
                print(f"✓ Model downloaded to {model_path}")
            except Exception as e:
                print(f"Warning: Could not download model: {e}")
        
        # Try to create face landmarker
        try:
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                num_faces=1,
                min_face_detection_confidence=self.detection_confidence,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.face_landmarker = vision.FaceLandmarker.create_from_options(options)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize face detector: {e}")
    
    def _calibrate_neutral_angles(self) -> None:
        """Set neutral head angles (to be calibrated per user)."""
        self.neutral_pitch = 0.0  # Looking straight ahead
        self.neutral_yaw = 0.0
        self.neutral_roll = 0.0
    
    def detect(self, frame: np.ndarray) -> FaceDetection:
        """
        Detect face and head orientation in a video frame.
        
        Args:
            frame: Input video frame (BGR format, as from OpenCV)
            
        Returns:
            FaceDetection object with landmarks and head angles
        """
        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to MediaPipe Image format
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Run face detection
        results = self.face_landmarker.detect(mp_image)
        
        if results.face_landmarks and len(results.face_landmarks) > 0:
            landmarks_list = results.face_landmarks[0]
            
            # Extract normalized coordinates (0-1)
            landmark_array = np.array([
                [lm.x, lm.y] for lm in landmarks_list
            ])
            
            # Calculate head orientation angles
            head_angles = self._calculate_head_angles(landmark_array)
            
            return FaceDetection(
                landmarks=landmark_array,
                head_euler_angles=head_angles,
                confidence=0.9,  # MediaPipe doesn't provide per-face confidence
                present=True
            )
        else:
            return FaceDetection(
                landmarks=np.empty((468, 2)),
                head_euler_angles=(0.0, 0.0, 0.0),
                confidence=0.0,
                present=False
            )
    
    def _calculate_head_angles(
        self,
        landmarks: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        Calculate head pitch, yaw, and roll angles from facial landmarks.
        
        Uses key facial landmarks to estimate 3D head orientation.
        
        Args:
            landmarks: Face landmarks (468 x 2, normalized)
            
        Returns:
            Tuple of (pitch, yaw, roll) in degrees
            - Pitch: Up (-) / Down (+)
            - Yaw: Left (-) / Right (+)
            - Roll: CCW (-) / CW (+)
        """
        if landmarks.size == 0:
            return (0.0, 0.0, 0.0)
        
        # Key points for angle calculation
        nose = landmarks[self.LANDMARK_NOSE_TIP]
        left_eye = landmarks[self.LANDMARK_LEFT_EYE_INNER]
        right_eye = landmarks[self.LANDMARK_RIGHT_EYE_INNER]
        mouth_left = landmarks[self.LANDMARK_MOUTH_LEFT]
        mouth_right = landmarks[self.LANDMARK_MOUTH_RIGHT]
        
        # Calculate pitch (vertical head tilt) from nose to mouth
        # Positive = tilted down, Negative = tilted up
        mouth_center_y = (mouth_left[1] + mouth_right[1]) / 2
        pitch = np.degrees(np.arctan2(mouth_center_y - nose[1], 0.1))
        
        # Calculate yaw (horizontal head rotation) from eye positions
        # Positive = face right, Negative = face left
        eye_diff_x = right_eye[0] - left_eye[0]
        eye_center_x = (left_eye[0] + right_eye[0]) / 2
        yaw = np.degrees(np.arctan2(eye_center_x - 0.5, 0.1))
        
        # Calculate roll (head tilt left-right) from eyes
        eye_diff_y = right_eye[1] - left_eye[1]
        roll = np.degrees(np.arctan2(eye_diff_y, eye_diff_x))
        
        return (pitch, yaw, roll)
    
    def get_gaze_direction(self, landmarks: np.ndarray) -> Tuple[float, float]:
        """
        Estimate gaze direction from eye landmarks.
        
        Args:
            landmarks: Face landmarks (468 x 2)
            
        Returns:
            Tuple of (gaze_x, gaze_y) where:
            - gaze_x: -1 = looking left, 0 = center, +1 = looking right
            - gaze_y: -1 = looking up, 0 = center, +1 = looking down
        """
        if landmarks.size == 0:
            return (0.0, 0.0)
        
        # Get eye positions
        left_eye = landmarks[self.LANDMARK_LEFT_EYE_INNER]
        right_eye = landmarks[self.LANDMARK_RIGHT_EYE_INNER]
        
        # Average eye position
        eye_center = (left_eye + right_eye) / 2
        
        # Simple gaze: deviation from center (frame is 0-1 normalized)
        gaze_x = (eye_center[0] - 0.5) * 2  # Scale to -1 to 1
        gaze_y = (eye_center[1] - 0.5) * 2
        
        return (gaze_x, gaze_y)
    
    def is_looking_at_screen(
        self,
        landmarks: np.ndarray,
        max_gaze_angle: float = 30.0
    ) -> bool:
        """
        Check if person is looking at the screen (eye gaze validation).
        
        Uses head angle and gaze direction to determine if eyes are on screen.
        
        Args:
            landmarks: Face landmarks (468 x 2)
            max_gaze_angle: Maximum angle from screen center (degrees)
            
        Returns:
            True if person appears to be looking at screen
        """
        if landmarks.size == 0:
            return False
        
        # Get gaze direction
        gaze_x, gaze_y = self.get_gaze_direction(landmarks)
        
        # Convert normalized gaze to angle estimate
        gaze_angle_x = np.degrees(np.arctan(gaze_x))
        gaze_angle_y = np.degrees(np.arctan(gaze_y))
        
        # Combined gaze angle
        total_angle = np.sqrt(gaze_angle_x**2 + gaze_angle_y**2)
        
        return total_angle <= max_gaze_angle
    
    def calibrate_neutral_head_position(
        self,
        landmarks: np.ndarray
    ) -> None:
        """
        Calibrate the neutral (straight ahead) head position.
        
        Should be called once at startup while user looks straight ahead.
        
        Args:
            landmarks: Face landmarks (468 x 2)
        """
        if landmarks.size > 0:
            pitch, yaw, roll = self._calculate_head_angles(landmarks)
            self.neutral_pitch = pitch
            self.neutral_yaw = yaw
            self.neutral_roll = roll
    
    def get_head_angle_deviation(
        self,
        landmarks: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        Get head angle deviation from calibrated neutral position.
        
        Args:
            landmarks: Face landmarks (468 x 2)
            
        Returns:
            Tuple of (pitch_dev, yaw_dev, roll_dev) in degrees
        """
        if landmarks.size == 0:
            return (0.0, 0.0, 0.0)
        
        pitch, yaw, roll = self._calculate_head_angles(landmarks)
        
        return (
            pitch - self.neutral_pitch,
            yaw - self.neutral_yaw,
            roll - self.neutral_roll
        )
    
    def get_head_tilt_vertical(self, landmarks: np.ndarray) -> float:
        """
        Get vertical head tilt (pitch) in degrees.
        
        Args:
            landmarks: Face landmarks (468 x 2)
            
        Returns:
            Pitch angle in degrees (negative = tilted up, positive = tilted down)
        """
        if landmarks.size == 0:
            return 0.0
        
        pitch, _, _ = self._calculate_head_angles(landmarks)
        return pitch - self.neutral_pitch
    
    def get_head_tilt_horizontal(self, landmarks: np.ndarray) -> float:
        """
        Get horizontal head tilt (yaw) in degrees.
        
        Args:
            landmarks: Face landmarks (468 x 2)
            
        Returns:
            Yaw angle in degrees (negative = tilted left, positive = tilted right)
        """
        if landmarks.size == 0:
            return 0.0
        
        _, yaw, _ = self._calculate_head_angles(landmarks)
        return yaw - self.neutral_yaw
    
    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()
