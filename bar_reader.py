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
        # Evita texto central da barra e as bordas superior/inferior.
        y1 = max(0, int(h * 0.55))
        y2 = min(h, int(h * 0.90))
        if y2 <= y1:
            return mask
        return mask[y1:y2, :]

    @staticmethod
    def _contiguous_fill_percent(mask: np.ndarray) -> float:
        if mask.size == 0:
            return 0.0

        band = BarReader._extract_analysis_band(mask)
        if band.size == 0:
            return 0.0

        # Remove ruído isolado sem destruir o preenchimento horizontal da barra.
        kernel = np.ones((2, 2), dtype=np.uint8)
        cleaned = cv2.morphologyEx(band, cv2.MORPH_OPEN, kernel)

        mask_bin = (cleaned > 0).astype(np.uint8)
        col_ratio = mask_bin.mean(axis=0)

        # Suaviza resposta por coluna para reduzir serrilhado.
        smooth_kernel = np.ones((5,), dtype=np.float32) / 5.0
        col_ratio = np.convolve(col_ratio, smooth_kernel, mode="same")
        active_cols = col_ratio >= 0.45

        if active_cols.size == 0 or not np.any(active_cols):
            return 0.0

        # Inicia somente quando existe um pequeno trecho inicial consistente.
        min_start_run = 4
        w = len(active_cols)
        stop_empty_run = max(10, int(w * 0.03))

        filled_end = 0
        started = False
        active_run = 0
        empty_run = 0

        for idx, is_active in enumerate(active_cols):
            if is_active:
                active_run += 1
                empty_run = 0
                if not started and active_run >= min_start_run:
                    started = True
                if started:
                    filled_end = idx + 1
            else:
                active_run = 0
                if started:
                    empty_run += 1
                    # Para quando encontra um bloco vazio longo (fim real da barra).
                    if empty_run >= stop_empty_run:
                        break

        total = int(mask.shape[1])
        if total <= 0:
            return 0.0
        return max(0.0, min(100.0, (filled_end / total) * 100.0))

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
