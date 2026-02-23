from __future__ import annotations

from collections import deque

import cv2
import numpy as np


class PercentageFilter:
    def __init__(self, window: int = 5) -> None:
        self.values: deque[float] = deque(maxlen=window)

    def apply(self, value: float) -> float:
        self.values.append(value)
        return float(np.median(np.array(self.values)))


class BarReader:
    @staticmethod
    def from_hsv_mask(roi: np.ndarray, lower: list[int], upper: list[int]) -> float:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))
        line = mask[mask.shape[0] // 2, :]
        filled = int(np.count_nonzero(line))
        total = len(line)
        return max(0.0, min(100.0, (filled / total) * 100 if total else 0.0))


class MemoryPercentReader:
    @staticmethod
    def current_to_percent(current: int | None, max_value: int) -> float | None:
        if current is None or max_value <= 0:
            return None
        return max(0.0, min(100.0, (current / max_value) * 100))
