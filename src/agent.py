"""
Sideswipe - Hand Gesture Tracking Agent
Per-hand GestureEngine instances, FaceMesh integration, strict gesture gating.
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
        """Switch browser tab. Swipe LEFT = next tab, RIGHT = previous tab."""
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
        """Navigate to Chrome tab 1-4 using Cmd+Number."""
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
    """Hand + face tracking with per-hand gesture engines.

    Each detected hand gets its own GestureEngine instance so smoothing
    and gesture state machines never interfere between hands.
    """

    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20

    # Colors per hand (BGR)
    HAND_COLORS = {
        'Left': (0, 255, 0),      # green
        'Right': (255, 200, 0),    # cyan-ish
        'Unknown': (0, 165, 255),  # orange
    }

    def __init__(self):
        print("Initializing Hand + Face Tracker...")

        # ── Per-hand engines (created on demand) ──
        self.engines = {}  # 'Left' -> GestureEngine, 'Right' -> GestureEngine
        self.face_engine = FaceEngine()
        self.controller = MacOSController()

        # ── MediaPipe Hands (Tasks API) ──
        model_path = "hand_landmarker.task"
        try:
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=2,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.4,
            )
            self.hands = vision.HandLandmarker.create_from_options(options)
            print("  Hand detector ready")
        except Exception as e:
            raise RuntimeError(f"Failed to init hand detector: {e}")

        # ── MediaPipe FaceLandmarker (Tasks API) ──
        face_model_path = "face_landmarker.task"
        try:
            face_base = python.BaseOptions(model_asset_path=face_model_path)
            face_options = vision.FaceLandmarkerOptions(
                base_options=face_base,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.face_landmarker = vision.FaceLandmarker.create_from_options(face_options)
            print("  FaceLandmarker ready")
        except Exception as e:
            print(f"  FaceLandmarker unavailable: {e}")
            self.face_landmarker = None

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

        # ── Start ACTIVE (no clap needed) ──
        self.is_active = True
        self.clap_history = deque(maxlen=3)
        self.clap_cooldown = 0

        # ── Scroll (pinch) — per-hand via PinchScrollTracker ──
        self.scroll_tracker = PinchScrollTracker(
            pinch_threshold=FINGER_SCROLL["pinch_threshold"],
            activation_frames=FINGER_SCROLL["activation_frames"],
            history_size=FINGER_SCROLL["history_size"],
            velocity_smoothing=FINGER_SCROLL["velocity_smoothing"],
            dead_zone=FINGER_SCROLL["dead_zone"],
            velocity_scale=FINGER_SCROLL["velocity_scale"],
            max_scroll_amount=FINGER_SCROLL["max_scroll_amount"],
        )

        # ── Face state ──
        self.face_metrics = None
        self.face_landmarks_raw = None  # for drawing

        print("\nCONTROLS:")
        print("  CLAP TWICE        : Toggle on/off")
        print("  FLAT HAND SWIPE   : Switch tabs (left/right)")
        print("  PINCH + DRAG      : Scroll (up/down)")
        print("  HOLD 1-4 (upright): Jump to Chrome tab 1-4")
        print("  'q'               : Quit\n")

    # ──────────────────────────────────────────
    #  Get or create per-hand engine
    # ──────────────────────────────────────────
    def _get_engine(self, hand_id):
        if hand_id not in self.engines:
            self.engines[hand_id] = GestureEngine(alpha=0.12, beta=0.08)
        return self.engines[hand_id]

    # ──────────────────────────────────────────
    #  Hand detection
    # ──────────────────────────────────────────
    def detect_hands(self, mp_image):
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
    def detect_face(self, mp_image):
        """Run FaceLandmarker and update face_engine metrics."""
        if self.face_landmarker is None:
            return None

        results = self.face_landmarker.detect(mp_image)

        if results.face_landmarks:
            face_lm = results.face_landmarks[0]
            self.face_landmarks_raw = face_lm  # save for drawing
            self.face_metrics = self.face_engine.process(face_lm)
            return self.face_metrics

        self.face_landmarks_raw = None
        return None

    # ──────────────────────────────────────────
    #  Gesture helpers
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
    def draw_hand(self, frame, landmarks, color=(0, 255, 0)):
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
            cv2.line(frame, p1, p2, color, 2)

        for i in range(21):
            px = int(landmarks[i][0]*w)
            py = int(landmarks[i][1]*h)
            r = 5 if i in (0, 4, 8, 12, 16, 20) else 3
            cv2.circle(frame, (px, py), r, color, -1)

    def draw_face_points(self, frame):
        """Draw key face landmarks so user can see face tracking works."""
        if self.face_landmarks_raw is None:
            return

        h, w = frame.shape[:2]
        lm = self.face_landmarks_raw

        # Key face landmarks: eyes, nose, mouth, jawline
        key_indices = [
            # Left eye
            33, 133, 159, 145,
            # Right eye
            362, 263, 386, 374,
            # Nose
            1, 4,
            # Mouth
            13, 14, 61, 291,
            # Eyebrows
            70, 300,
            # Jawline
            152, 234, 454,
        ]

        for idx in key_indices:
            if idx < len(lm):
                px = int(lm[idx].x * w)
                py = int(lm[idx].y * h)
                cv2.circle(frame, (px, py), 2, (0, 255, 255), -1)

    def draw_face_hud(self, frame):
        """Draw face-metrics HUD in the top-left corner."""
        if self.face_metrics is None:
            return

        m = self.face_metrics
        x0, y0 = 10, 10
        lh = 20
        bg_h = lh * 7 + 10
        bg_w = 260

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

    def draw_hand_info(self, frame, hand_id, engine, count, y_offset):
        """Show per-hand gesture state on screen."""
        x = 10
        y = self.height - 60 - y_offset * 80
        color = self.HAND_COLORS.get(hand_id, (200, 200, 200))

        cv2.putText(frame, f"{hand_id} hand", (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)

        mode = "SWIPE" if engine.is_hand_horizontal(engine._smoothed) \
            else ("COUNT" if engine.is_hand_vertical(engine._smoothed) else "---") \
            if engine._smoothed is not None else "---"

        cv2.putText(frame, f"Mode: {mode}  Swipe: {engine.swipe_state}  Fingers: {count}",
                    (x, y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

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

            # Convert once, reuse for both hand and face detection
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

            # ── Detect hands + face ──
            hands = self.detect_hands(mp_image)
            self.detect_face(mp_image)

            # ── Track which hands are present this frame ──
            current_ids = set()

            # ── Clap detection (2 hands) ──
            if len(hands) >= 2 and self.clap_cooldown <= 0:
                if self.detect_clap(hands):
                    self.is_active = not self.is_active
                    status = "ACTIVATED" if self.is_active else "DEACTIVATED"
                    print(f"CLAP -> {status}")
                    self.clap_cooldown = 0.5

            # ── Per-hand gesture processing ──
            for idx, hand in enumerate(hands):
                hand_id = hand['handedness']
                current_ids.add(hand_id)
                raw_lm = hand['landmarks']

                # Get this hand's dedicated engine
                engine = self._get_engine(hand_id)

                # Smooth landmarks (per-hand, no cross-contamination)
                smoothed = engine.smooth(raw_lm)

                # Draw with hand-specific color
                color = self.HAND_COLORS.get(hand_id, (200, 200, 200))
                self.draw_hand(frame, smoothed, color)

                # Count fingers (always, for display)
                count = self.count_fingers(hand)

                # ── SWIPE (horizontal hand only) ──
                swipe_dir = engine.process_swipe(smoothed)
                if swipe_dir:
                    print(f"SWIPE {swipe_dir} ({hand_id})")
                    if self.is_active:
                        self.controller.switch_tab(swipe_dir)

                # ── FINGER COUNT (upright hand only) ──
                if engine.is_hand_vertical(smoothed):
                    tab = engine.process_finger_count(count)
                    if tab is not None:
                        print(f"{tab} FINGER{'S' if tab > 1 else ''} -> Tab {tab} ({hand_id})")
                        if self.is_active:
                            self.controller.goto_tab(tab)

                # ── PINCH SCROLL ──
                scroll = self.detect_pinch_scroll(hand)
                if scroll:
                    scroll_dir, scroll_amt = scroll
                    if self.is_active:
                        self.controller.scroll(scroll_dir, scroll_amt)

                # Draw per-hand info
                self.draw_hand_info(frame, hand_id, engine, count, idx)

            # ── Clean up engines for hands that left the frame ──
            for hand_id in list(self.engines.keys()):
                if hand_id not in current_ids:
                    self.engines[hand_id].on_hand_lost()

            # ── Face drawing + HUD ──
            self.draw_face_points(frame)
            self.draw_face_hud(frame)

            # ── Blink event ──
            blinks = self.face_engine.consume_blink_event()
            if blinks >= 2:
                print("DOUBLE BLINK detected")

            # ── Status display ──
            status_text = "ACTIVE" if self.is_active else "INACTIVE"
            status_color = (0, 255, 0) if self.is_active else (0, 0, 255)
            cv2.putText(frame, status_text, (self.width - 180, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

            if hands:
                cv2.putText(frame, f"Hands: {len(hands)}", (self.width - 180, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

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
