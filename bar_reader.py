from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Literal, Optional, Sequence, Tuple

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
        selected_mode = mode if mode in {"ema", "median"} else "ema"
        self.hp_smoother = Smoother(mode=selected_mode, ema_alpha=ema_alpha, median_window=median_window)
        self.mp_smoother = Smoother(mode=selected_mode, ema_alpha=ema_alpha, median_window=median_window)

    @staticmethod
    def _validate_roi(frame: np.ndarray, roi: ROI) -> bool:
        h, w = frame.shape[:2]
        return roi.x >= 0 and roi.y >= 0 and roi.w > 0 and roi.h > 0 and roi.x + roi.w <= w and roi.y + roi.h <= h

    @staticmethod
    def _extract_analysis_band(mask: np.ndarray) -> np.ndarray:
        h = mask.shape[0]
        if h <= 3:
            return mask
        # Usa faixa central para evitar bordas/texto acima da barra.
        y1 = max(0, int(h * 0.25))
        y2 = min(h, int(h * 0.75))
        if y2 <= y1:
            return mask
        return mask[y1:y2, :]

    @staticmethod
    def _left_run_percent_per_row(bin_mask: np.ndarray) -> float:
        h, w = bin_mask.shape
        if h == 0 or w == 0:
            return 0.0

        runs = []
        min_row_activity = max(3, int(w * 0.20))
        gap_tolerance = max(3, int(w * 0.01))

        for row in range(h):
            line = bin_mask[row]
            if int(np.sum(line)) < min_row_activity:
                continue

            filled = 0
            gap = 0
            started = False
            for idx, val in enumerate(line):
                if val:
                    started = True
                    gap = 0
                    filled = idx + 1
                elif started:
                    gap += 1
                    if gap >= gap_tolerance:
                        break

            if started:
                runs.append(filled / w)

        if not runs:
            return 0.0

        runs_arr = np.array(runs, dtype=np.float32)
        # Usa quantil alto para priorizar linhas que realmente passam pela barra.
        return float(np.percentile(runs_arr, 75))

    @staticmethod
    def _contiguous_fill_percent(mask: np.ndarray) -> float:
        if mask.size == 0:
            return 0.0

        band = BarReader._extract_analysis_band(mask)
        if band.size == 0:
            return 0.0

        # Fecha pequenos buracos e remove ruído pontual.
        cleaned = cv2.morphologyEx(band, cv2.MORPH_CLOSE, np.ones((3, 3), dtype=np.uint8))
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, np.ones((2, 2), dtype=np.uint8))
        bin_mask = (cleaned > 0).astype(np.uint8)

        ratio = BarReader._left_run_percent_per_row(bin_mask)
        return max(0.0, min(100.0, ratio * 100.0))

    @staticmethod
    def _mask_for_ranges(
        hsv: np.ndarray,
        ranges: Sequence[Tuple[Tuple[int, int, int], Tuple[int, int, int]]],
    ) -> np.ndarray:
        base = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in ranges:
            m = cv2.inRange(hsv, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))
            base = cv2.bitwise_or(base, m)
        return base

    def read_percent(
        self,
        frame: np.ndarray,
        roi: ROI,
        hsv_lower: Tuple[int, int, int],
        hsv_upper: Tuple[int, int, int],
        hsv_lower2: Optional[Tuple[int, int, int]] = None,
        hsv_upper2: Optional[Tuple[int, int, int]] = None,
        hsv_lower3: Optional[Tuple[int, int, int]] = None,
        hsv_upper3: Optional[Tuple[int, int, int]] = None,
    ) -> float:
        if not self._validate_roi(frame, roi):
            raise ValueError(f"ROI inválida: {roi}")

        cropped = frame[roi.y : roi.y + roi.h, roi.x : roi.x + roi.w]
        hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)

        ranges = [(hsv_lower, hsv_upper)]
        if hsv_lower2 and hsv_upper2:
            ranges.append((hsv_lower2, hsv_upper2))
        if hsv_lower3 and hsv_upper3:
            ranges.append((hsv_lower3, hsv_upper3))

        mask = self._mask_for_ranges(hsv, ranges)
        return self._contiguous_fill_percent(mask)

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
        hp_hsv_lower3: Optional[Tuple[int, int, int]] = None,
        hp_hsv_upper3: Optional[Tuple[int, int, int]] = None,
        mp_hsv_lower3: Optional[Tuple[int, int, int]] = None,
        mp_hsv_upper3: Optional[Tuple[int, int, int]] = None,
    ) -> tuple[float, float]:
        hp_raw = self.read_percent(
            frame,
            hp_roi,
            hp_hsv_lower,
            hp_hsv_upper,
            hp_hsv_lower2,
            hp_hsv_upper2,
            hp_hsv_lower3,
            hp_hsv_upper3,
        )
        mp_raw = self.read_percent(
            frame,
            mp_roi,
            mp_hsv_lower,
            mp_hsv_upper,
            mp_hsv_lower2,
            mp_hsv_upper2,
            mp_hsv_lower3,
            mp_hsv_upper3,
        )
        return self.hp_smoother.update(hp_raw), self.mp_smoother.update(mp_raw)
