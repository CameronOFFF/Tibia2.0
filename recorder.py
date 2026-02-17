from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


@dataclass
class RecordingState:
    active: bool
    output_path: Optional[str] = None


class WindowRecorder:
    def __init__(self, output_dir: str = "recordings") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._writer: Optional[cv2.VideoWriter] = None
        self._fps: int = 15
        self._output_path: Optional[Path] = None

    @property
    def is_recording(self) -> bool:
        return self._writer is not None

    @property
    def output_path(self) -> Optional[str]:
        return str(self._output_path) if self._output_path else None

    def start(self, width: int, height: int, fps: int = 15, filename_prefix: str = "tibia_capture") -> RecordingState:
        if self._writer is not None:
            return RecordingState(active=True, output_path=self.output_path)

        self._fps = max(1, int(fps))
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._output_path = self.output_dir / f"{filename_prefix}_{ts}.mp4"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(self._output_path), fourcc, self._fps, (width, height))
        if not writer.isOpened():
            self._output_path = None
            return RecordingState(active=False, output_path=None)

        self._writer = writer
        return RecordingState(active=True, output_path=self.output_path)

    def write(self, frame: np.ndarray) -> None:
        if self._writer is None:
            return
        self._writer.write(frame)

    def stop(self) -> RecordingState:
        if self._writer is not None:
            self._writer.release()
            self._writer = None
        return RecordingState(active=False, output_path=self.output_path)
