from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
from mss import mss
import win32con
import win32gui
import win32process


@dataclass
class TibiaWindow:
    hwnd: int
    title: str


class WindowCaptureError(RuntimeError):
    pass


class TibiaWindowManager:
    def __init__(self) -> None:
        self._sct = mss()

    def list_tibia_windows(self) -> list[TibiaWindow]:
        windows: list[TibiaWindow] = []

        def callback(hwnd: int, _: int) -> bool:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd)
            if title.startswith("Tibia - "):
                windows.append(TibiaWindow(hwnd=hwnd, title=title))
            return True

        win32gui.EnumWindows(callback, 0)
        return windows

    def is_minimized(self, hwnd: int) -> bool:
        return win32gui.IsIconic(hwnd) == 1

    def get_window_rect(self, hwnd: int) -> tuple[int, int, int, int]:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        if right <= left or bottom <= top:
            raise WindowCaptureError("Retângulo de janela inválido")
        return left, top, right, bottom

    def capture_window(self, hwnd: int) -> np.ndarray:
        if self.is_minimized(hwnd):
            raise WindowCaptureError("Janela minimizada")

        left, top, right, bottom = self.get_window_rect(hwnd)
        raw = self._sct.grab({"left": left, "top": top, "width": right - left, "height": bottom - top})
        frame = np.array(raw)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    @staticmethod
    def extract_roi(frame: np.ndarray, roi: dict[str, int]) -> np.ndarray:
        x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]
        if any(v < 0 for v in (x, y, w, h)) or w <= 0 or h <= 0:
            raise WindowCaptureError("ROI inválida")
        max_h, max_w = frame.shape[:2]
        if x + w > max_w or y + h > max_h:
            raise WindowCaptureError("ROI fora da janela")
        return frame[y : y + h, x : x + w]


PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400


class MemoryReader:
    def __init__(self, hwnd: int) -> None:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        self.pid = pid
        self.handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not self.handle:
            raise WindowCaptureError("Falha ao abrir processo do Tibia")

    def close(self) -> None:
        if self.handle:
            ctypes.windll.kernel32.CloseHandle(self.handle)
            self.handle = None

    def __del__(self) -> None:
        self.close()

    def read_uint64(self, address: int) -> Optional[int]:
        buffer = ctypes.c_ulonglong(0)
        bytes_read = ctypes.c_size_t(0)
        ok = ctypes.windll.kernel32.ReadProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read),
        )
        if not ok or bytes_read.value != ctypes.sizeof(buffer):
            return None
        return int(buffer.value)


VK_MAP = {
    **{f"F{i}": getattr(win32con, f"VK_F{i}") for i in range(1, 13)},
}


def send_key(hwnd: int, key: str) -> None:
    key = key.upper().strip()
    if len(key) == 1 and key.isalnum():
        vk = ord(key)
    else:
        vk = VK_MAP.get(key)
    if vk is None:
        raise ValueError(f"Tecla não suportada: {key}")
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)
