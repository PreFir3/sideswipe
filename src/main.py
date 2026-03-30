#!/usr/bin/env python3
"""
Sideswipe - Hand Gesture & Head Tracking Control System
Main entry point for real-time gesture recognition
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from detectors.hand import HandDetector
from detectors.face import FaceDetector
from gestures.swipe import SwipeDetector
from gestures.number import NumberDetector
from gestures.clap import ClapDetector
from gestures.head_tilt import HeadTiltDetector
from gestures.ok_hand import OKHandDetector
from gestures.finger_scroll import FingerScrollDetector
from utils.visualization import GestureVisualizer
from utils.frame_buffer import FrameBuffer
from system_control.browser import system_controller


class SideSwiperApp:
    """Main application class for Sideswipe gesture recognition system"""
    
    def __init__(self):
        """Initialize the Sideswipe application"""
        print("🚀 Initializing Sideswipe Gesture Control System...")
        
        # Initialize detectors
        self.hand_detector = HandDetector()
        self.face_detector = FaceDetector()
        
        # Initialize gesture recognizers
        self.swipe_detector = SwipeDetector()
        self.number_detector = NumberDetector()
        self.clap_detector = ClapDetector()
        self.head_tilt_detector = HeadTiltDetector()
        self.ok_hand_detector = OKHandDetector()
        self.finger_scroll_detector = FingerScrollDetector()
        
        # Initialize visualization
        self.visualizer = GestureVisualizer()
        
        # System state
        self.is_system_on = False
        self.current_window = 0
        self.current_tab = 1
        self.debug_mode = False
        self.calibration_frames = 0
        self.neutral_head_angle = None
        
        # Frame buffer for temporal filtering
        self.frame_buffer = FrameBuffer(max_size=DETECTION["frame_buffer_size"])
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, DETECTION["resolution_width"])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DETECTION["resolution_height"])
        self.cap.set(cv2.CAP_PROP_FPS, DETECTION["frame_rate"])
        
        if not self.cap.isOpened():
            raise RuntimeError("❌ Cannot access camera. Check permissions in System Preferences.")
        
        print("✓ Camera initialized")
        print("✓ Hand detector loaded")
        print("✓ Face detector loaded")
        print("✓ Gesture recognizers loaded")
        print("\n📋 Instructions:")
        print("  • Look straight at the camera for 3 seconds to calibrate")
        print("  • Controls: 'q'=quit, 'c'=recalibrate, 'd'=debug")
        print("\n🎯 Gestures:")
        print("  • Swipe Left/Right: Switch tabs")
        print("  • Hold Fingers (1-5): Switch tabs (1-5)")
        print("  • OK Hand Gesture: Turn system ON/OFF")
        print("  • Middle Finger Scroll: Scroll up/down")
        print("  • Keyboard: 'n'=new tab, 'w'=close tab, '<'=back, '>'=forward")
        print("\n" + "="*60)
        print("Starting system calibration... Look straight ahead!")
        print("="*60 + "\n")
    
    def calibrate_head_position(self, frame):
        """Calibrate neutral head position"""
        face = self.face_detector.detect(frame)
        
        if face.present:
            if self.neutral_head_angle is None:
                self.calibration_frames = 0
                self.neutral_head_angle = face.head_euler_angles[0]  # pitch
                print(f"📍 Calibration started. Hold still...")
            
            self.calibration_frames += 1
            
            if self.calibration_frames >= DETECTION["calibration_frames"]:
                self.neutral_head_angle = face.head_euler_angles[0]
                print(f"✓ Calibration complete! Neutral head angle: {self.neutral_head_angle:.1f}°")
                self.is_system_on = True
                return True
        
        return False
    
    def process_frame(self, frame):
        """Process a single frame and detect gestures"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect hands and face
        hand_detections = self.hand_detector.detect(frame_rgb)
        face = self.face_detector.detect(frame_rgb)
        
        # Filter out hands that are not actually detected (present=False)
        detected_hands = [h for h in hand_detections if h.present]
        
        # Draw detections
        frame_annotated = frame.copy()
        
        # Draw hand landmarks
        if VISUALIZATION["show_hand_landmarks"] and len(detected_hands) > 0:
            for hand in detected_hands:
                # Define hand skeleton connections (21 points, 20 connections)
                hand_connections = [
                    (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
                    (0, 5), (5, 6), (6, 7), (7, 8),      # Index
                    (0, 9), (9, 10), (10, 11), (11, 12), # Middle
                    (0, 13), (13, 14), (14, 15), (15, 16), # Ring
                    (0, 17), (17, 18), (18, 19), (19, 20)  # Pinky
                ]
                self.visualizer.draw_hand_landmarks(
                    frame_annotated, 
                    hand.landmarks,
                    connections=hand_connections
                )
        
        # Draw face landmarks
        if face.present and VISUALIZATION["show_face_landmarks"]:
            self.visualizer.draw_face_landmarks(frame_annotated, face.landmarks)
        
        # Process hand-based gestures
        ok_gesture_state = "NONE"
        if len(detected_hands) > 0:
            hand = detected_hands[0]
            # OK Hand gesture (system ON/OFF) - ALWAYS AVAILABLE
            ok_gesture = self.ok_hand_detector.detect(hand.landmarks)
            ok_gesture_state = ok_gesture.state.value if ok_gesture else "NONE"
            if ok_gesture.is_confirmed:
                self.is_system_on = not self.is_system_on
                status = "✓ System ON" if self.is_system_on else "✗ System OFF"
                print(f"→ OK Hand detected! {status}")
                self.ok_hand_detector.reset()
        
        # Process other gestures only when system is ON
        if self.is_system_on:
            # Process hand gestures
            if len(detected_hands) > 0:
                hand = detected_hands[0]
                swipe_gesture = self.swipe_detector.add_hand_position(
                    hand.landmarks[8][0]  # Index finger MCP
                )
                if swipe_gesture.is_confirmed:
                    print(f"→ Swipe {swipe_gesture.direction} detected!")
                    if swipe_gesture.direction == "left":
                        system_controller.switch_tab_left()
                    else:
                        system_controller.switch_tab_right()
                
                # Number selection
                number_gesture = self.number_detector.detect(hand)
                if number_gesture.is_confirmed:
                    print(f"→ Number {number_gesture.number} detected! Switching to Tab {number_gesture.number}")
                    system_controller.goto_tab(number_gesture.number)
                    self.current_tab = number_gesture.number
                
                # Finger scroll detection
                scroll_gesture = self.finger_scroll_detector.detect_from_landmarks(hand.landmarks)
                if scroll_gesture.is_active:
                    if scroll_gesture.direction.value == "up":
                        system_controller.scroll_up(FINGER_SCROLL["scroll_amount"])
                    elif scroll_gesture.direction.value == "down":
                        system_controller.scroll_down(FINGER_SCROLL["scroll_amount"])
                
                # Clap detection (needs 2 hands)
                if len(detected_hands) >= 2:
                    clap_gesture = self.clap_detector.add_hand_pair(
                        detected_hands[0].landmarks[9],  # Palm center 1
                        detected_hands[1].landmarks[9]   # Palm center 2
                    )
                    if clap_gesture.is_confirmed:
                        print(f"→ Clap detected! (currently disabled, use OK Hand instead)")
        
        # Draw status
        status_text = "🟢 ON" if self.is_system_on else "🔴 OFF"
        
        cv2.putText(frame_annotated, status_text, (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if self.is_system_on else (0, 0, 255), 2)
        cv2.putText(frame_annotated, f"OK: {ok_gesture_state}", (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame_annotated, f"Window: {self.current_window} | Tab: {self.current_tab}", (20, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw calibration progress
        if not self.is_system_on and self.neutral_head_angle is None:
            progress = self.calibration_frames / DETECTION["calibration_frames"]
            cv2.putText(frame_annotated, f"Calibrating... {int(progress*100)}%", (20, 160),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
        
        # Draw debug info
        if self.debug_mode:
            debug_y = 200
            cv2.putText(frame_annotated, "DEBUG MODE", (20, debug_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            debug_y += 30
            cv2.putText(frame_annotated, f"Hands detected: {len(detected_hands)}",
                       (20, debug_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            if face.present:
                debug_y += 25
                cv2.putText(frame_annotated, f"Head angle: {face.head_euler_angles[0]:.1f}°",
                           (20, debug_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Draw keyboard help
        cv2.putText(frame_annotated, "Press: q=quit | c=calibrate | d=debug", (20, DETECTION["resolution_height"]-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        return frame_annotated
    
    def run(self):
        """Main application loop"""
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to read frame from camera")
                    break
                
                # Calibrate on startup
                if self.neutral_head_angle is None:
                    if self.calibrate_head_position(frame):
                        pass  # Calibration complete
                
                # Process frame
                frame_out = self.process_frame(frame)
                
                # Display
                cv2.imshow("Sideswipe - Gesture Control", frame_out)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n👋 Shutting down Sideswipe...")
                    break
                elif key == ord('c'):
                    print("\n🔄 Recalibrating head position...")
                    self.neutral_head_angle = None
                    self.calibration_frames = 0
                elif key == ord('d'):
                    self.debug_mode = not self.debug_mode
                    print(f"🐛 Debug mode: {'ON' if self.debug_mode else 'OFF'}")
                # New keybinds for browser control
                elif key == ord('n'):
                    print("→ New tab")
                    system_controller.new_tab()
                elif key == ord('w'):
                    print("→ Close tab")
                    system_controller.close_tab()
                elif key == ord('<'):
                    print("→ Go back")
                    system_controller.go_back()
                elif key == ord('>'):
                    print("→ Go forward")
                    system_controller.go_forward()
        
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.cap.release()
        cv2.destroyAllWindows()
        print("✓ Resources cleaned up")
        print("✓ Goodbye! 👋\n")


def main():
    """Entry point"""
    try:
        app = SideSwiperApp()
        app.run()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
