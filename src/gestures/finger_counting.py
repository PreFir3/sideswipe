"""
Shared helpers for stable finger counting across runtimes.
"""

import numpy as np


WRIST = 0
THUMB_IP = 3
THUMB_TIP = 4

NON_THUMB_FINGERS = (
    (8, 6, 5),    # Index: tip, pip, mcp
    (12, 10, 9),  # Middle
    (16, 14, 13), # Ring
    (20, 18, 17), # Pinky
)


def is_thumb_extended(
    landmarks: np.ndarray,
    handedness: str = "Unknown",
    horizontal_margin: float = 0.035,
    reach_margin: float = 0.015,
) -> bool:
    """Return True when the thumb is clearly extended away from the hand."""
    if landmarks.size == 0 or len(landmarks) < 21:
        return False

    thumb_tip = landmarks[THUMB_TIP]
    thumb_ip = landmarks[THUMB_IP]
    wrist = landmarks[WRIST]

    horizontal_delta = thumb_tip[0] - thumb_ip[0]

    if handedness == "Right":
        thumb_points_out = horizontal_delta < -horizontal_margin
    elif handedness == "Left":
        thumb_points_out = horizontal_delta > horizontal_margin
    else:
        thumb_points_out = abs(horizontal_delta) > horizontal_margin

    thumb_tip_reach = np.linalg.norm(thumb_tip - wrist)
    thumb_ip_reach = np.linalg.norm(thumb_ip - wrist)

    return thumb_points_out and thumb_tip_reach > thumb_ip_reach + reach_margin


def count_extended_fingers(
    landmarks: np.ndarray,
    handedness: str = "Unknown",
    finger_tip_margin: float = 0.025,
    thumb_horizontal_margin: float = 0.035,
    thumb_reach_margin: float = 0.015,
) -> int:
    """Count clearly extended fingers while avoiding accidental thumb overcounts."""
    if landmarks.size == 0 or len(landmarks) < 21:
        return 0

    count = 0

    if is_thumb_extended(
        landmarks,
        handedness=handedness,
        horizontal_margin=thumb_horizontal_margin,
        reach_margin=thumb_reach_margin,
    ):
        count += 1

    for tip_idx, pip_idx, mcp_idx in NON_THUMB_FINGERS:
        tip_y = landmarks[tip_idx][1]
        pip_y = landmarks[pip_idx][1]
        mcp_y = landmarks[mcp_idx][1]

        if tip_y < pip_y - finger_tip_margin and pip_y < mcp_y - (finger_tip_margin / 2):
            count += 1

    return count
