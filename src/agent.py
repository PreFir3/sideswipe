"""
Sideswipe - Hand Gesture Tracking Agent
Enhanced with double-exponential smoothing, strict swipe gating,
FaceMesh integration, and gesture state machines.
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

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DETECTION, NUMBER_SELECTION, FINGER_SCROLL
from gestures.finger_counting import count_extended_fingers
from gestures.pinch_scroll import PinchScrollTracker
from gesture_engine import GestureEngine
from face_engine import FaceEngine


class MacOSController:
    """Native macOS automation using pynput for smooth scrolling."""

    def __init__(self):
        try:
            from pynput.mouse import Controller as MouseController
            self.mouse = MouseController()
        except Exception:
            self.mouse = None

    def scroll(self, direction, amount=2):
        """Scroll using pynput mouse wheel."""
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
        """Navigate to a specific Chrome tab (1-4) using Cmd+Number."""
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
    """Hand + face tracking with strict gesture gating.

    Architecture:
      - GestureEngine handles all smoothing and gesture state machines
      - FaceEngine handles FaceMesh metric extraction
      - This class owns the camera, MediaPipe models, and rendering
    """

    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20

    def __init__(self):
        print("Initializing Hand + Face Tracker...")

        # ── Engines ──
        self.gesture_engine = GestureEngine(alpha=0.12, beta=0.08)
        self.face_engine = FaceEngine()
        self.controller = MacOSController()

        # ── MediaPipe Hands (Tasks API) ──
        model_path = "hand_landmarker.task"
        try:
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=2,
                min_hand_detection_confidence=0.6,
                min_hand_presence_confidence=0.6,
                min_tracking_confidence=0.5,
            )
            self.hands = vision.HandLandmarker.create_from_options(options)
            print("  Hand detector ready")
        except Exception as e:
            raise RuntimeError(f"Failed to init hand detector: {e}")

        # ── MediaPipe FaceMesh (Solutions API) ──
        try:
            mp_face = mp.solutions.face_mesh
            self.face_mesh = mp_face.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            print("  FaceMesh ready")
        except Exception as e:
            print(f"  FaceMesh unavailable: {e}")
            self.face_mesh = None

        # ── Camera ──
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, DETECTION["resolution_width"])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DETECTION["resolution_height"])
        self.cap.set(cv2.CAP_PROP_FPS, DETECTION["frame_rate"])

        if not self.cap.isOpened():
            raise RuntimeError("Cannot access camera")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"  Camera {self.width}x{self.height}")

        # ── Activation ──
        self.is_active = False
        self.clap_history = deque(maxlen=3)
        self.clap_cooldown = 0

        # ── Scroll (pinch) ──
        self.scroll_tracker = PinchScrollTracker(
            pinch_threshold=FINGER_SCROLL["pinch_threshold"],
            activation_frames=FINGER_SCROLL["activation_frames"],
            history_size=FINGER_SCROLL["history_size"],
            velocity_smoothing=FINGER_SCROLL["velocity_smoothing"],
            dead_zone=FINGER_SCROLL["dead_zone"],
            velocity_scale=FINGER_SCROLL["velocity_scale"],
            max_scroll_amount=FINGER_SCROLL["max_scroll_amount"],
        )

        # ── Per-frame state ──
        self.hand_was_present = False
        self.face_metrics = None

        print("\nCONTROLS:")
        print("  CLAP TWICE     : Toggle on/off")
        print("  FLAT HAND SWIPE: Switch tabs (left/right)")
        print("  PINCH + DRAG   : Scroll (up/down)")
        print("  HOLD 1-4 (vertical): Jump to Chrome tab 1-4")
        print("  'q'            : Quit\n")

    # ──────────────────────────────────────────
    #  Hand detection
    # ──────────────────────────────────────────
    def detect_hands(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        results = self.hands.detect(mp_image)

        hands = []
        if results.hand_landmarks:
            for i, hand_landmarks in enumerate(results.hand_landmarks):
                landmarks = np.array([[lm.x, lm.y] for lm in hand_landmarks])

                handedness_name = "Unknown"
                confidence = 0.0
                if results.handedness and i < len(results.handedness):
                    info = results.handedness[i]
                    if hasattr(info, '__iter__') and len(info) > 0:
                        handedness_name = info[0].category_name
                        confidence = info[0].score
                    elif hasattr(info, 'category_name'):
                        handedness_name = info.category_name
                        confidence = info.score

                hands.append({
                    'landmarks': landmarks,
                    'handedness': handedness_name,
                    'confidence': confidence,
                })
        return hands

    # ──────────────────────────────────────────
    #  Face detection
    # ──────────────────────────────────────────
    def detect_face(self, frame):
        """Run FaceMesh and update face_engine metrics."""
        if self.face_mesh is None:
            return None

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.face_mesh.process(rgb)

        if results.multi_face_landmarks:
            face_lm = results.multi_face_landmarks[0].landmark
            self.face_metrics = self.face_engine.process(face_lm)
            return self.face_metrics
        return None

    # ──────────────────────────────────────────
    #  Gesture helpers (delegated)
    # ──────────────────────────────────────────
    def get_hand_center(self, landmarks):
        return np.mean(landmarks[5:10], axis=0)

    def detect_clap(self, hands):
        if len(hands) < 2:
            return False
        c1 = self.get_hand_center(hands[0]['landmarks'])
        c2 = self.get_hand_center(hands[1]['landmarks'])
        dist = np.linalg.norm(c1 - c2)
        self.clap_history.append(dist)
        if len(self.clap_history) >= 3:
            if self.clap_history[-1] < 0.15 and self.clap_history[-3] > self.clap_history[-1]:
                return True
        return False

    def count_fingers(self, hand):
        return count_extended_fingers(
            hand['landmarks'],
            handedness=hand.get('handedness', 'Unknown'),
            finger_tip_margin=NUMBER_SELECTION["finger_position_threshold"],
            thumb_horizontal_margin=NUMBER_SELECTION["thumb_horizontal_margin"],
            thumb_reach_margin=NUMBER_SELECTION["thumb_reach_margin"],
        )

    def detect_pinch_scroll(self, hand):
        hand_id = hand['handedness']
        landmarks = hand['landmarks']
        update = self.scroll_tracker.update(
            hand_id, landmarks[self.THUMB_TIP], landmarks[self.INDEX_TIP]
        )
        if update is None:
            return None
        return (update.direction, update.amount)

    # ──────────────────────────────────────────
    #  Drawing
    # ──────────────────────────────────────────
    def draw_hand(self, frame, landmarks):
        h, w = frame.shape[:2]
        connections = [
            (0,1),(1,2),(2,3),(3,4),
            (0,5),(5,6),(6,7),(7,8),
            (0,9),(9,10),(10,11),(11,12),
            (0,13),(13,14),(14,15),(15,16),
            (0,17),(17,18),(18,19),(19,20),
            (5,9),(9,13),(13,17),
        ]
        for a, b in connections:
            p1 = (int(landmarks[a][0]*w), int(landmarks[a][1]*h))
            p2 = (int(landmarks[b][0]*w), int(landmarks[b][1]*h))
            cv2.line(frame, p1, p2, (0, 255, 0), 2)

        for i in range(21):
            px = int(landmarks[i][0]*w)
            py = int(landmarks[i][1]*h)
            color = {4:(0,255,0), 8:(0,255,255), 12:(255,0,255)}.get(i, (255,0,0))
            cv2.circle(frame, (px, py), 4, color, -1)

    def draw_face_hud(self, frame):
        """Draw a small face-metrics HUD in the top-left corner."""
        if self.face_metrics is None:
            return

        m = self.face_metrics
        x0, y0 = 10, 10
        lh = 20  # line height
        bg_h = lh * 7 + 10
        bg_w = 260

        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (x0, y0), (x0 + bg_w, y0 + bg_h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        def put(line, text, color=(200, 200, 200)):
            cv2.putText(frame, text, (x0 + 8, y0 + 18 + line * lh),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

        put(0, "FACEMESH", (0, 200, 255))

        blink_l = "BLINK" if m['blink_left'] else ""
        blink_r = "BLINK" if m['blink_right'] else ""
        put(1, f"L Eye: {m['ear_left']:.2f} {blink_l}",
            (0, 0, 255) if m['blink_left'] else (200, 200, 200))
        put(2, f"R Eye: {m['ear_right']:.2f} {blink_r}",
            (0, 0, 255) if m['blink_right'] else (200, 200, 200))

        mouth_s = "OPEN" if m['mouth_open'] else ""
        put(3, f"Mouth: {m['mouth_openness']:.2f} {mouth_s}",
            (0, 255, 0) if m['mouth_open'] else (200, 200, 200))

        put(4, f"Tilt:  {m['head_tilt']:.1f} deg")

        brow_s = "RAISED" if m['brow_raised'] else ""
        put(5, f"Brows: {m['brow_raise']:.2f} {brow_s}",
            (0, 255, 0) if m['brow_raised'] else (200, 200, 200))

    # ──────────────────────────────────────────
    #  Main loop
    # ──────────────────────────────────────────
    def run(self):
        print("Hand + face tracking started...\n")

        frame_count = 0
        fps_time = time.time()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                break

            frame_count += 1
            dt = 1 / 30
            self.clap_cooldown = max(0, self.clap_cooldown - dt)

            # ── Detect hands ──
            hands = self.detect_hands(frame)

            # ── Detect face (runs in parallel with hand processing) ──
            self.detect_face(frame)

            # ── Process hands ──
            hand_present = len(hands) > 0

            if not hand_present and self.hand_was_present:
                self.gesture_engine.on_hand_lost()
            self.hand_was_present = hand_present

            # ── Clap detection (2 hands) ──
            if len(hands) >= 2 and self.clap_cooldown <= 0:
                if self.detect_clap(hands):
                    self.is_active = not self.is_active
                    status = "ACTIVATED" if self.is_active else "DEACTIVATED"
                    print(f"CLAP -> {status}")
                    self.clap_cooldown = 0.5

            # ── Single-hand gestures ──
            for hand in hands:
                raw_lm = hand['landmarks']

                # Smooth landmarks through GestureEngine
                smoothed = self.gesture_engine.smooth(raw_lm)

                # Draw smoothed skeleton
                self.draw_hand(frame, smoothed)

                # ── SWIPE (horizontal hand only) ──
                swipe_dir = self.gesture_engine.process_swipe(smoothed)
                if swipe_dir:
                    print(f"SWIPE {swipe_dir} [{self.gesture_engine.swipe_state}]")
                    if self.is_active:
                        self.controller.switch_tab(swipe_dir)

                # ── FINGER COUNT (vertical hand only) ──
                if self.gesture_engine.is_hand_vertical(smoothed):
                    count = self.count_fingers(hand)
                    tab = self.gesture_engine.process_finger_count(count)
                    if tab is not None:
                        print(f"{tab} FINGER{'S' if tab > 1 else ''} -> Tab {tab}")
                        if self.is_active:
                            self.controller.goto_tab(tab)

                # ── PINCH SCROLL ──
                scroll = self.detect_pinch_scroll(hand)
                if scroll:
                    scroll_dir, scroll_amt = scroll
                    if self.is_active:
                        self.controller.scroll(scroll_dir, scroll_amt)

            # ── Face HUD overlay ──
            self.draw_face_hud(frame)

            # ── Blink event (double-blink wired as example action) ──
            blinks = self.face_engine.consume_blink_event()
            if blinks >= 2:
                print("DOUBLE BLINK detected")

            # ── Status display ──
            status_text = "ACTIVE" if self.is_active else "INACTIVE"
            status_color = (0, 255, 0) if self.is_active else (0, 0, 255)
            cv2.putText(frame, status_text, (self.width - 180, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

            swipe_st = self.gesture_engine.swipe_state
            cv2.putText(frame, f"Swipe: {swipe_st}", (self.width - 220, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            if hands:
                cv2.putText(frame, f"Hands: {len(hands)}", (10, self.height - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

            # ── FPS ──
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_time
                fps = 30 / max(elapsed, 0.001)
                print(f"FPS: {fps:.1f} | Hands: {len(hands)} | {'ACTIVE' if self.is_active else 'INACTIVE'}")
                fps_time = time.time()

            cv2.imshow("Sideswipe", frame)

            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()
        if self.face_mesh:
            self.face_mesh.close()
        print("\nTracking stopped")


if __name__ == "__main__":
    try:
        tracker = SimpleHandTracker()
        tracker.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
