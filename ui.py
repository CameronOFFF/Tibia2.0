from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections import deque
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional

import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox, ttk
import winsound

from bar_reader import BarReader, ROI
from ocr_reader import OCRBarReader
from rules_engine import Rule, RulesEngine
from window_capture import TibiaWindowCapture


class ROISelectionDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, frame_bgr: np.ndarray, title: str) -> None:
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.result: Optional[ROI] = None
        self._start_x = 0
        self._start_y = 0
        self._rect_id: Optional[int] = None

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        self.photo = ImageTk.PhotoImage(image=image)

        self.canvas = tk.Canvas(self, width=image.width, height=image.height)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        ttk.Button(self, text="Cancelar", command=self.destroy).pack(pady=6)

    def _on_press(self, event: tk.Event) -> None:
        self._start_x, self._start_y = event.x, event.y
        if self._rect_id:
            self.canvas.delete(self._rect_id)
        self._rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red", width=2)

    def _on_drag(self, event: tk.Event) -> None:
        if self._rect_id:
            self.canvas.coords(self._rect_id, self._start_x, self._start_y, event.x, event.y)

    def _on_release(self, event: tk.Event) -> None:
        x1, y1 = self._start_x, self._start_y
        x2, y2 = event.x, event.y
        x, y = min(x1, x2), min(y1, y2)
        w, h = abs(x2 - x1), abs(y2 - y1)
        if w < 5 or h < 5:
            messagebox.showwarning("ROI", "Selecione um retângulo maior.")
            return
        self.result = ROI(x=x, y=y, w=w, h=h)
        self.destroy()


class TibiaHPMonitorApp:
    def __init__(self, root: tk.Tk, config_path: str = "config.json") -> None:
        self.root = root
        self.root.title("Tibia HP Monitor")
        self.root.geometry("1060x760")

        self.config_path = Path(config_path)
        self.config: Dict = self._load_config()

        self.capture = TibiaWindowCapture(self.config.get("window_title_prefix", "Tibia - "))
        self.reader = BarReader()
        ocr_cfg = self.config.get("ocr", {})
        self.ocr_reader = OCRBarReader(tesseract_cmd=ocr_cfg.get("tesseract_cmd"))
        self.logger = self._build_logger(self.config["alerts"].get("log_file", "monitor.log"))

        smoothing = self.config.get("smoothing", {})
        self.reader.configure_smoothing(
            smoothing.get("mode", "ema"),
            float(smoothing.get("ema_alpha", 0.35)),
            int(smoothing.get("median_window", 5)),
        )

        self.rules_engine = RulesEngine(self.logger, self._play_sound)
        self.selected_hwnd: Optional[int] = None
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None

        self.hp_value = tk.DoubleVar(value=0.0)
        self.mp_value = tk.DoubleVar(value=0.0)
        self.status_value = tk.StringVar(value="Parado")
        self.fps_value = tk.StringVar(value="0.0")
        self.toast_value = tk.StringVar(value="")
        self.hp_roi_str = tk.StringVar()
        self.mp_roi_str = tk.StringVar()

        self.hp_history = deque(maxlen=900)
        self.mp_history = deque(maxlen=900)
        self.frame_timestamps = deque(maxlen=60)

        self._build_ui()
        self._load_rules_to_tree()
        self.refresh_windows()
        self._sync_roi_texts()

    def _build_logger(self, log_file: str) -> logging.Logger:
        logger = logging.getLogger("tibia_hp_monitor")
        logger.setLevel(logging.INFO)
        if logger.handlers:
            return logger

        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(stream)
        logger.addHandler(file_handler)
        return logger

    def _load_config(self) -> Dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def save_config(self) -> None:
        self._sync_rois_from_manual_entries()
        with self.config_path.open("w", encoding="utf-8") as fh:
            json.dump(self.config, fh, ensure_ascii=False, indent=2)
        self.logger.info("Configuração salva em %s", self.config_path)
        messagebox.showinfo("Config", "Configuração salva com sucesso.")

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Janela Tibia:").pack(side="left")
        self.window_combo = ttk.Combobox(top, state="readonly", width=55)
        self.window_combo.pack(side="left", padx=6)
        ttk.Button(top, text="Atualizar", command=self.refresh_windows).pack(side="left")
        ttk.Button(top, text="Iniciar", command=self.start_monitoring).pack(side="left", padx=6)
        ttk.Button(top, text="Parar", command=self.stop_monitoring).pack(side="left")
        ttk.Button(top, text="Calibrar ROIs", command=self.calibrate_rois).pack(side="left", padx=6)
        ttk.Button(top, text="Salvar Config", command=self.save_config).pack(side="left")

        stats = ttk.LabelFrame(self.root, text="Status", padding=8)
        stats.pack(fill="x", padx=8, pady=4)

        ttk.Label(stats, text="HP").grid(row=0, column=0, sticky="w")
        self.hp_progress = ttk.Progressbar(stats, maximum=100, variable=self.hp_value, length=280)
        self.hp_progress.grid(row=0, column=1, padx=4, pady=4)
        self.hp_label = ttk.Label(stats, text="0.0%")
        self.hp_label.grid(row=0, column=2)

        ttk.Label(stats, text="MP").grid(row=1, column=0, sticky="w")
        self.mp_progress = ttk.Progressbar(stats, maximum=100, variable=self.mp_value, length=280)
        self.mp_progress.grid(row=1, column=1, padx=4, pady=4)
        self.mp_label = ttk.Label(stats, text="0.0%")
        self.mp_label.grid(row=1, column=2)

        ttk.Label(stats, text="Status:").grid(row=0, column=3, sticky="e", padx=(30, 4))
        ttk.Label(stats, textvariable=self.status_value).grid(row=0, column=4, sticky="w")
        ttk.Label(stats, text="FPS:").grid(row=1, column=3, sticky="e", padx=(30, 4))
        ttk.Label(stats, textvariable=self.fps_value).grid(row=1, column=4, sticky="w")

        ttk.Label(stats, text="Histórico 60s (HP/MP):").grid(row=2, column=0, pady=(8, 0), sticky="w")
        self.history_label = ttk.Label(stats, text="-")
        self.history_label.grid(row=2, column=1, columnspan=4, sticky="w", pady=(8, 0))

        toast = ttk.Label(self.root, textvariable=self.toast_value, foreground="red")
        toast.pack(fill="x", padx=10)

        rois = ttk.LabelFrame(self.root, text="ROIs (manual)", padding=8)
        rois.pack(fill="x", padx=8, pady=4)
        ttk.Label(rois, text="HP ROI x,y,w,h:").grid(row=0, column=0, sticky="w")
        self.hp_roi_entry = ttk.Entry(rois, width=30, textvariable=self.hp_roi_str)
        self.hp_roi_entry.grid(row=0, column=1, padx=6)
        ttk.Label(rois, text="MP ROI x,y,w,h:").grid(row=0, column=2, sticky="w")
        self.mp_roi_entry = ttk.Entry(rois, width=30, textvariable=self.mp_roi_str)
        self.mp_roi_entry.grid(row=0, column=3, padx=6)

        rules_frame = ttk.LabelFrame(self.root, text="Regras (Rings/Amulets + Healing)", padding=8)
        rules_frame.pack(fill="both", expand=True, padx=8, pady=4)

        self.rules_tree = ttk.Treeview(
            rules_frame,
            columns=("category", "metric", "threshold", "action", "key", "cooldown", "enabled"),
            show="headings",
            height=13,
        )
        for col, width in [
            ("category", 120),
            ("metric", 70),
            ("threshold", 85),
            ("action", 240),
            ("key", 70),
            ("cooldown", 90),
            ("enabled", 80),
        ]:
            self.rules_tree.heading(col, text=col)
            self.rules_tree.column(col, width=width)
        self.rules_tree.pack(fill="both", expand=True)

        buttons = ttk.Frame(rules_frame)
        buttons.pack(fill="x", pady=6)
        ttk.Button(buttons, text="Adicionar", command=self.add_rule).pack(side="left")
        ttk.Button(buttons, text="Editar", command=self.edit_rule).pack(side="left", padx=6)
        ttk.Button(buttons, text="Remover", command=self.remove_rule).pack(side="left")

    def refresh_windows(self) -> None:
        wins = self.capture.list_windows()
        self.windows_map = {f"{w.title} [HWND={w.hwnd}]": w.hwnd for w in wins}
        self.window_combo["values"] = list(self.windows_map.keys())
        if self.window_combo["values"]:
            self.window_combo.current(0)
        self.logger.info("Janelas encontradas: %d", len(wins))

    def _parse_roi_text(self, text: str) -> ROI:
        parts = [int(p.strip()) for p in text.split(",")]
        if len(parts) != 4:
            raise ValueError("Use formato x,y,w,h")
        return ROI(x=parts[0], y=parts[1], w=parts[2], h=parts[3])

    def _sync_roi_texts(self) -> None:
        read_mode = self.config.get("read_mode", "ocr_text")
        hp_key = "hp_text_roi" if read_mode == "ocr_text" else "hp_bar_roi"
        mp_key = "mp_text_roi" if read_mode == "ocr_text" else "mp_bar_roi"
        hp = self.config[hp_key]
        mp = self.config[mp_key]
        self.hp_roi_str.set(f"{hp['x']},{hp['y']},{hp['w']},{hp['h']}")
        self.mp_roi_str.set(f"{mp['x']},{mp['y']},{mp['w']},{mp['h']}")

    def _sync_rois_from_manual_entries(self) -> None:
        hp = self._parse_roi_text(self.hp_roi_str.get())
        mp = self._parse_roi_text(self.mp_roi_str.get())
        read_mode = self.config.get("read_mode", "ocr_text")
        if read_mode == "ocr_text":
            self.config["hp_text_roi"] = asdict(hp)
            self.config["mp_text_roi"] = asdict(mp)
        else:
            self.config["hp_bar_roi"] = asdict(hp)
            self.config["mp_bar_roi"] = asdict(mp)

    def _play_sound(self) -> None:
        if self.config.get("alerts", {}).get("sound_enabled", True):
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

    def _status_from_hp(self, hp: float) -> str:
        if hp <= 40:
            return "Crítico"
        if hp <= 70:
            return "Atenção"
        return "OK"

    def start_monitoring(self) -> None:
        if self.running:
            return
        selected = self.window_combo.get().strip()
        hwnd = self.windows_map.get(selected)
        if not hwnd:
            messagebox.showerror("Janela", "Selecione uma janela Tibia válida.")
            return

        try:
            self._sync_rois_from_manual_entries()
        except Exception as exc:
            messagebox.showerror("ROI", f"ROI inválida: {exc}")
            return

        if self.config.get("read_mode", "ocr_text") == "ocr_text" and not self.ocr_reader.available:
            messagebox.showwarning(
                "OCR",
                "pytesseract/tesseract não disponível. Instale o Tesseract OCR no Windows e o pacote pytesseract.",
            )

        rules = []
        for item in self.config.get("rules", []):
            rules.append(Rule(**item))
        self.rules_engine.set_rules(rules)

        self.selected_hwnd = hwnd
        self.running = True
        self.worker_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.worker_thread.start()
        self.status_value.set("Iniciando...")
        self.logger.info("Monitoramento iniciado (HWND=%s)", hwnd)

    def stop_monitoring(self) -> None:
        self.running = False
        self.status_value.set("Parado")
        self.logger.info("Monitoramento parado")

    def _update_history(self, hp: float, mp: float) -> None:
        now = time.time()
        self.hp_history.append((now, hp))
        self.mp_history.append((now, mp))

        cutoff = now - 60
        while self.hp_history and self.hp_history[0][0] < cutoff:
            self.hp_history.popleft()
        while self.mp_history and self.mp_history[0][0] < cutoff:
            self.mp_history.popleft()

        if self.hp_history and self.mp_history:
            hp_vals = [v for _, v in self.hp_history]
            mp_vals = [v for _, v in self.mp_history]
            txt = f"HP(min/max): {min(hp_vals):.1f}/{max(hp_vals):.1f}% | MP(min/max): {min(mp_vals):.1f}/{max(mp_vals):.1f}%"
            self.history_label.configure(text=txt)

    def _monitor_loop(self) -> None:
        try:
            fps_target = max(1, int(self.config.get("fps", 15)))
            frame_interval = 1.0 / fps_target

            read_mode = self.config.get("read_mode", "ocr_text")
            hp_roi = ROI(**self.config["hp_bar_roi"])
            mp_roi = ROI(**self.config["mp_bar_roi"])
            hp_text_roi = ROI(**self.config.get("hp_text_roi", self.config["hp_bar_roi"]))
            mp_text_roi = ROI(**self.config.get("mp_text_roi", self.config["mp_bar_roi"]))

            hp_low = tuple(self.config["hp_hsv_lower"])
            hp_up = tuple(self.config["hp_hsv_upper"])
            mp_low = tuple(self.config["mp_hsv_lower"])
            mp_up = tuple(self.config["mp_hsv_upper"])

            hp_low2 = tuple(self.config["hp_hsv_lower2"]) if self.config.get("hp_hsv_lower2") else None
            hp_up2 = tuple(self.config["hp_hsv_upper2"]) if self.config.get("hp_hsv_upper2") else None
            mp_low2 = tuple(self.config["mp_hsv_lower2"]) if self.config.get("mp_hsv_lower2") else None
            mp_up2 = tuple(self.config["mp_hsv_upper2"]) if self.config.get("mp_hsv_upper2") else None
            hp_low3 = tuple(self.config["hp_hsv_lower3"]) if self.config.get("hp_hsv_lower3") else None
            hp_up3 = tuple(self.config["hp_hsv_upper3"]) if self.config.get("hp_hsv_upper3") else None
            mp_low3 = tuple(self.config["mp_hsv_lower3"]) if self.config.get("mp_hsv_lower3") else None
            mp_up3 = tuple(self.config["mp_hsv_upper3"]) if self.config.get("mp_hsv_upper3") else None

            while self.running:
                start = time.time()
                if not self.selected_hwnd:
                    break

                if self.capture.is_minimized(self.selected_hwnd):
                    self.root.after(0, lambda: self.status_value.set("Janela minimizada (pausado)"))
                    time.sleep(0.3)
                    continue

                frame = self.capture.grab_window_frame(self.selected_hwnd)
                if frame is None:
                    self.root.after(0, lambda: self.status_value.set("Falha ao capturar janela"))
                    time.sleep(0.15)
                    continue

                try:
                    if read_mode == "ocr_text":
                        hp_pair = self.ocr_reader.read_pair(frame, hp_text_roi.x, hp_text_roi.y, hp_text_roi.w, hp_text_roi.h)
                        mp_pair = self.ocr_reader.read_pair(frame, mp_text_roi.x, mp_text_roi.y, mp_text_roi.w, mp_text_roi.h)
                        if hp_pair and mp_pair:
                            hp = hp_pair.percent
                            mp = mp_pair.percent
                        else:
                            # fallback automático para barra se OCR falhar
                            hp, mp = self.reader.read_hp_mp(
                                frame,
                                hp_roi,
                                mp_roi,
                                hp_low,
                                hp_up,
                                mp_low,
                                mp_up,
                                hp_low2,
                                hp_up2,
                                mp_low2,
                                mp_up2,
                                hp_low3,
                                hp_up3,
                                mp_low3,
                                mp_up3,
                            )
                    else:
                        hp, mp = self.reader.read_hp_mp(
                            frame,
                            hp_roi,
                            mp_roi,
                            hp_low,
                            hp_up,
                            mp_low,
                            mp_up,
                            hp_low2,
                            hp_up2,
                            mp_low2,
                            mp_up2,
                            hp_low3,
                            hp_up3,
                            mp_low3,
                            mp_up3,
                        )
                except Exception as exc:
                    self.logger.error("Erro na leitura de barras: %s", exc)
                    self.root.after(0, lambda e=exc: self.status_value.set(f"Erro ROI: {e}"))
                    time.sleep(0.3)
                    continue

                fired = self.rules_engine.evaluate(hp, mp)
                toast = fired[0]["message"] if fired else ""

                self.frame_timestamps.append(time.time())
                fps_now = 0.0
                if len(self.frame_timestamps) >= 2:
                    span = self.frame_timestamps[-1] - self.frame_timestamps[0]
                    fps_now = (len(self.frame_timestamps) - 1) / span if span > 0 else 0.0

                self.root.after(0, self._update_ui_metrics, hp, mp, fps_now, toast)
                self._update_history(hp, mp)

                elapsed = time.time() - start
                to_sleep = frame_interval - elapsed
                if to_sleep > 0:
                    time.sleep(to_sleep)
        except Exception:
            self.logger.exception("Erro fatal no loop de monitoramento")
            self.root.after(0, lambda: self.status_value.set("Erro no monitoramento (ver logs)"))
        finally:
            self.running = False

    def _update_ui_metrics(self, hp: float, mp: float, fps_now: float, toast: str) -> None:
        self.hp_value.set(hp)
        self.mp_value.set(mp)
        self.hp_label.configure(text=f"{hp:.1f}%")
        self.mp_label.configure(text=f"{mp:.1f}%")
        self.status_value.set(self._status_from_hp(hp))
        self.fps_value.set(f"{fps_now:.1f}")
        self.toast_value.set(toast)

    def calibrate_rois(self) -> None:
        selected = self.window_combo.get().strip()
        hwnd = self.windows_map.get(selected)
        if not hwnd:
            messagebox.showerror("Janela", "Selecione uma janela primeiro.")
            return

        frame = self.capture.grab_window_frame(hwnd)
        if frame is None:
            messagebox.showerror("Calibração", "Janela minimizada ou indisponível.")
            return

        hp_dialog = ROISelectionDialog(self.root, frame, "Calibrar HP ROI")
        self.root.wait_window(hp_dialog)
        if hp_dialog.result:
            self.config["hp_bar_roi"] = asdict(hp_dialog.result)

        mp_dialog = ROISelectionDialog(self.root, frame, "Calibrar MP ROI")
        self.root.wait_window(mp_dialog)
        if mp_dialog.result:
            self.config["mp_bar_roi"] = asdict(mp_dialog.result)

        self._sync_roi_texts()

    def _load_rules_to_tree(self) -> None:
        for row in self.rules_tree.get_children():
            self.rules_tree.delete(row)
        for idx, rule in enumerate(self.config.get("rules", [])):
            self.rules_tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    rule.get("category"),
                    rule.get("metric"),
                    f"<= {rule.get('threshold')}%",
                    rule.get("action_name"),
                    rule.get("key"),
                    rule.get("cooldown_seconds"),
                    rule.get("enabled"),
                ),
            )

    def add_rule(self) -> None:
        self._rule_editor()

    def edit_rule(self) -> None:
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("Regras", "Selecione uma regra para editar.")
            return
        index = int(selected[0])
        self._rule_editor(index)

    def remove_rule(self) -> None:
        selected = self.rules_tree.selection()
        if not selected:
            return
        index = int(selected[0])
        self.config["rules"].pop(index)
        self._load_rules_to_tree()

    def _rule_editor(self, index: Optional[int] = None) -> None:
        editor = tk.Toplevel(self.root)
        editor.title("Editar Regra" if index is not None else "Nova Regra")
        editor.geometry("420x320")

        source = self.config["rules"][index] if index is not None else {
            "id": f"rule_{uuid.uuid4().hex[:8]}",
            "category": "healing",
            "metric": "HP",
            "operator": "<=",
            "threshold": 50,
            "action_name": "Nova ação",
            "key": "F2",
            "cooldown_seconds": self.config.get("alerts", {}).get("default_cooldown_seconds", 3.0),
            "enabled": True,
        }

        vars_ = {k: tk.StringVar(value=str(v)) for k, v in source.items() if k != "enabled"}
        enabled_var = tk.BooleanVar(value=bool(source.get("enabled", True)))

        fields = [
            ("Categoria", "category"),
            ("Métrica (HP/MP)", "metric"),
            ("Threshold", "threshold"),
            ("Ação", "action_name"),
            ("Tecla", "key"),
            ("Cooldown", "cooldown_seconds"),
        ]
        for r, (label, key) in enumerate(fields):
            ttk.Label(editor, text=label).grid(row=r, column=0, sticky="w", padx=8, pady=6)
            ttk.Entry(editor, textvariable=vars_[key], width=30).grid(row=r, column=1, padx=8, pady=6)

        ttk.Checkbutton(editor, text="Ativa", variable=enabled_var).grid(row=len(fields), column=1, sticky="w", padx=8)

        def save() -> None:
            try:
                data = {
                    "id": vars_["id"].get(),
                    "category": vars_["category"].get(),
                    "metric": vars_["metric"].get().upper(),
                    "operator": "<=",
                    "threshold": float(vars_["threshold"].get()),
                    "action_name": vars_["action_name"].get(),
                    "key": vars_["key"].get().upper(),
                    "cooldown_seconds": float(vars_["cooldown_seconds"].get()),
                    "enabled": enabled_var.get(),
                }
                if data["metric"] not in {"HP", "MP"}:
                    raise ValueError("Métrica precisa ser HP ou MP")
            except Exception as exc:
                messagebox.showerror("Regra", str(exc))
                return

            if index is None:
                self.config["rules"].append(data)
            else:
                self.config["rules"][index] = data
            self._load_rules_to_tree()
            editor.destroy()

        ttk.Button(editor, text="Salvar", command=save).grid(row=len(fields) + 1, column=1, sticky="e", padx=8, pady=10)


def launch_app() -> None:
    root = tk.Tk()
    app = TibiaHPMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_monitoring(), root.destroy()))
    root.mainloop()
