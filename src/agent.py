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
import argparse
import signal

# Use PyObjC for native macOS scrolling
try:
    from AppKit import NSEvent, NSApplication
    from Cocoa import NSEventTypeScrollWheel
    NATIVE_SCROLL_AVAILABLE = True
except:
    NATIVE_SCROLL_AVAILABLE = False

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DETECTION


class MacOSController:
    """Native macOS automation using PyObjC for true scrolling."""
    
    @staticmethod
    def scroll_pixels(delta_y_pixels: float) -> None:
        """Scroll the active window by a pixel delta (positive=down, negative=up)."""
        # Preferred: native scroll wheel event (smooth + continuous)
        if NATIVE_SCROLL_AVAILABLE:
            try:
                # Typical mouse wheel: positive delta_y scrolls down (content moves up)
                ev = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                    NSEventTypeScrollWheel, (0, 0), 0, 0, 0, None, 0, 0, int(delta_y_pixels), 0
                )
                NSApplication.sharedApplication().postEvent_atStart_(ev, True)
                return
            except:
                # Fall through to AppleScript fallback
                pass

        # Fallback: smaller increments using arrow keys (less jumpy than PageUp/PageDown)
        try:
            # Down scroll = Arrow Down, Up scroll = Arrow Up
            key_code = 125 if delta_y_pixels > 0 else 126
            presses = int(min(12, max(1, abs(delta_y_pixels) / 12)))
            script = f'''
            tell application "System Events"
                repeat {presses} times
                    key code {key_code}
                end repeat
            end tell
            '''
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=1)
        except:
            pass

    @staticmethod
    def scroll(direction: str, amount: int = 5) -> None:
        """Backward-compatible discrete scroll (kept for older call sites)."""
        delta = -120 if direction == "UP" else 120
        for _ in range(max(1, int(amount))):
            MacOSController.scroll_pixels(delta)
            time.sleep(0.01)
    
    @staticmethod  
    def switch_tab(direction):
        """Switch Chrome tab using Cmd+Option+Arrow."""
        try:
            # Use AppleScript to switch tabs in the frontmost app
            if direction == "LEFT":
                # Next tab
                script = '''
                tell application "System Events"
                    key code 124 using {command down, option down}
                end tell
                '''
            else:
                # Previous tab
                script = '''
                tell application "System Events"
                    key code 123 using {command down, option down}
                end tell
                '''
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=1)
            time.sleep(0.1)
        except:
            pass  # Silently fail


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
        # Runtime flags (set by create_from_args)
        self.headless = False
        self.quiet = False

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

        # Clap
        self.clap_history = deque(maxlen=3)  # Track last 3 hand distances
        self.clap_threshold = 0.15  # Distance between hands for clap detection
        self.clap_cooldown = 0
        self.clap_cooldown_time = 0.5

    # Swipe
    self.swipe_start_pos = {}  # legacy (kept)
    self.swipe_threshold = 0.15  # legacy (kept)
    self.swipe_cooldown = 0
    self.swipe_cooldown_time = 1.0  # seconds
    self.swipe_min_frames = 3  # frames of consistent motion before firing
    self.swipe_state = {}  # per hand: {"anchor": np.ndarray, "ema": np.ndarray, "dir": str, "frames": int}
    self.swipe_anchor_reset_distance = 0.20  # if hand recenters/jumps, reset anchor
    self.swipe_velocity_ema = {}  # per hand smoothed dx/dt in normalized units
    self.swipe_intent_until = {}  # per hand time until which we consider the user "swiping"
    self.swipe_intent_timeout = 0.7  # seconds
    self.swipe_min_speed = 0.75  # normalized units per second required to count as a swipe

    # Scroll (smooth)
    self.scroll_start_pos = {}
    self.scroll_threshold = 0.1  # legacy (kept)
    self.scroll_cooldown = 0
    self.scroll_cooldown_time = 0.3  # legacy (kept)
    self.scroll_ema = {}  # per-hand smoothed pinch point
    self.scroll_last_time = {}  # per-hand last scroll timestamp
    self.scroll_last_pos = {}  # per-hand last smoothed pinch position
    self.scroll_vel_ema = {}  # per-hand smoothed dy/dt (normalized/sec)
    self.scroll_pixel_per_norm_per_s = 1400.0  # pixels per normalized/sec
    self.scroll_deadzone = 0.0035
    self.scroll_max_step_pixels = 90
    self.scroll_rate_hz = 120.0
    self.scroll_vel_alpha = 0.35
    self.scroll_intent_until = {}  # per hand time until which we consider the user "scrolling"
    self.scroll_intent_timeout = 0.5

    # Tab selection by finger count
    self.number_last = {}  # per-hand last stable count
    self.number_frames = {}  # per-hand consecutive frames stable
    self.number_stable_frames = 6
    self.number_hold_start = {}  # per-hand hold start time for current count
    self.number_hold_required = 1.0  # seconds finger count must be held
    self.number_cooldown = {}  # per-hand cooldown timestamp
    self.number_cooldown_time = 0.7
    self.post_swipe_number_block_until = {}  # per-hand time until which number switching is blocked
    self.post_swipe_number_block_time = 1.1

    print(f"✓ Camera initialized ({self.width}x{self.height})")
    print("\n📋 CONTROLS:")
    print("  • 👏 CLAP TWICE: Toggle on/off")
    print("  • 👆 POINT: Hover over tabs")
    print("  • 🔄 SWIPE: Change windows (left/right)")
    print("  • 📌 1-5 FINGERS: Jump to that tab number (hold 1s)")
    print("  • 📜 PINCH + MOVE: Smooth scroll (up/down)")
    print("  • 'q': Quit\n")

    @classmethod
    def create_from_args(cls):
        """Create a tracker instance from command-line arguments."""
        parser = argparse.ArgumentParser(description="Sideswipe hand gesture agent")
        parser.add_argument("--headless", action="store_true", help="Run without preview window (background mode)")
        parser.add_argument("--quiet", action="store_true", help="Reduce console output")
        args = parser.parse_args()

        self = cls()
        self.headless = bool(args.headless)
        self.quiet = bool(args.quiet)
        return self

    def _log(self, msg: str) -> None:
        if not getattr(self, "quiet", False):
            print(msg)

    def _count_extended_fingers(self, landmarks: np.ndarray) -> int:
        """Count extended fingers (1-5) using simple tip-vs-pip y comparison.

        Notes:
        - Assumes camera feed is not rotated.
        - Works best for a roughly upright hand; good enough for tab selection.
        """

        def extended(tip: int, pip: int) -> bool:
            return landmarks[tip][1] < landmarks[pip][1]

        count = 0
        # Index, middle, ring, pinky
        if extended(self.INDEX_TIP, 6):
            count += 1
        if extended(self.MIDDLE_TIP, 10):
            count += 1
        if extended(self.RING_TIP, 14):
            count += 1
        if extended(self.PINKY_TIP, 18):
            count += 1

        # Thumb: use x comparison relative to index MCP, handles left/right reasonably
        thumb_tip = landmarks[self.THUMB_TIP]
        index_mcp = landmarks[5]
        if thumb_tip[0] < index_mcp[0] - 0.02 or thumb_tip[0] > index_mcp[0] + 0.02:
            count += 1

        return max(0, min(5, count))

    def detect_number_tab(self, hand):
        """Detect stable finger-count (1-5) and return a tab index (1-based).

        Behavior:
        - Requires a stable count AND a hold duration (to prevent accidental switches)
        - Disabled while pinching (scroll) and briefly after a swipe fires
        """
        hand_id = hand['handedness']
        landmarks = hand['landmarks']

        now = time.time()
        # If user is actively swiping or scrolling, don't interpret fingers as a tab-hold
        if now < self.swipe_intent_until.get(hand_id, 0.0):
            self.number_frames[hand_id] = 0
            self.number_hold_start.pop(hand_id, None)
            return None
        if now < self.scroll_intent_until.get(hand_id, 0.0):
            self.number_frames[hand_id] = 0
            self.number_hold_start.pop(hand_id, None)
            return None

        if now < self.post_swipe_number_block_until.get(hand_id, 0.0):
            self.number_frames[hand_id] = 0
            self.number_hold_start.pop(hand_id, None)
            return None

        # Don't trigger number selection while pinching (reserved for scroll)
        thumb_tip = landmarks[self.THUMB_TIP]
        index_tip = landmarks[self.INDEX_TIP]
        if np.linalg.norm(thumb_tip - index_tip) < 0.05:
            self.number_frames[hand_id] = 0
            self.number_hold_start.pop(hand_id, None)
            return None

        count = self._count_extended_fingers(landmarks)
        if count <= 0:
            self.number_frames[hand_id] = 0
            self.number_hold_start.pop(hand_id, None)
            return None

        last = self.number_last.get(hand_id)
        if last == count:
            self.number_frames[hand_id] = self.number_frames.get(hand_id, 0) + 1
        else:
            self.number_last[hand_id] = count
            self.number_frames[hand_id] = 1
            self.number_hold_start[hand_id] = now

        if self.number_frames[hand_id] < self.number_stable_frames:
            return None

        # Start hold timer the moment the count becomes stable
        if hand_id not in self.number_hold_start:
            self.number_hold_start[hand_id] = now

        if (now - self.number_hold_start[hand_id]) < self.number_hold_required:
            return None

        if now < self.number_cooldown.get(hand_id, 0):
            return None

        self.number_cooldown[hand_id] = now + self.number_cooldown_time
        self.number_frames[hand_id] = 0
        self.number_hold_start.pop(hand_id, None)
        return count
    
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
        """Detect swipe gesture (horizontal hand movement, but NOT while pinching)."""
        hand_id = hand['handedness']
        landmarks = hand['landmarks']
        center = self.get_hand_center(landmarks)
        
        # Check if we're pinching - if so, don't swipe
        thumb_tip = landmarks[self.THUMB_TIP]
        index_tip = landmarks[self.INDEX_TIP]
        thumb_index_distance = np.linalg.norm(thumb_tip - index_tip)
        
        if thumb_index_distance < 0.06:  # If pinching, don't swipe
            if hand_id in self.swipe_start_pos:
                del self.swipe_start_pos[hand_id]
            if hand_id in self.swipe_state:
                del self.swipe_state[hand_id]
            return None

        # Initialize per-hand swipe state
        if hand_id not in self.swipe_state:
            self.swipe_state[hand_id] = {
                "anchor": center,
                "ema": center,
                "dir": None,
                "frames": 0,
            }
            return None

        st = self.swipe_state[hand_id]

        # Smooth center using EMA to reduce jitter
        alpha = 0.30
        st["ema"] = (1 - alpha) * st["ema"] + alpha * center

        now = time.time()
        last_t = st.get("t")
        if last_t is None:
            st["t"] = now
            st["ema_prev"] = np.array(st["ema"], dtype=float)
            return None

        dt = max(1e-3, now - float(last_t))
        ema_prev = st.get("ema_prev", st["ema"])
        vel = (st["ema"] - ema_prev) / dt
        st["ema_prev"] = np.array(st["ema"], dtype=float)
        st["t"] = now

        # Track swipe intent using smoothed horizontal velocity
        v_prev = self.swipe_velocity_ema.get(hand_id, 0.0)
        v_x = float(vel[0])
        v_ema = 0.6 * v_prev + 0.4 * v_x
        self.swipe_velocity_ema[hand_id] = v_ema

        if abs(v_ema) >= self.swipe_min_speed:
            self.swipe_intent_until[hand_id] = now + self.swipe_intent_timeout

        # If the hand recenters or jumps a lot, reset anchor to avoid accidental swipe
        if np.linalg.norm(st["ema"] - st["anchor"]) > self.swipe_anchor_reset_distance:
            st["anchor"] = st["ema"]
            st["dir"] = None
            st["frames"] = 0
            return None

        delta = st["ema"] - st["anchor"]
        delta_x, delta_y = float(delta[0]), float(delta[1])

        # Horizontal-only constraint
        if abs(delta_y) > 0.09:
            st["dir"] = None
            st["frames"] = 0
            return None

        # Candidate direction
        if abs(delta_x) < 0.12:
            st["dir"] = None
            st["frames"] = 0
            return None

        candidate = "LEFT" if delta_x < 0 else "RIGHT"
        if st["dir"] == candidate:
            st["frames"] += 1
        else:
            st["dir"] = candidate
            st["frames"] = 1

        # Require both distance and speed intent to reduce shaky accidental swipes
        if st["frames"] >= self.swipe_min_frames and abs(self.swipe_velocity_ema.get(hand_id, 0.0)) >= self.swipe_min_speed:
            # Fire and reset anchor at current smoothed position
            st["anchor"] = st["ema"]
            st["dir"] = None
            st["frames"] = 0
            return candidate

        return None
    
    def detect_two_finger_scroll(self, hand):
        """Detect scroll gesture (pinching and moving up/down).

        Returns:
            float|None: signed normalized delta_y since last frame (positive=down).
        """
        hand_id = hand['handedness']
        landmarks = hand['landmarks']
        
        # Get index and middle finger tips
        index_tip = landmarks[self.INDEX_TIP]
        thumb_tip = landmarks[self.THUMB_TIP]
        
        # First check: are we pinching (thumb and index close together)?
        thumb_index_distance = np.linalg.norm(thumb_tip - index_tip)
        pinch_threshold = 0.05
        
        if thumb_index_distance > pinch_threshold:
            # Not pinching, so no scroll
            if hand_id in self.scroll_start_pos:
                del self.scroll_start_pos[hand_id]
            if hand_id in self.scroll_ema:
                del self.scroll_ema[hand_id]
            return None
        
        # We are pinching - now detect vertical movement
        # Calculate position of pinch point
        pinch_point = np.array([
            (index_tip[0] + thumb_tip[0]) / 2,
            (index_tip[1] + thumb_tip[1]) / 2
        ])
        
        # Smooth pinch point to reduce jitter
        if hand_id not in self.scroll_ema:
            self.scroll_ema[hand_id] = pinch_point
            self.scroll_start_pos[hand_id] = pinch_point
            self.scroll_last_pos[hand_id] = pinch_point
            self.scroll_last_time[hand_id] = time.time()
            return None

        alpha = 0.45
        self.scroll_ema[hand_id] = (1 - alpha) * self.scroll_ema[hand_id] + alpha * pinch_point

        now = time.time()
        prev_pos = self.scroll_last_pos.get(hand_id, self.scroll_ema[hand_id])
        prev_t = self.scroll_last_time.get(hand_id, now)
        dt = max(1e-3, now - float(prev_t))

        dy = float(self.scroll_ema[hand_id][1] - prev_pos[1])
        self.scroll_last_pos[hand_id] = np.array(self.scroll_ema[hand_id], dtype=float)
        self.scroll_last_time[hand_id] = now

        # Convert to velocity and smooth it. This gives more controllable scrolling.
        vel_y = dy / dt  # normalized/sec
        v_prev = self.scroll_vel_ema.get(hand_id, 0.0)
        v_ema = (1 - self.scroll_vel_alpha) * v_prev + self.scroll_vel_alpha * vel_y
        self.scroll_vel_ema[hand_id] = v_ema

        if abs(v_ema) < self.scroll_deadzone:
            return None

        # Mark scroll intent so tab-number hold can't steal intent
        self.scroll_intent_until[hand_id] = now + self.scroll_intent_timeout

        return v_ema
    
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
        self._log("🎥 Hand tracking started...\n")

        # Allow clean shutdown when run as a background service
        should_stop = {"stop": False}

        def _handle_stop(_sig, _frame):
            should_stop["stop"] = True

        signal.signal(signal.SIGINT, _handle_stop)
        signal.signal(signal.SIGTERM, _handle_stop)
        
        frame_count = 0
        fps_time = time.time()
        
        while True:
            if should_stop["stop"]:
                break

            ret, frame = self.cap.read()
            if not ret:
                self._log("Failed to read frame")
                break
            
            frame_count += 1
            
            # Update cooldowns
            self.clap_cooldown = max(0, self.clap_cooldown - 1/30)
            self.swipe_cooldown = max(0, self.swipe_cooldown - 1/30)
            self.scroll_cooldown = max(0, self.scroll_cooldown - 1/30)
            
            # Detect hands
            hands = self.detect_hands(frame)
            
            # Draw hands (only when not headless)
            if not self.headless:
                for hand in hands:
                    self.draw_hand(frame, hand)
            
            # Gesture detection
            if len(hands) >= 2:
                # Clap detection
                if self.clap_cooldown <= 0 and self.detect_clap(hands):
                    self.is_active = not self.is_active
                    status = "✓ ACTIVATED" if self.is_active else "✗ DEACTIVATED"
                    self._log(f"👏 CLAP DETECTED → {status}")
                    self.clap_cooldown = self.clap_cooldown_time
            
            # Single hand gestures
            for hand in hands:
                # Swipe detection
                if self.swipe_cooldown <= 0:
                    swipe_dir = self.detect_swipe(hand)
                    if swipe_dir:
                        self._log(f"🔄 SWIPE {swipe_dir}")
                        if self.is_active:
                            self.controller.switch_tab(swipe_dir)
                            time.sleep(0.1)
                        self.swipe_cooldown = self.swipe_cooldown_time
                        # Block finger-number switching briefly after a swipe so it can't override the swipe intent
                        self.post_swipe_number_block_until[hand['handedness']] = time.time() + self.post_swipe_number_block_time
                
                # Scroll detection
                v_ema = self.detect_two_finger_scroll(hand)
                if v_ema is not None and self.is_active:
                    now = time.time()
                    last = self.scroll_last_time.get(hand['handedness'], 0.0)
                    min_dt = 1.0 / self.scroll_rate_hz
                    if now - last >= min_dt:
                        self.scroll_last_time[hand['handedness']] = now
                        delta_px = float(v_ema) * self.scroll_pixel_per_norm_per_s * float(min_dt)
                        delta_px = float(np.clip(delta_px, -self.scroll_max_step_pixels, self.scroll_max_step_pixels))
                        self.controller.scroll_pixels(delta_px)

                # Number tab selection (stable finger count + 1s hold)
                tab_num = self.detect_number_tab(hand)
                if tab_num:
                    self._log(f"📌 TAB {tab_num}")
                    if self.is_active:
                        n = int(min(9, max(1, tab_num)))
                        key_code = 17 + n
                        script = f'''
                        tell application "System Events"
                            key code {key_code} using {{command down}}
                        end tell
                        '''
                        subprocess.run(['osascript', '-e', script], capture_output=True, timeout=1)
                        time.sleep(0.05)
            
            if not self.headless:
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
                    self._log(f"FPS: {fps:.1f} | Hands: {len(hands)} | Status: {'🟢 ACTIVE' if self.is_active else '🔴 INACTIVE'}")
                    fps_time = time.time()
                
                cv2.imshow("Hand Tracking", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
            else:
                # Headless: avoid busy loop if camera blocks less than expected
                if frame_count % 300 == 0:
                    # occasional heartbeat
                    self._log(f"Heartbeat | Hands: {len(hands)} | Status: {'🟢 ACTIVE' if self.is_active else '🔴 INACTIVE'}")

        self.cap.release()
        if not self.headless:
            cv2.destroyAllWindows()
        self._log("\n✓ Tracking stopped")


if __name__ == "__main__":
    backoff_s = 2
    max_backoff_s = 60
    while True:
        try:
            tracker = SimpleHandTracker.create_from_args()
            tracker.run()
            # If run() returns normally, treat as a clean exit.
            sys.exit(0)
        except Exception as e:
            # LaunchAgent + macOS TCC can block camera access in headless mode.
            # Don’t crash-loop: log the error and retry with exponential backoff.
            is_headless = any(arg in ("--headless", "--quiet") for arg in sys.argv)
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

            if not is_headless:
                sys.exit(1)

            time.sleep(backoff_s)
            backoff_s = min(max_backoff_s, backoff_s * 2)
