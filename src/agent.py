"""
Sideswipe - Hand Gesture Tracking Agent
Stable hand tracking with native macOS automation
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import time
from collections import deque
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import subprocess
import os

# Use PyObjC for native macOS scrolling
try:
    from AppKit import NSEvent, NSApplication
    from Cocoa import NSEventTypeScrollWheel
    NATIVE_SCROLL_AVAILABLE = True
except:
    NATIVE_SCROLL_AVAILABLE = False

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DETECTION, NUMBER_SELECTION, FINGER_SCROLL
from gestures.finger_counting import count_extended_fingers
from gestures.pinch_scroll import PinchScrollTracker


class MacOSController:
    """Native macOS automation using pynput for smooth scrolling."""

    def __init__(self):
        # Initialize pynput mouse controller once for smooth scrolling
        try:
            from pynput.mouse import Controller as MouseController
            self.mouse = MouseController()
        except Exception:
            self.mouse = None

    def scroll(self, direction, amount=2):
        """Scroll using pynput mouse wheel for smooth, controllable scrolling."""
        try:
            if self.mouse:
                dy = amount if direction == "UP" else -amount
                self.mouse.scroll(0, dy)
        except Exception:
            pass

    @staticmethod
    def switch_tab(direction):
        """Switch Chrome tab using Cmd+Option+Arrow."""
        try:
            if direction == "LEFT":
                script = '''
                tell application "System Events"
                    key code 124 using {command down, option down}
                end tell
                '''
            else:
                script = '''
                tell application "System Events"
                    key code 123 using {command down, option down}
                end tell
                '''
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=1)
        except Exception:
            pass

    @staticmethod
    def goto_tab(number):
        """Navigate to a specific Chrome tab (1-9) using Cmd+Number."""
        try:
            script = f'''
            tell application "System Events"
                keystroke "{number}" using {{command down}}
            end tell
            '''
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=1)
        except Exception:
            pass


class SimpleHandTracker:
    """
    Stable hand tracking with MediaPipe.
    Tracks hands at any angle with gesture recognition.
    """
    
    # Landmark indices
    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20
    
    def __init__(self):
        """Initialize hand tracker with optimal MediaPipe settings."""
        print("🤖 Initializing Hand Tracker...")
        
        # Initialize MediaPipe hand detector
        model_path = "hand_landmarker.task"
        
        try:
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=2,
                min_hand_detection_confidence=0.6,
                min_hand_presence_confidence=0.6,
                min_tracking_confidence=0.5
            )
            self.hands = vision.HandLandmarker.create_from_options(options)
            print("✓ Hand detector initialized")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize hand detector: {e}")
        
        # Initialize macOS controller
        self.controller = MacOSController()
        print("✓ macOS control initialized")

        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, DETECTION["resolution_width"])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DETECTION["resolution_height"])
        self.cap.set(cv2.CAP_PROP_FPS, DETECTION["frame_rate"])

        if not self.cap.isOpened():
            raise RuntimeError("❌ Cannot access camera")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Gesture tracking state
        self.is_active = False
        self.clap_history = deque(maxlen=3)  # Track last 3 hand distances
        self.clap_threshold = 0.15  # Distance between hands for clap detection
        self.clap_cooldown = 0
        self.clap_cooldown_time = 0.5

        # Swipe tracking - with return-to-neutral logic
        self.swipe_start_pos = {}  # Track start position per hand
        self.swipe_threshold = 0.15  # Minimum swipe distance
        self.swipe_cooldown = 0
        self.swipe_cooldown_time = 1.0  # 1 second cooldown between swipes
        self.swipe_neutral_pos = {}  # Where hand was when swipe fired
        self.swipe_returning = {}  # True while hand is returning to neutral
        self.swipe_settle_threshold = 0.03  # Hand must be nearly still to re-arm
        self.swipe_prev_pos = {}  # Previous frame position for velocity check

        # Scroll tracking - tuned to ignore jitter and ramp in smoothly
        self.scroll_cooldown = 0
        self.scroll_cooldown_time = 0.0  # No cooldown - continuous smooth scrolling
        self.scroll_tracker = PinchScrollTracker(
            pinch_threshold=FINGER_SCROLL["pinch_threshold"],
            activation_frames=FINGER_SCROLL["activation_frames"],
            history_size=FINGER_SCROLL["history_size"],
            velocity_smoothing=FINGER_SCROLL["velocity_smoothing"],
            dead_zone=FINGER_SCROLL["dead_zone"],
            velocity_scale=FINGER_SCROLL["velocity_scale"],
            max_scroll_amount=FINGER_SCROLL["max_scroll_amount"],
        )

        # Number gesture tracking (1-5 fingers → Chrome tab)
        self.number_stability_frames = max(8, NUMBER_SELECTION["stabilization_frames"] // 2)
        self.number_history = deque(maxlen=self.number_stability_frames)
        self.number_cooldown = 0
        self.number_cooldown_time = NUMBER_SELECTION["cooldown"]
        self.last_confirmed_number = 0

        print(f"✓ Camera initialized ({self.width}x{self.height})")
        print("\n📋 CONTROLS:")
        print("  • 👏 CLAP TWICE: Toggle on/off")
        print("  • 👆 POINT: Hover over tabs")
        print("  • 🔄 SWIPE: Change windows (left/right)")
        print("  • 📜 PINCH+DRAG: Scroll (up/down)")
        print("  • ✋ 1-5 FINGERS: Jump to Chrome tab 1-5")
        print("  • 'q': Quit\n")
    
    def detect_hands(self, frame):
        """Detect hands in frame."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        results = self.hands.detect(mp_image)
        
        hands = []
        if results.hand_landmarks:
            for i, hand_landmarks in enumerate(results.hand_landmarks):
                landmarks = np.array([
                    [lm.x, lm.y] for lm in hand_landmarks
                ])
                
                # Get handedness safely
                handedness_name = "Unknown"
                confidence = 0.0
                if results.handedness and i < len(results.handedness):
                    hand_info = results.handedness[i]
                    if hasattr(hand_info, '__iter__') and len(hand_info) > 0:
                        handedness_name = hand_info[0].category_name
                        confidence = hand_info[0].score
                    elif hasattr(hand_info, 'category_name'):
                        handedness_name = hand_info.category_name
                        confidence = hand_info.score
                
                hands.append({
                    'landmarks': landmarks,
                    'handedness': handedness_name,
                    'confidence': confidence
                })
        
        return hands
    
    def get_hand_center(self, landmarks):
        """Get center of hand (palm area)."""
        palm_landmarks = landmarks[5:10]
        center_x = np.mean(palm_landmarks[:, 0])
        center_y = np.mean(palm_landmarks[:, 1])
        return np.array([center_x, center_y])
    
    def detect_clap(self, hands):
        """Detect clap gesture (two hands close together)."""
        if len(hands) < 2:
            return False
        
        center1 = self.get_hand_center(hands[0]['landmarks'])
        center2 = self.get_hand_center(hands[1]['landmarks'])
        distance = np.linalg.norm(center1 - center2)
        
        self.clap_history.append(distance)
        
        # Detect clap: distance decreases then increases (hands clapping)
        if len(self.clap_history) >= 3:
            prev_dist = self.clap_history[-3]
            curr_dist = self.clap_history[-1]
            
            # If distance is small and was decreasing
            if curr_dist < self.clap_threshold and prev_dist > curr_dist:
                return True
        
        return False
    
    def detect_swipe(self, hand):
        """Detect swipe gesture with return-to-neutral logic.

        After a swipe fires, the detector enters a 'returning' state where it
        ignores hand movement until the hand settles (stops moving). This prevents
        the hand drifting back to center from triggering a reverse swipe.
        """
        hand_id = hand['handedness']
        landmarks = hand['landmarks']
        center = self.get_hand_center(landmarks)

        # Check if we're pinching - if so, don't swipe
        thumb_tip = landmarks[self.THUMB_TIP]
        index_tip = landmarks[self.INDEX_TIP]
        thumb_index_distance = np.linalg.norm(thumb_tip - index_tip)

        if thumb_index_distance < 0.06:  # If pinching, don't swipe
            self.swipe_start_pos.pop(hand_id, None)
            self.swipe_returning.pop(hand_id, None)
            self.swipe_prev_pos.pop(hand_id, None)
            return None

        # Calculate hand velocity (frame-to-frame movement)
        prev = self.swipe_prev_pos.get(hand_id)
        self.swipe_prev_pos[hand_id] = center.copy()
        if prev is None:
            return None
        frame_velocity = np.linalg.norm(center - prev)

        # RETURN-TO-NEUTRAL PHASE: after a swipe, wait for hand to settle
        if self.swipe_returning.get(hand_id, False):
            # Hand is settled when it's barely moving
            if frame_velocity < self.swipe_settle_threshold:
                # Hand is still - re-arm the detector
                self.swipe_returning[hand_id] = False
                self.swipe_start_pos[hand_id] = center.copy()
            # Still returning - don't detect any swipe
            return None

        # Normal swipe detection
        if hand_id not in self.swipe_start_pos:
            self.swipe_start_pos[hand_id] = center.copy()
            return None

        start = self.swipe_start_pos[hand_id]
        delta_x = center[0] - start[0]
        delta_y = center[1] - start[1]

        if abs(delta_x) > 0.1 and abs(delta_y) < 0.08:
            direction = "LEFT" if delta_x < -0.1 else "RIGHT"
            # Enter return-to-neutral phase instead of immediately re-arming
            self.swipe_returning[hand_id] = True
            self.swipe_start_pos.pop(hand_id, None)
            return direction

        return None
    
    def detect_two_finger_scroll(self, hand):
        """Detect scroll gesture with smooth velocity-proportional output.

        Returns (direction, scroll_amount) tuple or None.
        The scroll amount scales with how fast/far you move your pinched fingers,
        giving fine-grained control and smooth visual scrolling.
        """
        hand_id = hand['handedness']
        landmarks = hand['landmarks']

        index_tip = landmarks[self.INDEX_TIP]
        thumb_tip = landmarks[self.THUMB_TIP]

        scroll_update = self.scroll_tracker.update(hand_id, thumb_tip, index_tip)
        if scroll_update is None:
            return None

        return (scroll_update.direction, scroll_update.amount)

    def count_fingers(self, hand):
        """Count clearly extended fingers for tab navigation.

        Uses a stricter thumb rule so "2 fingers" and "3 fingers" land on the
        matching numbered tab instead of drifting one tab higher.
        """
        return count_extended_fingers(
            hand["landmarks"],
            handedness=hand.get("handedness", "Unknown"),
            finger_tip_margin=NUMBER_SELECTION["finger_position_threshold"],
            thumb_horizontal_margin=NUMBER_SELECTION["thumb_horizontal_margin"],
            thumb_reach_margin=NUMBER_SELECTION["thumb_reach_margin"],
        )

    def detect_number_gesture(self, hand):
        """Detect stable finger count (1-5) for Chrome tab navigation.

        Returns confirmed number (1-5) or None if no stable gesture detected.
        Requires consistent count over multiple frames to avoid jitter.
        Resets when hand returns to fist so the same tab can be re-selected.
        """
        count = self.count_fingers(hand)

        # Fist (0 fingers) resets state so same tab can be triggered again
        if count == 0:
            self.number_history.clear()
            self.last_confirmed_number = 0
            return None

        # Only track 1-5
        if count < 1 or count > 5:
            self.number_history.clear()
            return None

        self.number_history.append(count)

        # Need enough frames for stability
        if len(self.number_history) < self.number_stability_frames:
            return None

        # Check if the recent window is stable
        recent = list(self.number_history)[-self.number_stability_frames:]
        if all(n == recent[0] for n in recent):
            confirmed = recent[0]
            # Only fire if different from last confirmed (prevent repeats)
            if confirmed != self.last_confirmed_number:
                self.last_confirmed_number = confirmed
                self.number_history.clear()
                return confirmed

        return None

    def detect_pointing(self, landmarks):
        """Detect pointing gesture (index finger extended)."""
        index_tip = landmarks[self.INDEX_TIP]
        index_pip = landmarks[6]
        middle_tip = landmarks[self.MIDDLE_TIP]
        middle_pip = landmarks[10]
        
        # Index extended, middle not extended
        index_extended = index_tip[1] < index_pip[1]
        middle_not_extended = middle_tip[1] > middle_pip[1]
        
        return index_extended and middle_not_extended
    
    def draw_hand(self, frame, hand):
        """Draw hand landmarks on frame."""
        landmarks = hand['landmarks']
        h, w = frame.shape[:2]
        
        # Draw connections
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12),
            (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20),
            (5, 9), (9, 13), (13, 17)
        ]
        
        for start, end in connections:
            x1, y1 = int(landmarks[start][0] * w), int(landmarks[start][1] * h)
            x2, y2 = int(landmarks[end][0] * w), int(landmarks[end][1] * h)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw landmarks
        for i, (x, y) in enumerate(landmarks):
            px, py = int(x * w), int(y * h)
            if i == 8:
                color = (0, 255, 255)  # Cyan - Index
            elif i == 12:
                color = (255, 0, 255)  # Magenta - Middle
            elif i == 4:
                color = (0, 255, 0)   # Green - Thumb
            else:
                color = (255, 0, 0)   # Blue
            
            cv2.circle(frame, (px, py), 4, color, -1)
    
    def run(self):
        """Main loop - track and display hands."""
        print("🎥 Hand tracking started...\n")
        
        frame_count = 0
        fps_time = time.time()
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                break
            
            frame_count += 1
            
            # Update cooldowns
            self.clap_cooldown = max(0, self.clap_cooldown - 1/30)
            self.swipe_cooldown = max(0, self.swipe_cooldown - 1/30)
            self.scroll_cooldown = max(0, self.scroll_cooldown - 1/30)
            self.number_cooldown = max(0, self.number_cooldown - 1/30)
            
            # Detect hands
            hands = self.detect_hands(frame)
            
            # Draw hands
            for hand in hands:
                self.draw_hand(frame, hand)
            
            # Gesture detection
            if len(hands) >= 2:
                # Clap detection
                if self.clap_cooldown <= 0 and self.detect_clap(hands):
                    self.is_active = not self.is_active
                    status = "✓ ACTIVATED" if self.is_active else "✗ DEACTIVATED"
                    print(f"👏 CLAP DETECTED → {status}")
                    self.clap_cooldown = self.clap_cooldown_time
            
            # Single hand gestures
            for hand in hands:
                # Swipe detection
                if self.swipe_cooldown <= 0:
                    swipe_dir = self.detect_swipe(hand)
                    if swipe_dir:
                        print(f"🔄 SWIPE {swipe_dir}")
                        if self.is_active:
                            self.controller.switch_tab(swipe_dir)
                            time.sleep(0.1)
                        self.swipe_cooldown = self.swipe_cooldown_time
                
                # Scroll detection (smooth, velocity-proportional)
                scroll_result = self.detect_two_finger_scroll(hand)
                if scroll_result:
                    scroll_dir, scroll_amount = scroll_result
                    if self.is_active:
                        self.controller.scroll(scroll_dir, scroll_amount)

                # Number gesture detection (1-5 fingers → Chrome tab 1-5)
                # Skip while hand is returning from a swipe to avoid false triggers
                hand_id = hand['handedness']
                if self.number_cooldown <= 0 and not self.swipe_returning.get(hand_id, False):
                    number = self.detect_number_gesture(hand)
                    if number is not None:
                        print(f"✋ {number} FINGER{'S' if number > 1 else ''} → Tab {number}")
                        if self.is_active:
                            self.controller.goto_tab(number)
                        self.number_cooldown = self.number_cooldown_time
            
            # Display status
            status_text = "🟢 ACTIVE" if self.is_active else "🔴 INACTIVE"
            status_color = (0, 255, 0) if self.is_active else (0, 0, 255)
            cv2.putText(frame, status_text, (self.width - 200, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
            
            # Display hand count
            if len(hands) > 0:
                cv2.putText(frame, f"Hands: {len(hands)}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           1, (0, 255, 0), 2)
            
            # Calculate FPS
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_time
                fps = 30 / elapsed
                print(f"FPS: {fps:.1f} | Hands: {len(hands)} | Status: {'🟢 ACTIVE' if self.is_active else '🔴 INACTIVE'}")
                fps_time = time.time()
            
            # Display frame
            cv2.imshow("Hand Tracking", frame)
            
            # Check for quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()
        print("\n✓ Tracking stopped")


if __name__ == "__main__":
    try:
        tracker = SimpleHandTracker()
        tracker.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
