from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Dict, List, Optional

import cv2
import mss
import numpy as np
import win32gui


@dataclass
class WindowInfo:
    hwnd: int
    title: str
    rect: tuple[int, int, int, int]


class TibiaWindowCapture:
    def __init__(self, title_prefix: str = "Tibia - ") -> None:
        self.title_prefix = title_prefix
        self._thread_local = threading.local()

    def _get_sct(self) -> mss.mss:
        """mss usa handles thread-local no Windows, então cada thread precisa da sua instância."""
        sct = getattr(self._thread_local, "sct", None)
        if sct is None:
            sct = mss.mss()
            self._thread_local.sct = sct
        return sct

    def list_windows(self) -> List[WindowInfo]:
        windows: List[WindowInfo] = []

        def callback(hwnd: int, _extra: object) -> bool:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd).strip()
            if title.startswith(self.title_prefix):
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    windows.append(WindowInfo(hwnd=hwnd, title=title, rect=rect))
                except Exception:
                    pass
            return True

        win32gui.EnumWindows(callback, None)
        return windows

    def is_minimized(self, hwnd: int) -> bool:
        return bool(win32gui.IsIconic(hwnd))

    def get_window_rect(self, hwnd: int) -> tuple[int, int, int, int]:
        return win32gui.GetWindowRect(hwnd)

    def grab_window_frame(self, hwnd: int) -> Optional[np.ndarray]:
        if self.is_minimized(hwnd):
            return None

        left, top, right, bottom = self.get_window_rect(hwnd)
        if right <= left or bottom <= top:
            return None

        monitor: Dict[str, int] = {
            "left": left,
            "top": top,
            "width": right - left,
            "height": bottom - top,
        }

        raw = np.array(self._get_sct().grab(monitor), dtype=np.uint8)
        frame = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
        return frame
