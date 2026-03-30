"""
Smooth pinch-scroll filtering for the hand-tracking agent.
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np


@dataclass
class PinchScrollUpdate:
    """Result of a pinch-scroll update."""
    direction: str
    amount: int
    velocity: float


class PinchScrollTracker:
    """Turn pinch movement into smooth, low-jitter scroll updates."""

    def __init__(
        self,
        pinch_threshold: float = 0.05,
        activation_frames: int = 4,
        history_size: int = 8,
        velocity_smoothing: float = 0.8,
        dead_zone: float = 0.006,
        velocity_scale: float = 150.0,
        max_scroll_amount: int = 5,
    ):
        self.pinch_threshold = pinch_threshold
        self.activation_frames = activation_frames
        self.history_size = history_size
        self.velocity_smoothing = velocity_smoothing
        self.dead_zone = dead_zone
        self.velocity_scale = velocity_scale
        self.max_scroll_amount = max_scroll_amount

        self.position_history: Dict[str, deque] = {}
        self.velocity_by_hand = defaultdict(float)
        self.pinch_frames_by_hand = defaultdict(int)

    def reset_hand(self, hand_id: str) -> None:
        """Clear stored movement state for one hand."""
        self.position_history.pop(hand_id, None)
        self.velocity_by_hand.pop(hand_id, None)
        self.pinch_frames_by_hand.pop(hand_id, None)

    def update(
        self,
        hand_id: str,
        thumb_tip: np.ndarray,
        index_tip: np.ndarray,
    ) -> Optional[PinchScrollUpdate]:
        """Feed one pinch sample and return a scroll update when movement is intentional."""
        pinch_distance = float(np.linalg.norm(thumb_tip - index_tip))
        if pinch_distance > self.pinch_threshold:
            self.reset_hand(hand_id)
            return None

        history = self.position_history.setdefault(hand_id, deque(maxlen=self.history_size))
        history.append(float((thumb_tip[1] + index_tip[1]) / 2.0))
        self.pinch_frames_by_hand[hand_id] += 1

        if self.pinch_frames_by_hand[hand_id] < self.activation_frames or len(history) < 4:
            return None

        positions = list(history)
        window_size = min(3, len(positions) // 2)
        if window_size < 2:
            return None

        new_avg = sum(positions[-window_size:]) / window_size
        old_avg = sum(positions[-(window_size * 2):-window_size]) / window_size
        raw_velocity = new_avg - old_avg

        previous_velocity = self.velocity_by_hand[hand_id]
        smoothed_velocity = (
            self.velocity_smoothing * previous_velocity
            + (1.0 - self.velocity_smoothing) * raw_velocity
        )
        self.velocity_by_hand[hand_id] = smoothed_velocity

        if abs(smoothed_velocity) < self.dead_zone:
            return None

        speed = abs(smoothed_velocity) - self.dead_zone
        scroll_amount = int(
            np.clip(
                np.ceil(speed * self.velocity_scale),
                1,
                self.max_scroll_amount,
            )
        )
        direction = "UP" if smoothed_velocity < 0 else "DOWN"

        return PinchScrollUpdate(
            direction=direction,
            amount=scroll_amount,
            velocity=smoothed_velocity,
        )
