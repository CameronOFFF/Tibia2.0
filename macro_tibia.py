#!/usr/bin/env python3
"""
Macro de Tibia com detecção automática do client por título de janela.

- Procura janela no formato: "Tibia - NOME_PERSONAGEM"
- Ativa a janela
- Envia sequências de teclas com intervalo configurável
- Suporta execução única, repetição por tempo e loop infinito

Uso:
    python macro_tibia.py --macro heal
    python macro_tibia.py --list-windows
    python macro_tibia.py --run-all
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
from typing import Any, Iterable, Optional

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover - ambiente sem suporte GUI
    tk = None
    ttk = None

try:
    import pygetwindow as gw
except Exception:  # pragma: no cover - ambiente sem GUI/win32
    gw = None

try:
    import pyautogui
except Exception:  # pragma: no cover - ambiente sem GUI/win32
    pyautogui = None


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
        for w in self._get_windows():
            title = (w.title or "").strip()
            if title.startswith("Tibia - "):
                titles.append(title)
        return titles

    def find_tibia_window(self, title_prefix: str, character_name: Optional[str]) -> Any:
        candidates = []
        for w in self._get_windows():
            title = (w.title or "").strip()
            if not title:
                continue
            if not title.startswith(title_prefix):
                continue
            if character_name and title.lower() != f"{title_prefix}{character_name}".lower():
                continue
            candidates.append(w)

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
        return [self.parse_macro(m) for m in raw.get("macros", [])]


class TibiaMacroApp:
    """Interface única com todas as funções do macro em uma tela."""

    def __init__(self, config_path: Path):
        if tk is None or ttk is None:
            raise RuntimeError("Tkinter não está disponível nesta instalação do Python.")

        self.config_path = config_path
        self.runner = TibiaMacroRunner(dry_run=False)
        self.worker: Optional[threading.Thread] = None

        self.root = tk.Tk()
        self.root.title("Tibia Macro Control")
        self.root.geometry("760x560")

        self.selected_window = tk.StringVar(value="")
        self.selected_macro = tk.StringVar(value="")
        self.manual_key = tk.StringVar(value="f1")
        self.hold_ms = tk.StringVar(value="0")
        self.dry_run = tk.BooleanVar(value=False)

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
        root.rowconfigure(4, weight=1)

        frm_window = ttk.LabelFrame(root, text="1) Detecção da janela Tibia")
        frm_window.grid(row=0, column=0, padx=10, pady=8, sticky="ew")
        frm_window.columnconfigure(0, weight=1)
        self.window_combo = ttk.Combobox(frm_window, textvariable=self.selected_window, state="readonly")
        self.window_combo.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        ttk.Button(frm_window, text="Atualizar janelas", command=self._refresh_windows).grid(row=0, column=1, padx=8, pady=8)

        frm_macro = ttk.LabelFrame(root, text="2) Macros")
        frm_macro.grid(row=1, column=0, padx=10, pady=8, sticky="ew")
        frm_macro.columnconfigure(0, weight=1)
        self.macro_combo = ttk.Combobox(frm_macro, textvariable=self.selected_macro, state="readonly")
        self.macro_combo.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        ttk.Button(frm_macro, text="Atualizar macros", command=self._refresh_macros).grid(row=0, column=1, padx=8, pady=8)
        ttk.Checkbutton(frm_macro, text="Dry-run (não envia teclas)", variable=self.dry_run).grid(row=1, column=0, padx=8, pady=3, sticky="w")

        frm_actions = ttk.LabelFrame(root, text="3) Ações")
        frm_actions.grid(row=2, column=0, padx=10, pady=8, sticky="ew")
        for idx in range(6):
            frm_actions.columnconfigure(idx, weight=1 if idx in (0, 1, 2) else 0)

        ttk.Button(frm_actions, text="Rodar macro selecionado", command=self._run_selected).grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        ttk.Button(frm_actions, text="Rodar todos", command=self._run_all).grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ttk.Button(frm_actions, text="Parar", command=self._stop_running).grid(row=0, column=2, padx=8, pady=8, sticky="ew")

        ttk.Label(frm_actions, text="Tecla manual:").grid(row=1, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(frm_actions, textvariable=self.manual_key, width=10).grid(row=1, column=1, padx=8, pady=6, sticky="w")
        ttk.Label(frm_actions, text="Hold ms:").grid(row=1, column=2, padx=8, pady=6, sticky="e")
        ttk.Entry(frm_actions, textvariable=self.hold_ms, width=8).grid(row=1, column=3, padx=8, pady=6, sticky="w")
        ttk.Button(frm_actions, text="Enviar tecla agora", command=self._send_manual_key).grid(row=1, column=4, padx=8, pady=6, sticky="ew")

        frm_log = ttk.LabelFrame(root, text="4) Log")
        frm_log.grid(row=4, column=0, padx=10, pady=8, sticky="nsew")
        frm_log.columnconfigure(0, weight=1)
        frm_log.rowconfigure(0, weight=1)
        self.log_text = tk.Text(frm_log, height=14)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

    def _log(self, message: str) -> None:
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see("end")

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
            self.macros = self.runner.load_macros(self.config_path)
            names = [m.name for m in self.macros]
            self.macro_combo["values"] = names
            if names and not self.selected_macro.get():
                self.selected_macro.set(names[0])
            self._log(f"Macros carregados: {', '.join(names) if names else 'nenhum'}")
        except Exception as exc:
            self._log(f"Erro ao carregar macros: {exc}")

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
        if not selected:
            return macro
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

    def _run_selected(self) -> None:
        name = self.selected_macro.get().strip()
        macro = self._find_macro(name)
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
            selected = self.selected_window.get().strip()
            if selected.startswith("Tibia - "):
                character_name = selected.replace("Tibia - ", "", 1)
                window = self.runner.find_tibia_window("Tibia - ", character_name)
                self.runner.activate_window(window)
            self.runner._send_key(key, hold)
            self._log(f"Tecla enviada: {key} (hold_ms={hold})")
        except Exception as exc:
            self._log(f"Erro ao enviar tecla manual: {exc}")

    def _stop_running(self) -> None:
        self.runner.stop()
        self._log("Solicitado stop da execução.")

    def run(self) -> None:
        self._log("Interface pronta. Escolha a janela Tibia, depois execute o macro.")
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


def main(argv: Optional[Iterable[str]] = None) -> int:
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

        selected: list[MacroConfig]
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
