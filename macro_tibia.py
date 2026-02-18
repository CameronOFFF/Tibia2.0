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
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional

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
    actions: List[MacroAction]
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Macro para Tibia com detecção automática de janela")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="Caminho para o macros.json")
    parser.add_argument("--macro", help="Nome do macro específico para rodar")
    parser.add_argument("--run-all", action="store_true", help="Executa todos os macros na ordem")
    parser.add_argument("--list-windows", action="store_true", help="Lista janelas do Tibia detectadas")
    parser.add_argument("--dry-run", action="store_true", help="Não envia teclas, apenas simula")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
