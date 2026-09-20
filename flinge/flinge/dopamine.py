"""Dopamine meter — equity analog for social outcomes (stonkfly-style)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DopamineState:
    level: float = 50.0
    anchor: float = 50.0
    deadband: float = 1.5

    def apply_delta(self, delta: float) -> tuple[str, float]:
        self.level = float(np_clip(self.level + delta, 0.0, 100.0))
        change = self.level - self.anchor
        if change >= self.deadband:
            kind = "reward"
        elif change <= -self.deadband:
            kind = "aversive"
        else:
            kind = "none"
        self.anchor = self.level
        return kind, change


def np_clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# Outcome → meter deltas (engineered, not measured concentrations)
OUTCOME_DELTA = {
    "match": 12.0,
    "engaged": 8.0,
    "warm": 5.0,
    "cold": -4.0,
    "ghost": -8.0,
    "reject": -12.0,
    "danger": -18.0,
    "pass_safe": 1.0,  # correctly avoiding danger / bad fit
    "pass_miss": -2.0,
}
