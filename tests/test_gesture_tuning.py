import sys
from pathlib import Path

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gestures.finger_counting import count_extended_fingers
from gestures.finger_scroll import FingerScrollDetector
from gestures.pinch_scroll import PinchScrollTracker


def _build_hand_landmarks(handedness="Right", extended_fingers=()):
    landmarks = np.zeros((21, 2), dtype=float)

    landmarks[0] = [0.50, 0.86]  # Wrist
    landmarks[1] = [0.46, 0.78]
    landmarks[2] = [0.43, 0.72]
    landmarks[3] = [0.40, 0.68]

    if "thumb" in extended_fingers:
        landmarks[4] = [0.32, 0.64] if handedness == "Right" else [0.54, 0.64]
    else:
        landmarks[4] = [0.39, 0.69] if handedness == "Right" else [0.41, 0.69]

    finger_layout = {
        "index": (5, 6, 7, 8, 0.44),
        "middle": (9, 10, 11, 12, 0.50),
        "ring": (13, 14, 15, 16, 0.56),
        "pinky": (17, 18, 19, 20, 0.62),
    }

    for name, (mcp, pip, dip, tip, x) in finger_layout.items():
        landmarks[mcp] = [x, 0.72]
        landmarks[pip] = [x, 0.60]
        landmarks[dip] = [x, 0.52]
        tip_y = 0.40 if name in extended_fingers else 0.76
        landmarks[tip] = [x, tip_y]

    return landmarks


def test_relaxed_thumb_no_longer_pushes_three_fingers_to_four():
    landmarks = _build_hand_landmarks(
        handedness="Right",
        extended_fingers=("index", "middle", "ring"),
    )

    assert count_extended_fingers(landmarks, handedness="Right") == 3


def test_deliberate_left_thumb_still_counts_when_it_is_really_extended():
    landmarks = _build_hand_landmarks(
        handedness="Left",
        extended_fingers=("thumb", "index"),
    )

    assert count_extended_fingers(landmarks, handedness="Left") == 2


def test_legacy_scroll_detector_ignores_small_jitter():
    detector = FingerScrollDetector(min_movement=0.035, smoothing_frames=7, activation_frames=4)

    for y_pos in [0.50, 0.503, 0.499, 0.502, 0.501, 0.498, 0.500]:
        gesture = detector.add_finger_position(y_pos)

    assert gesture.is_active is False


def test_pinch_scroll_requires_real_motion_before_emitting_scroll():
    tracker = PinchScrollTracker(
        pinch_threshold=0.05,
        activation_frames=4,
        history_size=8,
        velocity_smoothing=0.8,
        dead_zone=0.006,
        velocity_scale=150,
        max_scroll_amount=5,
    )

    for y_pos in [0.50, 0.502, 0.499, 0.501, 0.500, 0.498]:
        update = tracker.update(
            "Right",
            np.array([0.40, y_pos]),
            np.array([0.44, y_pos]),
        )
        assert update is None

    direction = None
    amount = 0
    for y_pos in [0.50, 0.51, 0.53, 0.56, 0.60, 0.65, 0.71]:
        update = tracker.update(
            "Right",
            np.array([0.40, y_pos]),
            np.array([0.44, y_pos]),
        )
        if update is not None:
            direction = update.direction
            amount = update.amount

    assert direction == "DOWN"
    assert 1 <= amount <= 5
