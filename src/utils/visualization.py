"""
Visualization utilities for gesture detection and debugging.

Provides real-time feedback on detected landmarks, thresholds, and gesture states.
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional, Dict, Any


class GestureVisualizer:
    """
    Visualizes hand landmarks, face landmarks, and gesture states on video frames.
    
    Used for debugging and user feedback.
    """
    
    # Color definitions (BGR for OpenCV)
    COLOR_HAND = (0, 255, 0)          # Green
    COLOR_FACE = (255, 0, 0)          # Blue
    COLOR_GESTURE_ACTIVE = (0, 255, 255)  # Cyan
    COLOR_GESTURE_INACTIVE = (128, 128, 128)  # Gray
    COLOR_WARNING = (0, 165, 255)     # Orange
    COLOR_ERROR = (0, 0, 255)         # Red
    COLOR_SUCCESS = (0, 255, 0)       # Green
    
    def __init__(self, frame_width: int = 1280, frame_height: int = 720):
        """
        Initialize visualizer.
        
        Args:
            frame_width: Video frame width
            frame_height: Video frame height
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
    
    def draw_hand_landmarks(
        self,
        frame: np.ndarray,
        landmarks: np.ndarray,
        connections: Optional[List[Tuple[int, int]]] = None,
        color: Tuple[int, int, int] = None
    ) -> np.ndarray:
        """
        Draw hand skeleton on frame.
        
        Args:
            frame: Input video frame
            landmarks: Hand landmarks (21 x 2, normalized 0-1)
            connections: List of landmark pairs to connect
            color: RGB color for drawing
            
        Returns:
            Frame with drawn landmarks
        """
        if color is None:
            color = self.COLOR_HAND
        
        frame_h, frame_w = frame.shape[:2]
        
        # Draw connections first (lines)
        if connections:
            for start_idx, end_idx in connections:
                if start_idx < len(landmarks) and end_idx < len(landmarks):
                    start = landmarks[start_idx]
                    end = landmarks[end_idx]
                    
                    x1, y1 = int(start[0] * frame_w), int(start[1] * frame_h)
                    x2, y2 = int(end[0] * frame_w), int(end[1] * frame_h)
                    
                    cv2.line(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw landmarks (circles)
        for i, landmark in enumerate(landmarks):
            x, y = int(landmark[0] * frame_w), int(landmark[1] * frame_h)
            cv2.circle(frame, (x, y), 5, color, -1)
            
            # Draw landmark index
            cv2.putText(
                frame, str(i), (x + 5, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1
            )
        
        return frame
    
    def draw_face_landmarks(
        self,
        frame: np.ndarray,
        landmarks: np.ndarray,
        color: Tuple[int, int, int] = None
    ) -> np.ndarray:
        """
        Draw face landmarks on frame.
        
        Args:
            frame: Input video frame
            landmarks: Face landmarks (N x 2, normalized 0-1)
            color: RGB color for drawing
            
        Returns:
            Frame with drawn landmarks
        """
        if color is None:
            color = self.COLOR_FACE
        
        frame_h, frame_w = frame.shape[:2]
        
        for landmark in landmarks:
            x, y = int(landmark[0] * frame_w), int(landmark[1] * frame_h)
            cv2.circle(frame, (x, y), 3, color, -1)
        
        return frame
    
    def draw_gesture_status(
        self,
        frame: np.ndarray,
        gesture_states: Dict[str, Any],
        position: Tuple[int, int] = (10, 30)
    ) -> np.ndarray:
        """
        Draw gesture status text on frame.
        
        Args:
            frame: Input video frame
            gesture_states: Dict of gesture names to their current states
            position: (x, y) top-left position for text
            
        Returns:
            Frame with status text
        """
        y_offset = position[1]
        
        for gesture_name, state_info in gesture_states.items():
            state = state_info.get("state", "idle")
            
            # Choose color based on state
            if state == "detected":
                color = self.COLOR_SUCCESS
                text = f"✓ {gesture_name.upper()}: {state}"
            elif state == "in_progress":
                color = self.COLOR_GESTURE_ACTIVE
                text = f"→ {gesture_name.upper()}: {state}"
            else:
                color = self.COLOR_GESTURE_INACTIVE
                text = f"  {gesture_name.upper()}: {state}"
            
            cv2.putText(
                frame, text, (position[0], y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
            )
            y_offset += 30
        
        return frame
    
    def draw_threshold_lines(
        self,
        frame: np.ndarray,
        swipe_threshold: int,
        scroll_threshold: int
    ) -> np.ndarray:
        """
        Draw visual thresholds for swipe and scroll gestures.
        
        Args:
            frame: Input video frame
            swipe_threshold: Minimum x-movement for swipe (pixels)
            scroll_threshold: Minimum y-movement for scroll (pixels)
            
        Returns:
            Frame with threshold lines
        """
        frame_h, frame_w = frame.shape[:2]
        
        # Vertical lines for swipe thresholds (left and right)
        left_line_x = frame_w // 2 - swipe_threshold
        right_line_x = frame_w // 2 + swipe_threshold
        
        cv2.line(frame, (left_line_x, 0), (left_line_x, frame_h),
                self.COLOR_WARNING, 1)
        cv2.line(frame, (right_line_x, 0), (right_line_x, frame_h),
                self.COLOR_WARNING, 1)
        
        # Horizontal lines for scroll thresholds (up and down)
        top_line_y = frame_h // 2 - scroll_threshold
        bottom_line_y = frame_h // 2 + scroll_threshold
        
        cv2.line(frame, (0, top_line_y), (frame_w, top_line_y),
                self.COLOR_WARNING, 1)
        cv2.line(frame, (0, bottom_line_y), (frame_w, bottom_line_y),
                self.COLOR_WARNING, 1)
        
        return frame
    
    def draw_hand_distance(
        self,
        frame: np.ndarray,
        hand1_pos: Tuple[float, float],
        hand2_pos: Tuple[float, float],
        distance: float,
        clap_threshold: float
    ) -> np.ndarray:
        """
        Draw line between hands and distance indicator (for clap gesture).
        
        Args:
            frame: Input video frame
            hand1_pos: First hand position (normalized 0-1)
            hand2_pos: Second hand position (normalized 0-1)
            distance: Distance between hands (meters)
            clap_threshold: Clap distance threshold (meters)
            
        Returns:
            Frame with distance visualization
        """
        frame_h, frame_w = frame.shape[:2]
        
        x1 = int(hand1_pos[0] * frame_w)
        y1 = int(hand1_pos[1] * frame_h)
        x2 = int(hand2_pos[0] * frame_w)
        y2 = int(hand2_pos[1] * frame_h)
        
        # Choose color based on if within clap distance
        color = self.COLOR_WARNING if distance < clap_threshold else self.COLOR_GESTURE_INACTIVE
        
        cv2.line(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw distance text
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        text = f"{distance:.2f}m"
        cv2.putText(
            frame, text, (mid_x, mid_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
        )
        
        return frame
    
    def draw_head_tilt_indicator(
        self,
        frame: np.ndarray,
        head_angle: float,
        angle_threshold: float,
        scroll_direction: Optional[str] = None
    ) -> np.ndarray:
        """
        Draw head tilt angle and scroll direction indicator.
        
        Args:
            frame: Input video frame
            head_angle: Current head tilt angle (degrees)
            angle_threshold: Threshold angle for scroll trigger
            scroll_direction: "up", "down", or None
            
        Returns:
            Frame with head tilt indicator
        """
        frame_h, frame_w = frame.shape[:2]
        center_x = frame_w // 2
        center_y = 50
        
        # Draw angle arc
        cv2.putText(
            frame, f"Head Angle: {head_angle:.1f}°", (center_x - 100, center_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.COLOR_FACE, 2
        )
        
        # Draw threshold indicator
        threshold_text = f"Threshold: ±{angle_threshold:.1f}°"
        color = self.COLOR_WARNING if abs(head_angle) >= angle_threshold else self.COLOR_GESTURE_INACTIVE
        cv2.putText(
            frame, threshold_text, (center_x - 100, center_y + 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
        )
        
        # Draw scroll direction if active
        if scroll_direction:
            direction_text = f"Scrolling: {scroll_direction.upper()}"
            cv2.putText(
                frame, direction_text, (center_x - 100, center_y + 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.COLOR_SUCCESS, 2
            )
        
        return frame
    
    def draw_gaze_indicator(
        self,
        frame: np.ndarray,
        gaze_valid: bool,
        gaze_angle: Optional[float] = None
    ) -> np.ndarray:
        """
        Draw eye gaze validation indicator.
        
        Args:
            frame: Input video frame
            gaze_valid: Whether gaze is valid (looking at screen)
            gaze_angle: Gaze angle if available
            
        Returns:
            Frame with gaze indicator
        """
        frame_h, frame_w = frame.shape[:2]
        
        if gaze_valid:
            status = "✓ Eyes on Screen"
            color = self.COLOR_SUCCESS
        else:
            status = "✗ Look at Screen"
            color = self.COLOR_ERROR
        
        cv2.putText(
            frame, status, (10, frame_h - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
        )
        
        if gaze_angle is not None:
            # Handle both tuple and float
            angle_val = gaze_angle[0] if isinstance(gaze_angle, (tuple, list)) else gaze_angle
            angle_text = f"Angle: {angle_val:.1f}°"
            cv2.putText(
                frame, angle_text, (10, frame_h - 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1
            )
        
        return frame
    
    def draw_fps(
        self,
        frame: np.ndarray,
        fps: float,
        position: Tuple[int, int] = (10, 30)
    ) -> np.ndarray:
        """
        Draw FPS counter on frame.
        
        Args:
            frame: Input video frame
            fps: Current frames per second
            position: (x, y) position for text
            
        Returns:
            Frame with FPS text
        """
        text = f"FPS: {fps:.1f}"
        cv2.putText(
            frame, text, position,
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.COLOR_SUCCESS, 2
        )
        return frame
