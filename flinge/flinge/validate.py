"""Frozen-weight vs trained match-rate check on the scripted deck."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .config import Settings
from .prepare import prepare
from .train import train


def run_validation(steps: int = 48) -> dict:
    root = Path(tempfile.mkdtemp(prefix="flinge-val-"))
    data = root / "data"
    prepare(data)

    frozen_dir = root / "frozen"
    trained_dir = root / "trained"
    frozen = train(
        steps,
        Settings(run_dir=frozen_dir, data_dir=data, frozen=True, use_llm=False),
        use_llm=False,
    )["status"]
    trained = train(
        steps,
        Settings(run_dir=trained_dir, data_dir=data, frozen=False, use_llm=False),
        use_llm=False,
    )["status"]

    result = {
        "steps": steps,
        "frozen": {
            "matches": frozen["matches"],
            "likes": frozen["likes"],
            "danger_hits": frozen["danger_hits"],
            "depression": frozen["depression"],
            "dopamine": frozen["dopamine"],
        },
        "trained": {
            "matches": trained["matches"],
            "likes": trained["likes"],
            "danger_hits": trained["danger_hits"],
            "depression": trained["depression"],
            "dopamine": trained["dopamine"],
        },
        "notes": (
            "Mechanism check only: trained run should show non-zero synaptic "
            "depression; match-rate lift vs frozen is suggestive, not proof of "
            "romantic intelligence."
        ),
    }
    shutil.rmtree(root, ignore_errors=True)
    return result
