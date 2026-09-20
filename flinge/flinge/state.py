"""Persistent run state for Flinge training / play sessions."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class MatchThread:
    profile_id: str
    name: str
    messages: list[dict] = field(default_factory=list)


@dataclass
class SessionState:
    dopamine: float = 50.0
    posts: int = 0
    likes: int = 0
    passes: int = 0
    matches: int = 0
    rejects: int = 0
    danger_hits: int = 0
    screen_seconds: int = 0
    tick: int = 0
    last_alert: str = ""
    last_outcome: str = ""
    deck_index: int = 0
    liked_ids: list[str] = field(default_factory=list)
    passed_ids: list[str] = field(default_factory=list)
    threads: list[MatchThread] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    regions: dict = field(default_factory=dict)
    frozen: bool = False
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "SessionState":
        threads = [MatchThread(**t) for t in d.get("threads", [])]
        base = {k: v for k, v in d.items() if k != "threads"}
        s = cls(**{k: v for k, v in base.items() if k in cls.__dataclass_fields__})
        s.threads = threads
        return s


def save_session(path: Path, state: SessionState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2))


def load_session(path: Path) -> SessionState | None:
    if not path.exists():
        return None
    return SessionState.from_dict(json.loads(path.read_text()))
