"""
FaceEngine — MediaPipe FaceMesh metric extraction.
Computes blink, mouth openness, head tilt, and eyebrow raise from 468 landmarks.
"""

import math
import time


class FaceEngine:
    """Processes FaceMesh landmarks into facial metrics with EMA smoothing.

    Metrics:
      - ear_left / ear_right: Eye Aspect Ratio (lower = more closed)
      - blink_left / blink_right: boolean blink state
      - mouth_openness / mouth_open: lip separation ratio
      - head_tilt: roll angle in degrees (0 = straight)
      - brow_raise / brow_raised: eyebrow elevation ratio
    """

    def __init__(self):
        self.EAR_THRESHOLD = 0.22
        self.MOUTH_THRESHOLD = 0.06
        self.BROW_THRESHOLD = 0.28
        self.smooth_alpha = 0.3

        self.metrics = {
            'ear_left': 0.3,
            'ear_right': 0.3,
            'mouth_openness': 0.0,
            'head_tilt': 0.0,
            'brow_raise': 0.0,
            'blink_left': False,
            'blink_right': False,
            'mouth_open': False,
            'brow_raised': False,
        }

        # Blink event detection (edge-triggered)
        self._prev_both_closed = False
        self._last_blink_time = 0.0
        self._blink_count = 0
        self.DOUBLE_BLINK_WINDOW = 0.4  # seconds

    @staticmethod
    def _dist(a, b):
        """Euclidean 2D distance between two NormalizedLandmark objects."""
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def _ema(self, prev, curr):
        return self.smooth_alpha * curr + (1 - self.smooth_alpha) * prev

    def process(self, landmarks):
        """Process a list of 468+ FaceMesh NormalizedLandmark objects.
        Returns the smoothed metrics dict.
        """
        if not landmarks or len(landmarks) < 468:
            return self.metrics

        lm = landmarks

        # ── Eye Aspect Ratio ──
        # Left:  159(top), 145(bottom), 33(inner), 133(outer)
        ear_l = self._dist(lm[159], lm[145]) / max(self._dist(lm[33], lm[133]), 0.001)
        # Right: 386(top), 374(bottom), 362(inner), 263(outer)
        ear_r = self._dist(lm[386], lm[374]) / max(self._dist(lm[362], lm[263]), 0.001)

        # ── Mouth openness ──
        # 13(upper lip center), 14(lower lip center) vs face height 10(forehead)→152(chin)
        mouth_d = self._dist(lm[13], lm[14])
        face_h = max(self._dist(lm[10], lm[152]), 0.001)
        mouth_ratio = mouth_d / face_h

        # ── Head tilt (roll) ──
        # Angle of nose-tip(1) → chin(152) relative to vertical
        tilt = math.atan2(lm[152].x - lm[1].x, lm[152].y - lm[1].y) * (180 / math.pi)

        # ── Eyebrow raise ──
        # Left brow(70)→eye(159) and right brow(300)→eye(386) vs face height
        brow_l = self._dist(lm[70], lm[159])
        brow_r = self._dist(lm[300], lm[386])
        brow_ratio = ((brow_l + brow_r) / 2) / face_h

        # ── EMA smoothing ──
        m = self.metrics
        m['ear_left'] = self._ema(m['ear_left'], ear_l)
        m['ear_right'] = self._ema(m['ear_right'], ear_r)
        m['mouth_openness'] = self._ema(m['mouth_openness'], mouth_ratio)
        m['head_tilt'] = self._ema(m['head_tilt'], tilt)
        m['brow_raise'] = self._ema(m['brow_raise'], brow_ratio)

        # ── Boolean states ──
        m['blink_left'] = m['ear_left'] < self.EAR_THRESHOLD
        m['blink_right'] = m['ear_right'] < self.EAR_THRESHOLD
        m['mouth_open'] = m['mouth_openness'] > self.MOUTH_THRESHOLD
        m['brow_raised'] = m['brow_raise'] > self.BROW_THRESHOLD

        # ── Blink event (rising edge: both eyes just closed) ──
        both = m['blink_left'] and m['blink_right']
        now = time.time()
        if both and not self._prev_both_closed:
            if now - self._last_blink_time < self.DOUBLE_BLINK_WINDOW:
                self._blink_count += 1
            else:
                self._blink_count = 1
            self._last_blink_time = now
        self._prev_both_closed = both

        return m

    def consume_blink_event(self) -> int:
        """Returns pending blink count (1 or 2+) once the double-blink window
        has elapsed, then resets. Returns 0 if no event ready."""
        now = time.time()
        if self._blink_count > 0 and (now - self._last_blink_time) > self.DOUBLE_BLINK_WINDOW:
            count = self._blink_count
            self._blink_count = 0
            return count
        return 0
