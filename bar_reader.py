from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Literal, Optional, Tuple

import cv2
import numpy as np


@dataclass
class ROI:
    x: int
    y: int
    w: int
    h: int


class Smoother:
    def __init__(self, mode: Literal["ema", "median"] = "ema", ema_alpha: float = 0.35, median_window: int = 5):
        self.mode = mode
        self.ema_alpha = ema_alpha
        self.median_window = max(1, median_window)
        self._values: Deque[float] = deque(maxlen=self.median_window)
        self._ema_val: float | None = None

    def update(self, value: float) -> float:
        if self.mode == "median":
            self._values.append(value)
            return float(np.median(np.array(self._values)))

        if self._ema_val is None:
            self._ema_val = value
        else:
            self._ema_val = (self.ema_alpha * value) + ((1 - self.ema_alpha) * self._ema_val)
        return self._ema_val


class BarReader:
    def __init__(self) -> None:
        self.hp_smoother = Smoother()
        self.mp_smoother = Smoother()

    def configure_smoothing(self, mode: str, ema_alpha: float, median_window: int) -> None:
        self.hp_smoother = Smoother(mode=mode if mode in {"ema", "median"} else "ema", ema_alpha=ema_alpha, median_window=median_window)
        self.mp_smoother = Smoother(mode=mode if mode in {"ema", "median"} else "ema", ema_alpha=ema_alpha, median_window=median_window)

    @staticmethod
    def _validate_roi(frame: np.ndarray, roi: ROI) -> bool:
        h, w = frame.shape[:2]
        return roi.x >= 0 and roi.y >= 0 and roi.w > 0 and roi.h > 0 and roi.x + roi.w <= w and roi.y + roi.h <= h

    @staticmethod
    def _percent_from_mask(mask: np.ndarray) -> float:
        if mask.size == 0:
            return 0.0

        mask_bin = (mask > 0).astype(np.uint8)
        col_activity = mask_bin.mean(axis=0)
        active_cols = col_activity > 0.30
        if len(active_cols) == 0 or not np.any(active_cols):
            return 0.0

        # Busca preenchimento contínuo da esquerda para direita com tolerância a pequenos buracos.
        filled_pixels = 0
        gap = 0
        gap_tolerance = 4
        started = False
        for idx, is_active in enumerate(active_cols):
            if is_active:
                started = True
                gap = 0
                filled_pixels = idx + 1
                continue
            if started:
                gap += 1
                if gap >= gap_tolerance:
                    break

        total_pixels = int(mask.shape[1])
        if total_pixels <= 0:
            return 0.0
        return max(0.0, min(100.0, (filled_pixels / total_pixels) * 100.0))

    def read_percent(
        self,
        frame: np.ndarray,
        roi: ROI,
        hsv_lower: Tuple[int, int, int],
        hsv_upper: Tuple[int, int, int],
        hsv_lower2: Optional[Tuple[int, int, int]] = None,
        hsv_upper2: Optional[Tuple[int, int, int]] = None,
    ) -> float:
        if not self._validate_roi(frame, roi):
            raise ValueError(f"ROI inválida: {roi}")

        cropped = frame[roi.y : roi.y + roi.h, roi.x : roi.x + roi.w]
        hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(hsv_lower, dtype=np.uint8), np.array(hsv_upper, dtype=np.uint8))
        if hsv_lower2 and hsv_upper2:
            mask2 = cv2.inRange(hsv, np.array(hsv_lower2, dtype=np.uint8), np.array(hsv_upper2, dtype=np.uint8))
            mask = cv2.bitwise_or(mask, mask2)
        mask = cv2.medianBlur(mask, 3)
        return self._percent_from_mask(mask)

    def read_hp_mp(
        self,
        frame: np.ndarray,
        hp_roi: ROI,
        mp_roi: ROI,
        hp_hsv_lower: Tuple[int, int, int],
        hp_hsv_upper: Tuple[int, int, int],
        mp_hsv_lower: Tuple[int, int, int],
        mp_hsv_upper: Tuple[int, int, int],
        hp_hsv_lower2: Optional[Tuple[int, int, int]] = None,
        hp_hsv_upper2: Optional[Tuple[int, int, int]] = None,
        mp_hsv_lower2: Optional[Tuple[int, int, int]] = None,
        mp_hsv_upper2: Optional[Tuple[int, int, int]] = None,
    ) -> tuple[float, float]:
        hp_raw = self.read_percent(frame, hp_roi, hp_hsv_lower, hp_hsv_upper, hp_hsv_lower2, hp_hsv_upper2)
        mp_raw = self.read_percent(frame, mp_roi, mp_hsv_lower, mp_hsv_upper, mp_hsv_lower2, mp_hsv_upper2)
        return self.hp_smoother.update(hp_raw), self.mp_smoother.update(mp_raw)
