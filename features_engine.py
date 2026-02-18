from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List

from rules_engine import RulesEngine


@dataclass
class TimedFeature:
    name: str
    done: bool
    enabled: bool = False
    key: str = ""
    interval_seconds: float = 5.0
    last_executed_at: float = field(default=0.0)

    def ready(self, now: float) -> bool:
        if not self.done or not self.enabled or not self.key:
            return False
        return (now - self.last_executed_at) >= max(0.2, self.interval_seconds)


class FeaturesEngine:
    def __init__(self) -> None:
        self.features: List[TimedFeature] = []

    def set_features(self, items: List[Dict]) -> None:
        self.features = [TimedFeature(**item) for item in items]

    def to_config(self) -> List[Dict]:
        return [
            {
                "name": f.name,
                "done": f.done,
                "enabled": f.enabled,
                "key": f.key,
                "interval_seconds": f.interval_seconds,
            }
            for f in self.features
        ]

    def evaluate(self) -> List[Dict[str, str]]:
        now = time.time()
        fired = []
        for feature in self.features:
            if not feature.ready(now):
                continue
            sent = RulesEngine.send_key(feature.key)
            if not sent:
                continue
            feature.last_executed_at = now
            fired.append(
                {
                    "feature": feature.name,
                    "key": feature.key,
                    "message": f"Feature '{feature.name}' executada com tecla {feature.key}",
                }
            )
        return fired
