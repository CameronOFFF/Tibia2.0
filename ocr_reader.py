from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

try:
    import pytesseract
except Exception:  # pragma: no cover - dependência externa opcional em runtime
    pytesseract = None


@dataclass
class OCRResult:
    current: int
    maximum: int

    @property
    def percent(self) -> float:
        if self.maximum <= 0:
            return 0.0
        return max(0.0, min(100.0, (self.current / self.maximum) * 100.0))


class OCRBarReader:
    _PAIR_RE = re.compile(r"(\d{2,6})\s*/\s*(\d{2,6})")

    def __init__(self, tesseract_cmd: Optional[str] = None) -> None:
        self.available = pytesseract is not None
        if self.available and tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    @staticmethod
    def _preprocess(roi_bgr: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, th1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        th2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 4)
        # Combinação melhora leitura quando texto está sobre fundo variado.
        return cv2.bitwise_or(th1, th2)

    @classmethod
    def _parse_pair(cls, text: str) -> Optional[OCRResult]:
        cleaned = text.replace("O", "0").replace("I", "1").replace("l", "1")
        match = cls._PAIR_RE.search(cleaned)
        if not match:
            return None
        cur = int(match.group(1))
        maxv = int(match.group(2))
        if maxv <= 0:
            return None
        return OCRResult(current=cur, maximum=maxv)

    def read_pair(self, frame: np.ndarray, x: int, y: int, w: int, h: int) -> Optional[OCRResult]:
        if not self.available:
            return None
        h_frame, w_frame = frame.shape[:2]
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > w_frame or y + h > h_frame:
            return None

        roi = frame[y : y + h, x : x + w]
        prep = self._preprocess(roi)
        config = "--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789/"
        text = pytesseract.image_to_string(prep, config=config)
        parsed = self._parse_pair(text)
        if parsed:
            return parsed

        # Segunda tentativa com inversão.
        text_inv = pytesseract.image_to_string(255 - prep, config=config)
        return self._parse_pair(text_inv)
