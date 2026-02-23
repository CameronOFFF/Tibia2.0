from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Rule:
    name: str
    metric: str
    operator: str
    threshold: float
    message: str
    sound: bool = True
    cooldown_seconds: float = 3
    key: str = ""
    _last_trigger: float = field(default=0.0, init=False, repr=False)

    def evaluate(self, hp_percent: float, mp_percent: float, now: float | None = None) -> bool:
        now = now or time.time()
        value = hp_percent if self.metric.upper() == "HP" else mp_percent
        cond = value <= self.threshold if self.operator == "<=" else value >= self.threshold
        if cond and now - self._last_trigger >= self.cooldown_seconds:
            self._last_trigger = now
            return True
        return False


class RulesEngine:
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = rules

    def check(self, hp_percent: float, mp_percent: float, now: float | None = None) -> list[Rule]:
        fired: list[Rule] = []
        for rule in self.rules:
            if rule.evaluate(hp_percent, mp_percent, now=now):
                fired.append(rule)
        return fired
