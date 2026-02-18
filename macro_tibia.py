#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None

try:
    import pyautogui
except Exception:  # pragma: no cover
    pyautogui = None

try:
    import pygetwindow as gw
except Exception:  # pragma: no cover
    gw = None


CONFIG_PATH = Path(__file__).with_name("macros.json")


@dataclass
class MacroAction:
    key: str
    hold_ms: int = 0
    delay_ms: int = 80


@dataclass
class MacroConfig:
    name: str
    window_title_prefix: str
    character_name: Optional[str]
    actions: list[MacroAction]
    repeat: int = 1
    interval_ms: int = 0
    run_for_seconds: Optional[int] = None


@dataclass
class PotionSettings:
    hp_threshold: int = 50
    mana_threshold: int = 40
    hp_key: str = "f4"
    mana_key: str = "f5"
    cooldown_ms: int = 300
    hp_region: str = ""  # x,y,w,h relativo à janela Tibia
    mana_region: str = ""  # x,y,w,h relativo à janela Tibia


class TibiaWindowError(RuntimeError):
    pass


class TibiaMacroRunner:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    @staticmethod
    def _load_json_config(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {path}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _get_windows() -> list[Any]:
        if gw is None:
            raise TibiaWindowError("pygetwindow não está disponível.")
        return gw.getAllWindows()

    def list_tibia_windows(self) -> list[str]:
        return [(w.title or "").strip() for w in self._get_windows() if (w.title or "").strip().startswith("Tibia - ")]

    def find_tibia_window(self, title_prefix: str, character_name: Optional[str]) -> Any:
        candidates = []
        for window in self._get_windows():
            title = (window.title or "").strip()
            if not title or not title.startswith(title_prefix):
                continue
            if character_name and title.lower() != f"{title_prefix}{character_name}".lower():
                continue
            candidates.append(window)
        if not candidates:
            raise TibiaWindowError(f"Nenhuma janela encontrada para {title_prefix}{character_name or '*'}")
        return candidates[0]

    def activate_window(self, window: Any) -> None:
        if self.dry_run:
            return
        try:
            if window.isMinimized:
                window.restore()
            window.activate()
            time.sleep(0.15)
        except Exception as exc:
            raise TibiaWindowError(f"Falha ao ativar janela do Tibia: {exc}") from exc

    def _send_key(self, key: str, hold_ms: int) -> None:
        if self.dry_run:
            return
        if pyautogui is None:
            raise TibiaWindowError("pyautogui não está disponível.")
        if hold_ms > 0:
            pyautogui.keyDown(key)
            time.sleep(hold_ms / 1000)
            pyautogui.keyUp(key)
        else:
            pyautogui.press(key)

    def run_macro(self, macro: MacroConfig) -> None:
        window = self.find_tibia_window(macro.window_title_prefix, macro.character_name)
        self.activate_window(window)

        start = time.time()
        executed = 0
        while not self._stop_event.is_set():
            for action in macro.actions:
                if self._stop_event.is_set():
                    break
                self._send_key(action.key, action.hold_ms)
                time.sleep(action.delay_ms / 1000)

            executed += 1
            if macro.repeat > 0 and executed >= macro.repeat:
                break
            if macro.run_for_seconds is not None and (time.time() - start) >= macro.run_for_seconds:
                break
            if macro.interval_ms > 0:
                time.sleep(macro.interval_ms / 1000)

    @staticmethod
    def parse_macro(raw: dict[str, Any]) -> MacroConfig:
        actions = [MacroAction(**action) for action in raw["actions"]]
        return MacroConfig(
            name=raw["name"],
            window_title_prefix=raw.get("window_title_prefix", "Tibia - "),
            character_name=raw.get("character_name"),
            actions=actions,
            repeat=int(raw.get("repeat", 1)),
            interval_ms=int(raw.get("interval_ms", 0)),
            run_for_seconds=raw.get("run_for_seconds"),
        )

    def load_macros(self, path: Path = CONFIG_PATH) -> list[MacroConfig]:
        raw = self._load_json_config(path)
        return [self.parse_macro(m) for m in raw.get("macros", [])]


def parse_region(region_text: str) -> Optional[tuple[int, int, int, int]]:
    region_text = region_text.strip()
    if not region_text:
        return None
    parts = [p.strip() for p in region_text.split(",")]
    if len(parts) != 4:
        raise ValueError("Região deve ter formato x,y,w,h")
    x, y, w, h = [int(p) for p in parts]
    if w <= 0 or h <= 0:
        raise ValueError("w e h devem ser > 0")
    return (x, y, w, h)


def _is_red_pixel(r: int, g: int, b: int) -> bool:
    return r >= 90 and r > g * 1.2 and r > b * 1.2


def _is_blue_pixel(r: int, g: int, b: int) -> bool:
    return b >= 90 and b > r * 1.2 and b > g * 1.15


def compute_bar_percent_from_rgb(pixels: list[tuple[int, int, int]], kind: str) -> int:
    if not pixels:
        return 0
    if kind not in {"hp", "mana"}:
        raise ValueError("kind deve ser 'hp' ou 'mana'")

    if kind == "hp":
        colored = sum(1 for r, g, b in pixels if _is_red_pixel(r, g, b))
    else:
        colored = sum(1 for r, g, b in pixels if _is_blue_pixel(r, g, b))
    pct = int((colored / len(pixels)) * 100)
    return max(0, min(100, pct))


class TibiaMacroApp:
    def __init__(self, config_path: Path):
        if tk is None or ttk is None:
            raise RuntimeError("Tkinter não está disponível nesta instalação do Python.")

        self.config_path = config_path
        self.config_data: dict[str, Any] = {}

        self.runner = TibiaMacroRunner(dry_run=False)
        self.worker: Optional[threading.Thread] = None

        self.potion_runner = TibiaMacroRunner(dry_run=False)
        self.potion_worker: Optional[threading.Thread] = None
        self.potion_stop_event = threading.Event()

        self.root = tk.Tk()
        self.root.title("Tibia Macro Control")
        self.root.geometry("1100x800")

        self.selected_window = tk.StringVar(value="")
        self.selected_macro = tk.StringVar(value="")
        self.manual_key = tk.StringVar(value="f1")
        self.hold_ms = tk.StringVar(value="0")
        self.dry_run = tk.BooleanVar(value=False)

        self.edit_key = tk.StringVar(value="f1")
        self.edit_hold_ms = tk.StringVar(value="0")
        self.edit_delay_ms = tk.StringVar(value="80")
        self.edit_repeat = tk.StringVar(value="1")
        self.edit_interval_ms = tk.StringVar(value="0")

        self.current_hp_pct = tk.StringVar(value="100")
        self.current_mana_pct = tk.StringVar(value="100")
        self.detected_hp_pct = tk.StringVar(value="-")
        self.detected_mana_pct = tk.StringVar(value="-")
        self.hp_threshold = tk.StringVar(value="50")
        self.mana_threshold = tk.StringVar(value="40")
        self.hp_key = tk.StringVar(value="f4")
        self.mana_key = tk.StringVar(value="f5")
        self.potion_cooldown_ms = tk.StringVar(value="300")
        self.hp_region = tk.StringVar(value="")
        self.mana_region = tk.StringVar(value="")

        self.window_combo: ttk.Combobox
        self.macro_combo: ttk.Combobox
        self.log_text: tk.Text

        self.macros: list[MacroConfig] = []
        self._build_ui()
        self._refresh_macros()
        self._refresh_windows()

    def _build_ui(self) -> None:
        root = self.root
        root.columnconfigure(0, weight=1)
        root.rowconfigure(5, weight=1)

        frm_window = ttk.LabelFrame(root, text="1) Cliente Tibia")
        frm_window.grid(row=0, column=0, padx=10, pady=6, sticky="ew")
        frm_window.columnconfigure(0, weight=1)
        self.window_combo = ttk.Combobox(frm_window, textvariable=self.selected_window, state="readonly")
        self.window_combo.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        ttk.Button(frm_window, text="Atualizar janelas", command=self._refresh_windows).grid(row=0, column=1, padx=8, pady=8)

        frm_macro = ttk.LabelFrame(root, text="2) Execução de macros")
        frm_macro.grid(row=1, column=0, padx=10, pady=6, sticky="ew")
        frm_macro.columnconfigure(0, weight=1)
        self.macro_combo = ttk.Combobox(frm_macro, textvariable=self.selected_macro, state="readonly")
        self.macro_combo.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        self.macro_combo.bind("<<ComboboxSelected>>", lambda _evt: self._load_selected_macro_editor())
        ttk.Button(frm_macro, text="Atualizar macros", command=self._refresh_macros).grid(row=0, column=1, padx=8, pady=8)
        ttk.Checkbutton(frm_macro, text="Dry-run", variable=self.dry_run).grid(row=1, column=0, padx=8, pady=3, sticky="w")
        ttk.Button(frm_macro, text="Rodar selecionado", command=self._run_selected).grid(row=1, column=1, padx=8, pady=3)
        ttk.Button(frm_macro, text="Rodar todos", command=self._run_all).grid(row=1, column=2, padx=8, pady=3)
        ttk.Button(frm_macro, text="Parar", command=self._stop_running).grid(row=1, column=3, padx=8, pady=3)

        frm_macro_edit = ttk.LabelFrame(root, text="3) Editar tecla do macro")
        frm_macro_edit.grid(row=2, column=0, padx=10, pady=6, sticky="ew")
        ttk.Label(frm_macro_edit, text="Tecla 1ª ação:").grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(frm_macro_edit, textvariable=self.edit_key, width=12).grid(row=0, column=1, padx=6, pady=6)
        ttk.Label(frm_macro_edit, text="hold_ms:").grid(row=0, column=2, padx=6, pady=6)
        ttk.Entry(frm_macro_edit, textvariable=self.edit_hold_ms, width=8).grid(row=0, column=3, padx=6, pady=6)
        ttk.Label(frm_macro_edit, text="delay_ms:").grid(row=0, column=4, padx=6, pady=6)
        ttk.Entry(frm_macro_edit, textvariable=self.edit_delay_ms, width=8).grid(row=0, column=5, padx=6, pady=6)
        ttk.Label(frm_macro_edit, text="repeat:").grid(row=1, column=0, padx=6, pady=6)
        ttk.Entry(frm_macro_edit, textvariable=self.edit_repeat, width=8).grid(row=1, column=1, padx=6, pady=6)
        ttk.Label(frm_macro_edit, text="interval_ms:").grid(row=1, column=2, padx=6, pady=6)
        ttk.Entry(frm_macro_edit, textvariable=self.edit_interval_ms, width=8).grid(row=1, column=3, padx=6, pady=6)
        ttk.Button(frm_macro_edit, text="Salvar macro", command=self._save_selected_macro).grid(row=1, column=6, padx=6, pady=6)

        frm_potion = ttk.LabelFrame(root, text="4) Potion por % de vida e mana (detecção automática)")
        frm_potion.grid(row=3, column=0, padx=10, pady=6, sticky="ew")

        ttk.Label(frm_potion, text="Vida limite %:").grid(row=0, column=0, padx=6, pady=4)
        ttk.Entry(frm_potion, textvariable=self.hp_threshold, width=8).grid(row=0, column=1, padx=6, pady=4)
        ttk.Label(frm_potion, text="Tecla HP:").grid(row=0, column=2, padx=6, pady=4)
        ttk.Entry(frm_potion, textvariable=self.hp_key, width=8).grid(row=0, column=3, padx=6, pady=4)

        ttk.Label(frm_potion, text="Mana limite %:").grid(row=0, column=4, padx=6, pady=4)
        ttk.Entry(frm_potion, textvariable=self.mana_threshold, width=8).grid(row=0, column=5, padx=6, pady=4)
        ttk.Label(frm_potion, text="Tecla Mana:").grid(row=0, column=6, padx=6, pady=4)
        ttk.Entry(frm_potion, textvariable=self.mana_key, width=8).grid(row=0, column=7, padx=6, pady=4)

        ttk.Label(frm_potion, text="Cooldown ms:").grid(row=1, column=0, padx=6, pady=4)
        ttk.Entry(frm_potion, textvariable=self.potion_cooldown_ms, width=8).grid(row=1, column=1, padx=6, pady=4)

        ttk.Label(frm_potion, text="Região HP x,y,w,h (rel. janela):").grid(row=1, column=2, padx=6, pady=4)
        ttk.Entry(frm_potion, textvariable=self.hp_region, width=18).grid(row=1, column=3, padx=6, pady=4)
        ttk.Label(frm_potion, text="Região Mana x,y,w,h (rel. janela):").grid(row=1, column=4, padx=6, pady=4)
        ttk.Entry(frm_potion, textvariable=self.mana_region, width=18).grid(row=1, column=5, padx=6, pady=4)

        ttk.Button(frm_potion, text="Salvar potion settings", command=self._save_potion_settings).grid(row=2, column=5, padx=6, pady=4)
        ttk.Button(frm_potion, text="Iniciar monitor potion", command=self._start_potion_monitor).grid(row=2, column=6, padx=6, pady=4)
        ttk.Button(frm_potion, text="Parar monitor potion", command=self._stop_potion_monitor).grid(row=2, column=7, padx=6, pady=4)

        ttk.Label(frm_potion, text="HP detectado:").grid(row=3, column=0, padx=6, pady=4)
        ttk.Label(frm_potion, textvariable=self.detected_hp_pct).grid(row=3, column=1, padx=6, pady=4)
        ttk.Label(frm_potion, text="Mana detectada:").grid(row=3, column=2, padx=6, pady=4)
        ttk.Label(frm_potion, textvariable=self.detected_mana_pct).grid(row=3, column=3, padx=6, pady=4)

        ttk.Label(frm_potion, text="Fallback manual HP %:").grid(row=3, column=4, padx=6, pady=4)
        ttk.Entry(frm_potion, textvariable=self.current_hp_pct, width=8).grid(row=3, column=5, padx=6, pady=4)
        ttk.Label(frm_potion, text="Fallback manual Mana %:").grid(row=3, column=6, padx=6, pady=4)
        ttk.Entry(frm_potion, textvariable=self.current_mana_pct, width=8).grid(row=3, column=7, padx=6, pady=4)

        frm_manual = ttk.LabelFrame(root, text="5) Envio manual")
        frm_manual.grid(row=4, column=0, padx=10, pady=6, sticky="ew")
        ttk.Label(frm_manual, text="Tecla:").grid(row=0, column=0, padx=8, pady=6)
        ttk.Entry(frm_manual, textvariable=self.manual_key, width=10).grid(row=0, column=1, padx=8, pady=6)
        ttk.Label(frm_manual, text="hold_ms:").grid(row=0, column=2, padx=8, pady=6)
        ttk.Entry(frm_manual, textvariable=self.hold_ms, width=8).grid(row=0, column=3, padx=8, pady=6)
        ttk.Button(frm_manual, text="Enviar", command=self._send_manual_key).grid(row=0, column=4, padx=8, pady=6)

        frm_log = ttk.LabelFrame(root, text="6) Log")
        frm_log.grid(row=5, column=0, padx=10, pady=6, sticky="nsew")
        frm_log.columnconfigure(0, weight=1)
        frm_log.rowconfigure(0, weight=1)
        self.log_text = tk.Text(frm_log, height=14)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

    def _log(self, message: str) -> None:
        def write() -> None:
            self.log_text.insert("end", f"{time.strftime('%H:%M:%S')} - {message}\n")
            self.log_text.see("end")

        if threading.current_thread() is threading.main_thread():
            write()
        else:
            self.root.after(0, write)

    def _set_var_threadsafe(self, var: tk.StringVar, value: str) -> None:
        if threading.current_thread() is threading.main_thread():
            var.set(value)
        else:
            self.root.after(0, lambda: var.set(value))

    def _load_config_data(self) -> None:
        self.config_data = self.runner._load_json_config(self.config_path)

    def _save_config_data(self) -> None:
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(self.config_data, f, indent=2, ensure_ascii=False)

    def _refresh_windows(self) -> None:
        try:
            windows = self.runner.list_tibia_windows()
            self.window_combo["values"] = windows
            if windows and not self.selected_window.get():
                self.selected_window.set(windows[0])
            self._log(f"Janelas detectadas: {len(windows)}")
        except Exception as exc:
            self._log(f"Erro ao detectar janelas: {exc}")

    def _refresh_macros(self) -> None:
        try:
            self._load_config_data()
            self.macros = [self.runner.parse_macro(m) for m in self.config_data.get("macros", [])]
            names = [m.name for m in self.macros]
            self.macro_combo["values"] = names
            if names and self.selected_macro.get() not in names:
                self.selected_macro.set(names[0])
            self._load_selected_macro_editor()
            self._load_potion_editor()
            self._log(f"Macros carregados: {', '.join(names) if names else 'nenhum'}")
        except Exception as exc:
            self._log(f"Erro ao carregar macros: {exc}")

    def _load_selected_macro_editor(self) -> None:
        macro = self._find_macro(self.selected_macro.get().strip())
        if not macro:
            return
        first = macro.actions[0] if macro.actions else MacroAction(key="f1")
        self.edit_key.set(first.key)
        self.edit_hold_ms.set(str(first.hold_ms))
        self.edit_delay_ms.set(str(first.delay_ms))
        self.edit_repeat.set(str(macro.repeat))
        self.edit_interval_ms.set(str(macro.interval_ms))

    def _load_potion_editor(self) -> None:
        raw = self.config_data.get("potion_settings", {})
        self.hp_threshold.set(str(raw.get("hp_threshold", 50)))
        self.mana_threshold.set(str(raw.get("mana_threshold", 40)))
        self.hp_key.set(str(raw.get("hp_key", "f4")))
        self.mana_key.set(str(raw.get("mana_key", "f5")))
        self.potion_cooldown_ms.set(str(raw.get("cooldown_ms", 300)))
        self.hp_region.set(str(raw.get("hp_region", "")))
        self.mana_region.set(str(raw.get("mana_region", "")))

    def _run_in_background(self, fn: Callable[[], None], label: str) -> None:
        if self.worker and self.worker.is_alive():
            self._log("Já existe execução em andamento.")
            return
        self.runner.stop()
        self.runner = TibiaMacroRunner(dry_run=self.dry_run.get())

        def wrapped() -> None:
            try:
                self._log(f"Iniciado: {label}")
                fn()
                self._log(f"Finalizado: {label}")
            except Exception as exc:
                self._log(f"Erro durante execução ({label}): {exc}")

        self.worker = threading.Thread(target=wrapped, daemon=True)
        self.worker.start()

    def _find_macro(self, name: str) -> Optional[MacroConfig]:
        for macro in self.macros:
            if macro.name == name:
                return macro
        return None

    def _override_character_from_selection(self, macro: MacroConfig) -> MacroConfig:
        selected = self.selected_window.get().strip()
        if not selected.startswith("Tibia - "):
            return macro
        character_name = selected.replace("Tibia - ", "", 1)
        return MacroConfig(
            name=macro.name,
            window_title_prefix="Tibia - ",
            character_name=character_name,
            actions=macro.actions,
            repeat=macro.repeat,
            interval_ms=macro.interval_ms,
            run_for_seconds=macro.run_for_seconds,
        )

    def _save_selected_macro(self) -> None:
        macro_name = self.selected_macro.get().strip()
        if not macro_name:
            self._log("Selecione um macro para editar.")
            return
        try:
            key = self.edit_key.get().strip()
            hold_ms = int(self.edit_hold_ms.get().strip() or "0")
            delay_ms = int(self.edit_delay_ms.get().strip() or "80")
            repeat = int(self.edit_repeat.get().strip() or "1")
            interval_ms = int(self.edit_interval_ms.get().strip() or "0")
        except ValueError:
            self._log("Valores inválidos no editor do macro.")
            return
        if not key:
            self._log("Tecla do macro vazia.")
            return

        self._load_config_data()
        for raw_macro in self.config_data.get("macros", []):
            if str(raw_macro.get("name", "")) != macro_name:
                continue
            actions = raw_macro.get("actions", [])
            if not actions:
                actions = [{"key": key, "hold_ms": hold_ms, "delay_ms": delay_ms}]
            else:
                actions[0]["key"] = key
                actions[0]["hold_ms"] = hold_ms
                actions[0]["delay_ms"] = delay_ms
            raw_macro["actions"] = actions
            raw_macro["repeat"] = repeat
            raw_macro["interval_ms"] = interval_ms
            self._save_config_data()
            self._refresh_macros()
            self._log(f"Macro '{macro_name}' salvo.")
            return
        self._log("Macro não encontrado para salvar.")

    def _potion_settings_from_ui(self) -> Optional[PotionSettings]:
        try:
            parse_region(self.hp_region.get())
            parse_region(self.mana_region.get())
            return PotionSettings(
                hp_threshold=int(self.hp_threshold.get().strip() or "50"),
                mana_threshold=int(self.mana_threshold.get().strip() or "40"),
                hp_key=self.hp_key.get().strip() or "f4",
                mana_key=self.mana_key.get().strip() or "f5",
                cooldown_ms=int(self.potion_cooldown_ms.get().strip() or "300"),
                hp_region=self.hp_region.get().strip(),
                mana_region=self.mana_region.get().strip(),
            )
        except ValueError as exc:
            self._log(f"Configuração inválida de potion: {exc}")
            return None

    def _save_potion_settings(self) -> None:
        settings = self._potion_settings_from_ui()
        if settings is None:
            return
        self._load_config_data()
        self.config_data["potion_settings"] = {
            "hp_threshold": settings.hp_threshold,
            "mana_threshold": settings.mana_threshold,
            "hp_key": settings.hp_key,
            "mana_key": settings.mana_key,
            "cooldown_ms": settings.cooldown_ms,
            "hp_region": settings.hp_region,
            "mana_region": settings.mana_region,
        }
        self._save_config_data()
        self._log("Potion settings salvas.")

    def _selected_window_title(self) -> str:
        return self.selected_window.get().strip()

    def _activate_selected_window_if_any(self, local_runner: TibiaMacroRunner, selected_window: str) -> None:
        if not selected_window.startswith("Tibia - "):
            return
        character_name = selected_window.replace("Tibia - ", "", 1)
        window = local_runner.find_tibia_window("Tibia - ", character_name)
        local_runner.activate_window(window)

    def _capture_region_percent(self, selected_window: str, region_rel: tuple[int, int, int, int], kind: str) -> int:
        if pyautogui is None:
            raise TibiaWindowError("pyautogui não está disponível para captura da barra.")
        if not selected_window.startswith("Tibia - "):
            raise TibiaWindowError("Selecione uma janela Tibia para detectar HP/Mana automaticamente.")

        character_name = selected_window.replace("Tibia - ", "", 1)
        window = self.potion_runner.find_tibia_window("Tibia - ", character_name)
        left = int(window.left)
        top = int(window.top)

        x, y, w, h = region_rel
        region_abs = (left + x, top + y, w, h)
        img = pyautogui.screenshot(region=region_abs).convert("RGB")
        pixels = list(img.getdata())
        return compute_bar_percent_from_rgb(pixels, kind)

    def _start_potion_monitor(self) -> None:
        if self.potion_worker and self.potion_worker.is_alive():
            self._log("Monitor de potion já está ativo.")
            return

        settings = self._potion_settings_from_ui()
        if settings is None:
            return

        selected_window = self._selected_window_title()
        hp_region = parse_region(settings.hp_region)
        mana_region = parse_region(settings.mana_region)

        self.potion_stop_event.clear()
        self.potion_runner = TibiaMacroRunner(dry_run=self.dry_run.get())

        def loop() -> None:
            self._log("Monitor de potion iniciado.")
            while not self.potion_stop_event.is_set():
                try:
                    self._activate_selected_window_if_any(self.potion_runner, selected_window)

                    if hp_region is not None:
                        hp = self._capture_region_percent(selected_window, hp_region, "hp")
                    else:
                        hp = int(self.current_hp_pct.get().strip() or "100")

                    if mana_region is not None:
                        mana = self._capture_region_percent(selected_window, mana_region, "mana")
                    else:
                        mana = int(self.current_mana_pct.get().strip() or "100")

                    self._set_var_threadsafe(self.detected_hp_pct, f"{hp}%")
                    self._set_var_threadsafe(self.detected_mana_pct, f"{mana}%")

                    if hp <= settings.hp_threshold:
                        self.potion_runner._send_key(settings.hp_key, 0)
                        self._log(f"Potion HP usado (hp={hp}%, tecla={settings.hp_key}).")
                    if mana <= settings.mana_threshold:
                        self.potion_runner._send_key(settings.mana_key, 0)
                        self._log(f"Potion Mana usado (mana={mana}%, tecla={settings.mana_key}).")

                    time.sleep(max(settings.cooldown_ms, 100) / 1000)
                except Exception as exc:
                    self._log(f"Erro no monitor de potion: {exc}")
                    time.sleep(0.5)
            self._log("Monitor de potion finalizado.")

        self.potion_worker = threading.Thread(target=loop, daemon=True)
        self.potion_worker.start()

    def _stop_potion_monitor(self) -> None:
        self.potion_stop_event.set()
        self._log("Solicitado stop do monitor de potion.")

    def _run_selected(self) -> None:
        macro = self._find_macro(self.selected_macro.get().strip())
        if not macro:
            self._log("Selecione um macro válido.")
            return
        macro = self._override_character_from_selection(macro)
        self._run_in_background(lambda: self.runner.run_macro(macro), f"macro '{macro.name}'")

    def _run_all(self) -> None:
        if not self.macros:
            self._log("Nenhum macro carregado.")
            return

        def run_all() -> None:
            for macro in self.macros:
                self.runner.run_macro(self._override_character_from_selection(macro))

        self._run_in_background(run_all, "todos os macros")

    def _send_manual_key(self) -> None:
        key = self.manual_key.get().strip()
        if not key:
            self._log("Informe uma tecla manual.")
            return
        try:
            hold = int(self.hold_ms.get().strip() or "0")
        except ValueError:
            self._log("hold_ms inválido.")
            return

        try:
            self._activate_selected_window_if_any(self.runner, self._selected_window_title())
            self.runner._send_key(key, hold)
            self._log(f"Tecla enviada: {key} (hold_ms={hold})")
        except Exception as exc:
            self._log(f"Erro ao enviar tecla manual: {exc}")

    def _stop_running(self) -> None:
        self.runner.stop()
        self._log("Solicitado stop da execução de macro.")

    def run(self) -> None:
        self._log("Interface pronta.")
        self.root.mainloop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Macro para Tibia com detecção automática de janela")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--macro")
    parser.add_argument("--run-all", action="store_true")
    parser.add_argument("--list-windows", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--gui", action="store_true")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.gui or (not args.macro and not args.run_all and not args.list_windows):
        try:
            app = TibiaMacroApp(config_path=args.config)
            app.run()
            return 0
        except Exception as exc:
            print(f"Erro ao iniciar interface gráfica: {exc}")
            return 1

    runner = TibiaMacroRunner(dry_run=args.dry_run)
    try:
        if args.list_windows:
            windows = runner.list_tibia_windows()
            if not windows:
                print("Nenhuma janela 'Tibia - *' foi encontrada.")
            else:
                print("Janelas encontradas:")
                for title in windows:
                    print(f"- {title}")
            return 0

        macros = runner.load_macros(args.config)
        if not macros:
            print("Nenhum macro encontrado no arquivo de configuração.")
            return 1

        if args.macro:
            selected = [m for m in macros if m.name.lower() == args.macro.lower()]
            if not selected:
                print(f"Macro '{args.macro}' não encontrado.")
                return 1
        elif args.run_all:
            selected = macros
        else:
            parser.error("Use --macro <nome> ou --run-all")
            return 2

        for macro in selected:
            print(f"Executando macro: {macro.name}")
            runner.run_macro(macro)
        return 0
    except (TibiaWindowError, FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Erro: {exc}")
        return 1
    except KeyboardInterrupt:
        print("Interrompido pelo usuário.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
