from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
import winsound

import cv2
from pydantic import BaseModel, Field

from bar_reader import BarReader, MemoryPercentReader, PercentageFilter
from rules_engine import Rule, RulesEngine
from window_capture import MemoryReader, TibiaWindowManager, WindowCaptureError, send_key


class Roi(BaseModel):
    x: int
    y: int
    w: int
    h: int


class RuleConfig(BaseModel):
    name: str
    metric: str
    operator: str = "<="
    threshold: float
    message: str
    sound: bool = True
    cooldown_seconds: float = 3
    key: str = ""


class AppConfig(BaseModel):
    fps: int = 15
    log_file: str = "monitor.log"
    history_seconds: int = 60
    max_hp: int = 5000
    max_mp: int = 3000
    hp_addresses: list[str] = Field(default_factory=list)
    mp_addresses: list[str] = Field(default_factory=list)
    hp_bar_roi: Roi
    mp_bar_roi: Roi
    hp_hsv_lower: list[int]
    hp_hsv_upper: list[int]
    mp_hsv_lower: list[int]
    mp_hsv_upper: list[int]
    rules: list[RuleConfig] = Field(default_factory=list)


@dataclass
class Sample:
    ts: float
    hp: float
    mp: float


class TibiaMonitorUI:
    def __init__(self, root: tk.Tk, config_path: str = "config.json") -> None:
        self.root = root
        self.root.title("Macho Never Duality - By: Nerd Din")
        self.config_path = Path(config_path)
        self.config = self.load_config()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            handlers=[logging.FileHandler(self.config.log_file, encoding="utf-8"), logging.StreamHandler()],
        )

        self.window_manager = TibiaWindowManager()
        self.rules_engine = RulesEngine([Rule(**r.model_dump()) for r in self.config.rules])
        self.monitor_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.selected_hwnd: int | None = None
        self.memory_reader: MemoryReader | None = None
        self.hp_filter = PercentageFilter()
        self.mp_filter = PercentageFilter()
        self.history: deque[Sample] = deque()

        self.hp_value = tk.DoubleVar(value=0)
        self.mp_value = tk.DoubleVar(value=0)
        self.status_text = tk.StringVar(value="Parado")
        self.fps_text = tk.StringVar(value="FPS: 0")
        self.max_hp_var = tk.IntVar(value=self.config.max_hp)
        self.max_mp_var = tk.IntVar(value=self.config.max_mp)
        self.toast_var = tk.StringVar(value="")

        self._build_ui()
        self.refresh_windows()

    def load_config(self) -> AppConfig:
        return AppConfig.model_validate_json(self.config_path.read_text(encoding="utf-8"))

    def save_config(self) -> None:
        self.config.max_hp = self.max_hp_var.get()
        self.config.max_mp = self.max_mp_var.get()
        self.config_path.write_text(json.dumps(self.config.model_dump(), indent=2), encoding="utf-8")
        messagebox.showinfo("Config", "Configuração salva.")

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.BOTH, expand=True)

        window_row = ttk.Frame(top)
        window_row.pack(fill=tk.X)
        self.window_combo = ttk.Combobox(window_row, state="readonly")
        self.window_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(window_row, text="Atualizar", command=self.refresh_windows).pack(side=tk.LEFT, padx=6)

        metrics = ttk.LabelFrame(top, text="Status")
        metrics.pack(fill=tk.X, pady=8)
        ttk.Label(metrics, text="HP").grid(row=0, column=0, sticky="w")
        self.hp_bar = ttk.Progressbar(metrics, maximum=100, variable=self.hp_value)
        self.hp_bar.grid(row=0, column=1, sticky="ew", padx=6)
        self.hp_lbl = ttk.Label(metrics, text="0.0%")
        self.hp_lbl.grid(row=0, column=2)

        ttk.Label(metrics, text="MP").grid(row=1, column=0, sticky="w")
        self.mp_bar = ttk.Progressbar(metrics, maximum=100, variable=self.mp_value)
        self.mp_bar.grid(row=1, column=1, sticky="ew", padx=6)
        self.mp_lbl = ttk.Label(metrics, text="0.0%")
        self.mp_lbl.grid(row=1, column=2)
        metrics.columnconfigure(1, weight=1)

        info = ttk.Frame(top)
        info.pack(fill=tk.X)
        ttk.Label(info, textvariable=self.status_text).pack(side=tk.LEFT)
        ttk.Label(info, textvariable=self.fps_text).pack(side=tk.RIGHT)

        max_row = ttk.LabelFrame(top, text="Atributos do personagem")
        max_row.pack(fill=tk.X, pady=8)
        ttk.Label(max_row, text="HP Máxima").grid(row=0, column=0)
        ttk.Entry(max_row, textvariable=self.max_hp_var, width=10).grid(row=0, column=1, padx=6)
        ttk.Label(max_row, text="MP Máxima").grid(row=0, column=2)
        ttk.Entry(max_row, textvariable=self.max_mp_var, width=10).grid(row=0, column=3, padx=6)

        controls = ttk.Frame(top)
        controls.pack(fill=tk.X, pady=8)
        ttk.Button(controls, text="Iniciar", command=self.start_monitor).pack(side=tk.LEFT)
        ttk.Button(controls, text="Parar", command=self.stop_monitor).pack(side=tk.LEFT, padx=6)
        ttk.Button(controls, text="Calibrar ROIs", command=self.open_calibration).pack(side=tk.LEFT)
        ttk.Button(controls, text="Salvar config", command=self.save_config).pack(side=tk.RIGHT)

        rules_frame = ttk.LabelFrame(top, text="Rules (Rings/Amulets e Healing)")
        rules_frame.pack(fill=tk.BOTH, expand=True)
        self.rules_list = tk.Listbox(rules_frame, height=7)
        self.rules_list.pack(fill=tk.BOTH, expand=True)
        for r in self.config.rules:
            self.rules_list.insert(tk.END, f"{r.metric} {r.operator} {r.threshold}% | {r.message} | tecla={r.key}")

        ttk.Label(top, textvariable=self.toast_var, foreground="red").pack(fill=tk.X)

    def refresh_windows(self) -> None:
        windows = self.window_manager.list_tibia_windows()
        self.windows_map = {w.title: w.hwnd for w in windows}
        self.window_combo["values"] = list(self.windows_map.keys())
        if windows:
            self.window_combo.current(0)

    def start_monitor(self) -> None:
        title = self.window_combo.get()
        hwnd = self.windows_map.get(title)
        if not hwnd:
            messagebox.showerror("Erro", "Selecione uma janela Tibia válida")
            return
        self.selected_hwnd = hwnd
        try:
            self.memory_reader = MemoryReader(hwnd)
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha na leitura de memória: {exc}")
            return
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.status_text.set("Monitorando")

    def stop_monitor(self) -> None:
        self.stop_event.set()
        if self.memory_reader:
            self.memory_reader.close()
            self.memory_reader = None
        self.status_text.set("Parado")

    def read_first_valid(self, addresses: list[str]) -> int | None:
        if not self.memory_reader:
            return None
        for addr in addresses:
            value = self.memory_reader.read_uint64(int(addr, 16))
            if value is not None and value > 0:
                return value
        return None

    def monitor_loop(self) -> None:
        last = time.time()
        while not self.stop_event.is_set():
            try:
                if self.window_manager.is_minimized(self.selected_hwnd):
                    self.root.after(0, lambda: self.status_text.set("Janela minimizada - pausa"))
                    time.sleep(0.3)
                    continue

                frame = self.window_manager.capture_window(self.selected_hwnd)
                hp_current = self.read_first_valid(self.config.hp_addresses)
                mp_current = self.read_first_valid(self.config.mp_addresses)

                hp_percent = MemoryPercentReader.current_to_percent(hp_current, self.max_hp_var.get())
                mp_percent = MemoryPercentReader.current_to_percent(mp_current, self.max_mp_var.get())

                if hp_percent is None:
                    hp_percent = BarReader.from_hsv_mask(
                        self.window_manager.extract_roi(frame, self.config.hp_bar_roi.model_dump()),
                        self.config.hp_hsv_lower,
                        self.config.hp_hsv_upper,
                    )
                if mp_percent is None:
                    mp_percent = BarReader.from_hsv_mask(
                        self.window_manager.extract_roi(frame, self.config.mp_bar_roi.model_dump()),
                        self.config.mp_hsv_lower,
                        self.config.mp_hsv_upper,
                    )

                hp_percent = self.hp_filter.apply(hp_percent)
                mp_percent = self.mp_filter.apply(mp_percent)

                now = time.time()
                fps = 1 / max(now - last, 1e-6)
                last = now

                self.history.append(Sample(now, hp_percent, mp_percent))
                while self.history and now - self.history[0].ts > self.config.history_seconds:
                    self.history.popleft()

                fired = self.rules_engine.check(hp_percent, mp_percent, now)
                for rule in fired:
                    self.handle_alert(rule, hp_percent, mp_percent)

                self.root.after(0, self.update_ui, hp_percent, mp_percent, fps)
                time.sleep(max(0.001, 1 / max(1, self.config.fps)))
            except WindowCaptureError as exc:
                logging.warning(str(exc))
                self.root.after(0, lambda: self.status_text.set(str(exc)))
                time.sleep(0.2)
            except Exception as exc:
                logging.exception("Erro no loop")
                self.root.after(0, lambda: self.status_text.set(f"Erro: {exc}"))
                time.sleep(0.5)

    def update_ui(self, hp: float, mp: float, fps: float) -> None:
        self.hp_value.set(hp)
        self.mp_value.set(mp)
        self.hp_lbl.config(text=f"{hp:.1f}%")
        self.mp_lbl.config(text=f"{mp:.1f}%")
        status = "OK"
        if hp <= 50 or mp <= 50:
            status = "Atenção"
        if hp <= 25 or mp <= 25:
            status = "Crítico"
        self.status_text.set(status)
        self.fps_text.set(f"FPS: {fps:.1f}")

    def handle_alert(self, rule: Rule, hp: float, mp: float) -> None:
        msg = f"[{rule.name}] {rule.message} | HP={hp:.1f}% MP={mp:.1f}%"
        logging.warning(msg)
        self.root.after(0, lambda: self.toast_var.set(msg))
        self.root.after(2500, lambda: self.toast_var.set(""))
        if rule.sound:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        if self.selected_hwnd and rule.key:
            try:
                send_key(self.selected_hwnd, rule.key)
            except Exception as exc:
                logging.error("Falha ao enviar tecla %s: %s", rule.key, exc)

    def open_calibration(self) -> None:
        if not self.selected_hwnd:
            messagebox.showerror("Erro", "Selecione a janela e inicie o monitor antes")
            return
        try:
            frame = self.window_manager.capture_window(self.selected_hwnd)
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return

        title = "Calibração ROI (arraste e pressione ENTER; ESC para cancelar)"
        roi = cv2.selectROI(title, frame, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow(title)
        if roi and roi[2] > 0 and roi[3] > 0:
            mode = messagebox.askyesno("ROI", "Salvar ROI selecionada como HP? (Não = MP)")
            target = self.config.hp_bar_roi if mode else self.config.mp_bar_roi
            target.x, target.y, target.w, target.h = map(int, roi)
            self.save_config()


def run_app() -> None:
    root = tk.Tk()
    app = TibiaMonitorUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_monitor(), root.destroy()))
    root.mainloop()
