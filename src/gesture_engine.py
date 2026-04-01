"""
GestureEngine — all smoothing, orientation checks, and gesture state machines.
Separated from rendering logic per architecture requirements.
"""

import math
import time
import numpy as np
from collections import deque


class GestureEngine:
    """Processes hand landmarks into gesture events.

    Responsibilities:
      - Double exponential smoothing on raw landmarks
      - Hand orientation detection (horizontal vs vertical)
      - Swipe state machine: IDLE → CANDIDATE → CONFIRMED → COOLDOWN
      - Finger-count state machine for tab navigation (1-4)
      - Scroll momentum tracking
    """

    def __init__(self, alpha=0.12, beta=0.08):
        # ── Double exponential smoothing ──
        self.alpha = alpha
        self.beta = beta
        self._smoothed = None
        self._vel = None

        # ── Swipe state machine ──
        self.swipe_state = 'IDLE'
        self._swipe_start_x = 0.0
        self._swipe_start_time = 0.0
        self._swipe_cooldown_end = 0.0
        self._hand_entry_time = 0.0
        self._hand_was_present = False
        self.partial_swipe_offset = 0.0

        # Swipe thresholds
        self.HAND_ENTRY_COOLDOWN = 0.6   # 600 ms after hand enters frame
        self.SWIPE_Y_SPREAD_MAX = 0.08   # max Y spread across 5 fingertips
        self.SWIPE_ANGLE_TOL = 20        # degrees from horizontal
        self.SWIPE_MIN_DISP = 0.12       # normalized displacement
        self.SWIPE_MIN_VEL = 0.35        # normalized units / second
        self.SWIPE_MAX_TIME = 0.4        # seconds to complete swipe
        self.SWIPE_COOLDOWN = 0.6        # seconds after confirmed swipe

        # ── Finger count state ──
        self._finger_history = deque(maxlen=12)
        self._last_confirmed = 0
        self._finger_cooldown_end = 0.0
        self.FINGER_STABILITY = 12       # frames of consistent count
        self.FINGER_COOLDOWN = 0.8       # seconds between triggers

    # ──────────────────────────────────────────
    #  Double Exponential Smoothing (Holt)
    # ──────────────────────────────────────────
    def smooth(self, raw: np.ndarray) -> np.ndarray:
        """Apply double exponential smoothing to a (21, 2) landmark array."""
        if self._smoothed is None:
            self._smoothed = raw.copy()
            self._vel = np.zeros_like(raw)
            return self._smoothed

        s = self.alpha * raw + (1 - self.alpha) * (self._smoothed + self._vel)
        v = self.beta * (s - self._smoothed) + (1 - self.beta) * self._vel
        self._smoothed = s
        self._vel = v
        return self._smoothed

    # ──────────────────────────────────────────
    #  Hand orientation helpers
    # ──────────────────────────────────────────
    def is_hand_horizontal(self, landmarks: np.ndarray) -> bool:
        """True when all 5 fingertips sit in a tight horizontal band
        AND the wrist→middle-MCP vector is near-horizontal."""
        tip_ys = [landmarks[i][1] for i in (4, 8, 12, 16, 20)]
        if max(tip_ys) - min(tip_ys) > self.SWIPE_Y_SPREAD_MAX:
            return False

        wrist = landmarks[0]
        mcp9 = landmarks[9]
        angle = abs(math.atan2(mcp9[1] - wrist[1], mcp9[0] - wrist[0]) * 180 / math.pi)
        return angle < self.SWIPE_ANGLE_TOL or angle > (180 - self.SWIPE_ANGLE_TOL)

    def is_hand_vertical(self, landmarks: np.ndarray) -> bool:
        """True when wrist is below all non-thumb tips and vector is ~vertical."""
        wrist_y = landmarks[0][1]
        if not all(landmarks[i][1] < wrist_y for i in (8, 12, 16, 20)):
            return False

        wrist = landmarks[0]
        mcp9 = landmarks[9]
        angle = math.atan2(mcp9[1] - wrist[1], mcp9[0] - wrist[0]) * 180 / math.pi
        return abs(angle + 90) < 30

    # ──────────────────────────────────────────
    #  Swipe state machine
    # ──────────────────────────────────────────
    def process_swipe(self, landmarks: np.ndarray) -> str | None:
        """Returns 'LEFT', 'RIGHT', or None.

        State machine: IDLE → CANDIDATE → CONFIRMED → COOLDOWN
        Only fires when hand is horizontal, displacement and velocity exceed
        thresholds, and the 600 ms hand-entry cooldown has elapsed.
        """
        now = time.time()

        # Hand-entry cooldown
        if not self._hand_was_present:
            self._hand_entry_time = now
            self._hand_was_present = True
            self.swipe_state = 'IDLE'

        if now - self._hand_entry_time < self.HAND_ENTRY_COOLDOWN:
            self.partial_swipe_offset = 0
            return None

        # COOLDOWN tick
        if self.swipe_state == 'COOLDOWN':
            self.partial_swipe_offset = 0
            if now > self._swipe_cooldown_end:
                self.swipe_state = 'IDLE'
            return None

        # Must be horizontal to swipe
        if not self.is_hand_horizontal(landmarks):
            if self.swipe_state == 'CANDIDATE':
                self.swipe_state = 'IDLE'
            self.partial_swipe_offset = 0
            return None

        palm_x = (landmarks[0][0] + landmarks[9][0]) / 2

        # IDLE → CANDIDATE
        if self.swipe_state == 'IDLE':
            self._swipe_start_x = palm_x
            self._swipe_start_time = now
            self.swipe_state = 'CANDIDATE'
            self.partial_swipe_offset = 0
            return None

        # CANDIDATE → check for CONFIRMED
        if self.swipe_state == 'CANDIDATE':
            disp = palm_x - self._swipe_start_x
            elapsed = now - self._swipe_start_time

            self.partial_swipe_offset = max(-0.5, min(0.5, disp))

            # Too slow — reset start point
            if elapsed > self.SWIPE_MAX_TIME:
                self._swipe_start_x = palm_x
                self._swipe_start_time = now
                return None

            abs_disp = abs(disp)
            velocity = abs_disp / max(elapsed, 0.001)

            if abs_disp >= self.SWIPE_MIN_DISP and velocity >= self.SWIPE_MIN_VEL:
                self.swipe_state = 'COOLDOWN'
                self._swipe_cooldown_end = now + self.SWIPE_COOLDOWN
                self.partial_swipe_offset = 0
                return 'LEFT' if disp < 0 else 'RIGHT'

        return None

    # ──────────────────────────────────────────
    #  Finger count (tab navigation)
    # ──────────────────────────────────────────
    def process_finger_count(self, count: int) -> int | None:
        """Feed a finger count each frame. Returns confirmed tab (1-4) or None.

        Caller must verify hand is vertical before calling.
        A fist (0) resets state so the same tab can be re-triggered.
        """
        now = time.time()
        if now < self._finger_cooldown_end:
            return None

        if count == 0:
            self._finger_history.clear()
            self._last_confirmed = 0
            return None

        if count > 4:
            self._finger_history.clear()
            return None

        self._finger_history.append(count)
        if len(self._finger_history) < self.FINGER_STABILITY:
            return None

        recent = list(self._finger_history)
        if all(n == recent[0] for n in recent):
            confirmed = recent[0]
            if confirmed != self._last_confirmed:
                self._last_confirmed = confirmed
                self._finger_history.clear()
                self._finger_cooldown_end = now + self.FINGER_COOLDOWN
                return confirmed

        return None

    # ──────────────────────────────────────────
    #  Hand lost / reset
    # ──────────────────────────────────────────
    def on_hand_lost(self):
        """Call when hand leaves frame. Resets all state."""
        self._hand_was_present = False
        self.swipe_state = 'IDLE'
        self.partial_swipe_offset = 0
        self._finger_history.clear()
        self._smoothed = None
        self._vel = None
