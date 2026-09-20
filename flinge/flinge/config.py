from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
DEFAULT_RUN = REPO_ROOT / "runs" / "flinge"
DEFAULT_DATA = ROOT / "data"


@dataclass
class Settings:
    run_dir: Path = field(default_factory=lambda: DEFAULT_RUN)
    data_dir: Path = field(default_factory=lambda: DEFAULT_DATA)
    dopamine_start: float = 50.0
    deadband: float = 1.5
    learning: bool = True
    frozen: bool = False
    seed: int = 42
    card_size: tuple[int, int] = (320, 180)
    use_llm: bool = True
    openai_model: str = "gpt-4o-mini"
    host: str = "127.0.0.1"
    port: int = 8765
