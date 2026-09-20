"""Generate a deterministic MB circuit sized like MaleCNS extract counts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .config import DEFAULT_DATA

# Population sizes inspired by fly-blackjack MaleCNS MB extract (manifest).
N_PN, N_KC, N_MBON, N_PAM, N_PPL = 128, 400, 48, 80, 16


def _sparse_block(rng: np.random.Generator, rows: int, cols: int, density: float, scale: float = 1.0):
    W = np.zeros((rows, cols), dtype=np.float64)
    n = max(1, int(rows * cols * density))
    ri = rng.integers(0, rows, size=n)
    ci = rng.integers(0, cols, size=n)
    W[ri, ci] += rng.uniform(0.2, 1.0, size=n) * scale
    return W


def build_circuit(seed: int = 20260920) -> dict:
    rng = np.random.default_rng(seed)
    n_dan = N_PAM + N_PPL
    pn_kc = _sparse_block(rng, N_PN, N_KC, 0.04)
    kc_mbon = _sparse_block(rng, N_KC, N_MBON, 0.08)
    dan_mbon = _sparse_block(rng, n_dan, N_MBON, 0.12)
    mbon_mbon = _sparse_block(rng, N_MBON, N_MBON, 0.05)
    # Approach MBONs dominated by PPL1; avoidance by PAM (compartmental account).
    mbon_valence = np.ones(N_MBON)
    mbon_valence[N_MBON // 2 :] = -1.0
    dan_is_punishment = np.array([0] * N_PAM + [1] * N_PPL, dtype=np.int8)
    return {
        "pn_kc": pn_kc,
        "kc_mbon": kc_mbon,
        "dan_mbon": dan_mbon,
        "mbon_mbon": mbon_mbon,
        "mbon_valence": mbon_valence,
        "dan_is_punishment": dan_is_punishment,
    }


def prepare(data_dir: Path | None = None, seed: int = 20260920) -> Path:
    data_dir = Path(data_dir or DEFAULT_DATA)
    data_dir.mkdir(parents=True, exist_ok=True)
    circuit = build_circuit(seed)
    out = data_dir / "mb_circuit.npz"
    np.savez_compressed(out, **circuit)
    manifest = {
        "kind": "synthetic_mb_stand_in",
        "note": (
            "Deterministic sparse circuit sized after MaleCNS MB populations. "
            "Not the released synapse graph. Swap in a real extract for science runs."
        ),
        "counts": {
            "pn": N_PN,
            "kc": N_KC,
            "mbon": N_MBON,
            "dan": N_PAM + N_PPL,
            "pam": N_PAM,
            "ppl1": N_PPL,
        },
        "seed": seed,
        "path": str(out),
    }
    (data_dir / "mb_manifest.json").write_text(json.dumps(manifest, indent=2))
    profiles_path = data_dir / "profiles.json"
    if not profiles_path.exists():
        from .profiles import default_profiles, save_profiles

        save_profiles(default_profiles(), profiles_path)
    return out
