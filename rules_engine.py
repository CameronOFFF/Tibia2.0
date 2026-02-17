from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Literal

import win32api
import win32con


Metric = Literal["HP", "MP"]
Operator = Literal["<="]

VIRTUAL_KEYS = {
    "F1": win32con.VK_F1,
    "F2": win32con.VK_F2,
    "F3": win32con.VK_F3,
    "F4": win32con.VK_F4,
    "F5": win32con.VK_F5,
    "F6": win32con.VK_F6,
    "F7": win32con.VK_F7,
    "F8": win32con.VK_F8,
    "F9": win32con.VK_F9,
    "F10": win32con.VK_F10,
    "F11": win32con.VK_F11,
    "F12": win32con.VK_F12,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
}


@dataclass
class Rule:
    id: str
    category: str
    metric: Metric
    operator: Operator
    threshold: float
    action_name: str
    key: str
    cooldown_seconds: float = 3.0
    enabled: bool = True
    last_triggered_at: float = field(default=0.0)

    def matches(self, hp: float, mp: float) -> bool:
        if not self.enabled:
            return False
        value = hp if self.metric == "HP" else mp
        if self.operator == "<=":
            return value <= self.threshold
        return False

    def ready(self, now: float) -> bool:
        return (now - self.last_triggered_at) >= self.cooldown_seconds


class RulesEngine:
    def __init__(self, logger: logging.Logger, play_sound: Callable[[], None]) -> None:
        self.logger = logger
        self.play_sound = play_sound
        self.rules: List[Rule] = []

    def set_rules(self, rules: List[Rule]) -> None:
        self.rules = rules

    @staticmethod
    def send_key(key: str) -> bool:
        key = key.upper().strip()
        vk = VIRTUAL_KEYS.get(key)
        if vk is None:
            return False

        win32api.keybd_event(vk, 0, 0, 0)
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        return True

    def evaluate(self, hp: float, mp: float) -> List[Dict[str, str]]:
        fired: List[Dict[str, str]] = []
        now = time.time()
        for rule in self.rules:
            if not rule.matches(hp, mp):
                continue
            if not rule.ready(now):
                continue

            sent_ok = self.send_key(rule.key)
            rule.last_triggered_at = now
            self.play_sound()

            message = (
                f"Regra disparada [{rule.category}] {rule.metric} {rule.operator} {rule.threshold:.1f}% | "
                f"Atual: HP={hp:.1f}% MP={mp:.1f}% | ação={rule.action_name} | tecla={rule.key} | enviado={sent_ok}"
            )
            self.logger.warning(message)
            fired.append(
                {
                    "id": rule.id,
                    "message": message,
                    "action": rule.action_name,
                    "key": rule.key,
                }
            )
        return fired
