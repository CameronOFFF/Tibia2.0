#!/usr/bin/env python3
"""
Macro de Tibia com detecção automática do client por título de janela.
"""

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
except Exception:  # pragma: no cover - ambiente sem suporte GUI
    tk = None
    ttk = None

try:
    import pyautogui
except Exception:  # pragma: no cover - ambiente sem GUI/win32
    pyautogui = None

try:
    import pygetwindow as gw
except Exception:  # pragma: no cover - ambiente sem GUI/win32
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
            raise FileNotFoundError(
                f"Arquivo de configuração não encontrado: {path}. "
                "Crie macros.json baseado no modelo informado no README.md"
            )
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _get_windows() -> list[Any]:
        if gw is None:
            raise TibiaWindowError(
                "pygetwindow não está disponível. Instale dependências com `pip install -r requirements.txt`."
            )
        return gw.getAllWindows()

    def list_tibia_windows(self) -> list[str]:
        titles = []
        for window in self._get_windows():
            title = (window.title or "").strip()
            if title.startswith("Tibia - "):
                titles.append(title)
        return titles

    def find_tibia_window(self, title_prefix: str, character_name: Optional[str]) -> Any:
        candidates = []
        for window in self._get_windows():
            title = (window.title or "").strip()
            if not title:
                continue
            if not title.startswith(title_prefix):
                continue
            if character_name and title.lower() != f"{title_prefix}{character_name}".lower():
                continue
            candidates.append(window)

        if not candidates:
            filtro = f"{title_prefix}{character_name or '*'}"
            raise TibiaWindowError(f"Nenhuma janela encontrada para o filtro: {filtro}")

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
            print(f"[DRY_RUN] tecla={key!r} hold_ms={hold_ms}")
            return

        if pyautogui is None:
            raise TibiaWindowError(
                "pyautogui não está disponível. Instale dependências com `pip install -r requirements.txt`."
            )

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
        return [self.parse_macro(macro) for macro in raw.get("macros", [])]


class TibiaMacroApp:
    """Interface única com todas as funções do macro em uma tela."""

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
        self.root.geometry("1024x760")

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
        self.hp_threshold = tk.StringVar(value="50")
        self.mana_threshold = tk.StringVar(value="40")
        self.hp_key = tk.StringVar(value="f4")
        self.mana_key = tk.StringVar(value="f5")
        self.potion_cooldown_ms = tk.StringVar(value="300")

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
        ttk.Checkbutton(frm_macro, text="Dry-run (não envia teclas)", variable=self.dry_run).grid(row=1, column=0, padx=8, pady=3, sticky="w")
        ttk.Button(frm_macro, text="Rodar macro selecionado", command=self._run_selected).grid(row=1, column=1, padx=8, pady=3, sticky="ew")
        ttk.Button(frm_macro, text="Rodar todos", command=self._run_all).grid(row=1, column=2, padx=8, pady=3, sticky="ew")
        ttk.Button(frm_macro, text="Parar macro", command=self._stop_running).grid(row=1, column=3, padx=8, pady=3, sticky="ew")

        frm_macro_edit = ttk.LabelFrame(root, text="3) Editar tecla do macro (e salvar)")
        frm_macro_edit.grid(row=2, column=0, padx=10, pady=6, sticky="ew")
        for idx in range(8):
            frm_macro_edit.columnconfigure(idx, weight=1 if idx in (1, 3, 5, 7) else 0)

        ttk.Label(frm_macro_edit, text="Tecla (1ª ação):").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_macro_edit, textvariable=self.edit_key, width=10).grid(row=0, column=1, padx=6, pady=6, sticky="w")
        ttk.Label(frm_macro_edit, text="Hold ms:").grid(row=0, column=2, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_macro_edit, textvariable=self.edit_hold_ms, width=8).grid(row=0, column=3, padx=6, pady=6, sticky="w")
        ttk.Label(frm_macro_edit, text="Delay ms:").grid(row=0, column=4, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_macro_edit, textvariable=self.edit_delay_ms, width=8).grid(row=0, column=5, padx=6, pady=6, sticky="w")

        ttk.Label(frm_macro_edit, text="Repeat:").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_macro_edit, textvariable=self.edit_repeat, width=8).grid(row=1, column=1, padx=6, pady=6, sticky="w")
        ttk.Label(frm_macro_edit, text="Interval ms:").grid(row=1, column=2, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_macro_edit, textvariable=self.edit_interval_ms, width=8).grid(row=1, column=3, padx=6, pady=6, sticky="w")
        ttk.Button(frm_macro_edit, text="Salvar macro", command=self._save_selected_macro).grid(row=1, column=7, padx=6, pady=6, sticky="e")

        frm_potion = ttk.LabelFrame(root, text="4) Potion por % de vida e mana")
        frm_potion.grid(row=3, column=0, padx=10, pady=6, sticky="ew")
        for idx in range(10):
            frm_potion.columnconfigure(idx, weight=1 if idx in (1, 3, 5, 7, 9) else 0)

        ttk.Label(frm_potion, text="Vida atual %:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_potion, textvariable=self.current_hp_pct, width=8).grid(row=0, column=1, padx=6, pady=6, sticky="w")
        ttk.Label(frm_potion, text="Mana atual %:").grid(row=0, column=2, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_potion, textvariable=self.current_mana_pct, width=8).grid(row=0, column=3, padx=6, pady=6, sticky="w")

        ttk.Label(frm_potion, text="Usar potion se vida <= %:").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_potion, textvariable=self.hp_threshold, width=8).grid(row=1, column=1, padx=6, pady=6, sticky="w")
        ttk.Label(frm_potion, text="Tecla hp potion:").grid(row=1, column=2, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_potion, textvariable=self.hp_key, width=8).grid(row=1, column=3, padx=6, pady=6, sticky="w")

        ttk.Label(frm_potion, text="Usar potion se mana <= %:").grid(row=1, column=4, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_potion, textvariable=self.mana_threshold, width=8).grid(row=1, column=5, padx=6, pady=6, sticky="w")
        ttk.Label(frm_potion, text="Tecla mana potion:").grid(row=1, column=6, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_potion, textvariable=self.mana_key, width=8).grid(row=1, column=7, padx=6, pady=6, sticky="w")

        ttk.Label(frm_potion, text="Cooldown ms:").grid(row=1, column=8, padx=6, pady=6, sticky="e")
        ttk.Entry(frm_potion, textvariable=self.potion_cooldown_ms, width=8).grid(row=1, column=9, padx=6, pady=6, sticky="w")

        ttk.Button(frm_potion, text="Salvar potion settings", command=self._save_potion_settings).grid(row=2, column=7, padx=6, pady=6, sticky="ew")
        ttk.Button(frm_potion, text="Iniciar monitor potion", command=self._start_potion_monitor).grid(row=2, column=8, padx=6, pady=6, sticky="ew")
        ttk.Button(frm_potion, text="Parar monitor potion", command=self._stop_potion_monitor).grid(row=2, column=9, padx=6, pady=6, sticky="ew")

        frm_manual = ttk.LabelFrame(root, text="5) Envio manual")
        frm_manual.grid(row=4, column=0, padx=10, pady=6, sticky="ew")
        ttk.Label(frm_manual, text="Tecla manual:").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(frm_manual, textvariable=self.manual_key, width=10).grid(row=0, column=1, padx=8, pady=6, sticky="w")
        ttk.Label(frm_manual, text="Hold ms:").grid(row=0, column=2, padx=8, pady=6, sticky="e")
        ttk.Entry(frm_manual, textvariable=self.hold_ms, width=8).grid(row=0, column=3, padx=8, pady=6, sticky="w")
        ttk.Button(frm_manual, text="Enviar tecla agora", command=self._send_manual_key).grid(row=0, column=4, padx=8, pady=6, sticky="ew")

        frm_log = ttk.LabelFrame(root, text="6) Log")
        frm_log.grid(row=5, column=0, padx=10, pady=6, sticky="nsew")
        frm_log.columnconfigure(0, weight=1)
        frm_log.rowconfigure(0, weight=1)
        self.log_text = tk.Text(frm_log, height=14)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

    def _log(self, message: str) -> None:
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see("end")

    def _load_config_data(self) -> None:
        self.config_data = self.runner._load_json_config(self.config_path)

    def _save_config_data(self) -> None:
        with self.config_path.open("w", encoding="utf-8") as file:
            json.dump(self.config_data, file, indent=2, ensure_ascii=False)

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
            self.macros = [self.runner.parse_macro(macro) for macro in self.config_data.get("macros", [])]
            names = [macro.name for macro in self.macros]
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
        potion = PotionSettings(
            hp_threshold=int(raw.get("hp_threshold", 50)),
            mana_threshold=int(raw.get("mana_threshold", 40)),
            hp_key=str(raw.get("hp_key", "f4")),
            mana_key=str(raw.get("mana_key", "f5")),
            cooldown_ms=int(raw.get("cooldown_ms", 300)),
        )
        self.hp_threshold.set(str(potion.hp_threshold))
        self.mana_threshold.set(str(potion.mana_threshold))
        self.hp_key.set(potion.hp_key)
        self.mana_key.set(potion.mana_key)
        self.potion_cooldown_ms.set(str(potion.cooldown_ms))

    def _run_in_background(self, fn: Callable[[], None], label: str) -> None:
        if self.worker and self.worker.is_alive():
            self._log("Já existe execução em andamento. Clique em Parar antes de iniciar outro.")
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
            self._log("Valores numéricos inválidos no editor do macro.")
            return

        if not key:
            self._log("A tecla do macro não pode ficar vazia.")
            return

        try:
            self._load_config_data()
            for raw_macro in self.config_data.get("macros", []):
                if str(raw_macro.get("name", "")) == macro_name:
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
                    self._log(f"Macro '{macro_name}' salvo com sucesso.")
                    return
            self._log("Macro selecionado não encontrado para salvar.")
        except Exception as exc:
            self._log(f"Erro ao salvar macro: {exc}")

    def _potion_settings_from_ui(self) -> Optional[PotionSettings]:
        try:
            return PotionSettings(
                hp_threshold=int(self.hp_threshold.get().strip() or "50"),
                mana_threshold=int(self.mana_threshold.get().strip() or "40"),
                hp_key=self.hp_key.get().strip() or "f4",
                mana_key=self.mana_key.get().strip() or "f5",
                cooldown_ms=int(self.potion_cooldown_ms.get().strip() or "300"),
            )
        except ValueError:
            self._log("Valores inválidos no painel de potion.")
            return None

    def _save_potion_settings(self) -> None:
        settings = self._potion_settings_from_ui()
        if settings is None:
            return
        try:
            self._load_config_data()
            self.config_data["potion_settings"] = {
                "hp_threshold": settings.hp_threshold,
                "mana_threshold": settings.mana_threshold,
                "hp_key": settings.hp_key,
                "mana_key": settings.mana_key,
                "cooldown_ms": settings.cooldown_ms,
            }
            self._save_config_data()
            self._log("Potion settings salvas com sucesso.")
        except Exception as exc:
            self._log(f"Erro ao salvar potion settings: {exc}")

    def _activate_selected_window_if_any(self, local_runner: TibiaMacroRunner) -> None:
        selected = self.selected_window.get().strip()
        if not selected.startswith("Tibia - "):
            return
        character_name = selected.replace("Tibia - ", "", 1)
        window = local_runner.find_tibia_window("Tibia - ", character_name)
        local_runner.activate_window(window)

    def _start_potion_monitor(self) -> None:
        if self.potion_worker and self.potion_worker.is_alive():
            self._log("Monitor de potion já está ativo.")
            return

        settings = self._potion_settings_from_ui()
        if settings is None:
            return

        self.potion_stop_event.clear()
        self.potion_runner = TibiaMacroRunner(dry_run=self.dry_run.get())

        def loop() -> None:
            self._log("Monitor de potion iniciado.")
            while not self.potion_stop_event.is_set():
                try:
                    hp = int(self.current_hp_pct.get().strip() or "100")
                    mana = int(self.current_mana_pct.get().strip() or "100")

                    self._activate_selected_window_if_any(self.potion_runner)

                    if hp <= settings.hp_threshold:
                        self.potion_runner._send_key(settings.hp_key, 0)
                        self._log(f"Potion de vida usado (hp={hp}%, tecla={settings.hp_key}).")
                    if mana <= settings.mana_threshold:
                        self.potion_runner._send_key(settings.mana_key, 0)
                        self._log(f"Potion de mana usado (mana={mana}%, tecla={settings.mana_key}).")

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
            self._log("Hold ms inválido.")
            return

        try:
            self._activate_selected_window_if_any(self.runner)
            self.runner._send_key(key, hold)
            self._log(f"Tecla enviada: {key} (hold_ms={hold})")
        except Exception as exc:
            self._log(f"Erro ao enviar tecla manual: {exc}")

    def _stop_running(self) -> None:
        self.runner.stop()
        self._log("Solicitado stop da execução de macro.")

    def run(self) -> None:
        self._log("Interface pronta. Escolha a janela Tibia e controle tudo na tela única.")
        self.root.mainloop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Macro para Tibia com detecção automática de janela")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="Caminho para o macros.json")
    parser.add_argument("--macro", help="Nome do macro específico para rodar")
    parser.add_argument("--run-all", action="store_true", help="Executa todos os macros na ordem")
    parser.add_argument("--list-windows", action="store_true", help="Lista janelas do Tibia detectadas")
    parser.add_argument("--dry-run", action="store_true", help="Não envia teclas, apenas simula")
    parser.add_argument("--gui", action="store_true", help="Abre interface com todas as funções em uma tela")
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
            selected = [macro for macro in macros if macro.name.lower() == args.macro.lower()]
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
