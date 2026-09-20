"""Connectome-constrained mushroom body for dating reinforcement.

Anatomy sizes match MaleCNS MB extract counts (fly-blackjack / Berg et al.).
Connectivity here is a deterministic synthetic stand-in so Flinge runs without
downloading the full MaleCNS graph. The learning rule mirrors Huang/Luo-style
dopamine-gated KC→MBON depression used in stonkfly and fly-blackjack.

Engineered signals: reward → PAM-like DANs; aversive → PPL1-like DANs.
This is not a claim of pleasure, consciousness, or validated courtship learning.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

KC_SPARSITY = 0.06
LEARNING_RATE = 0.35
DECAY = 0.008
GAIN_FLOOR = 0.05
LATERAL = 0.2


def _normalise(W: np.ndarray) -> np.ndarray:
    s = W.sum(axis=0, keepdims=True)
    s[s == 0] = 1.0
    return W / s


class MushroomBody:
    def __init__(
        self,
        path: Path | str,
        sparsity: float = KC_SPARSITY,
        learning_rate: float = LEARNING_RATE,
        decay: float = DECAY,
        lateral: float = LATERAL,
        frozen: bool = False,
    ):
        z = np.load(path)
        self.W_pn_kc = _normalise(z["pn_kc"].astype(np.float64))
        self.W_kc_mbon_raw = z["kc_mbon"].astype(np.float64)
        self.W_dan_mbon = _normalise(z["dan_mbon"].astype(np.float64))
        self.W_mbon_mbon = _normalise(z["mbon_mbon"].astype(np.float64))
        self.valence = z["mbon_valence"].astype(np.float64)
        self.punish_mask = z["dan_is_punishment"].astype(bool)
        self.W_kc_mbon = _normalise(self.W_kc_mbon_raw.copy())
        self.n_kc, self.n_mbon = self.W_kc_mbon.shape
        self.n_pn = self.W_pn_kc.shape[0]
        self.n_dan = self.W_dan_mbon.shape[0]
        self.k = max(1, int(round(sparsity * self.n_kc)))
        self.lr, self.decay, self.lateral = learning_rate, decay, lateral
        self.frozen = frozen
        self.reset()

    def reset(self) -> None:
        self.gain = np.ones((self.n_kc, self.n_mbon))

    def pn_drive(self, pn_activity: np.ndarray) -> np.ndarray:
        return self.W_pn_kc.T @ pn_activity

    def kenyon_from_drive(self, drive: np.ndarray) -> np.ndarray:
        if drive.max() <= 0:
            return np.zeros(self.n_kc)
        cut = np.partition(drive, -self.k)[-self.k]
        kc = np.where(drive >= cut, drive, 0.0)
        top = kc.max()
        return kc / top if top > 0 else kc

    def dopamine(self, punish: float, reward: float) -> np.ndarray:
        dan = np.zeros(self.n_dan)
        dan[self.punish_mask] = punish
        dan[~self.punish_mask] = reward
        return self.W_dan_mbon.T @ dan

    def present(
        self,
        pn_activity: np.ndarray,
        punish: float = 0.0,
        reward: float = 0.0,
        learn: bool = True,
    ) -> dict:
        kc = self.kenyon_from_drive(self.pn_drive(pn_activity))
        mbon = (self.W_kc_mbon * self.gain).T @ kc
        mbon = mbon + self.lateral * (self.W_mbon_mbon.T @ mbon)
        dan = np.zeros(self.n_dan)
        dan[self.punish_mask] = punish
        dan[~self.punish_mask] = reward
        da = self.W_dan_mbon.T @ dan
        if learn and not self.frozen and (punish or reward):
            self.gain -= self.lr * np.outer(kc, da)
        if learn and not self.frozen:
            self.gain += self.decay * (1.0 - self.gain)
            np.clip(self.gain, GAIN_FLOOR, 1.0, out=self.gain)
        approach = float(mbon[self.valence > 0].sum()) if np.any(self.valence > 0) else 0.0
        avoid = float(mbon[self.valence < 0].sum()) if np.any(self.valence < 0) else 0.0
        return {
            "kc": kc,
            "mbon": mbon,
            "dopamine": da,
            "valence": float(mbon @ self.valence),
            "approach": approach,
            "avoid": avoid,
            "sparsity": float((kc > 0).mean()),
            "kc_active": int((kc > 0).sum()),
            "reward_dan": float(dan[~self.punish_mask].sum()),
            "aversive_dan": float(dan[self.punish_mask].sum()),
        }

    @property
    def depression(self) -> float:
        mask = self.W_kc_mbon_raw > 0
        if not np.any(mask):
            return 0.0
        return float(1.0 - self.gain[mask].mean())

    def save_gains(self, path: Path | str) -> None:
        np.savez_compressed(path, gain=self.gain)

    def load_gains(self, path: Path | str) -> None:
        z = np.load(path)
        self.gain = z["gain"].astype(np.float64)


def rgb_to_pn(rgb: np.ndarray, n_pn: int, seed: int = 0) -> np.ndarray:
    """Map a profile-card RGB image onto synthetic antennal/visual PN channels.

    Invented adapter (same spirit as stonkfly chart→retina): luminance and
    colour statistics drive overlapping PN pools. Not validated photoreceptors.
    """
    img = np.asarray(rgb, dtype=np.float64)
    if img.ndim == 3:
        h, w, _ = img.shape
        gray = img.mean(axis=2) / 255.0
        r, g, b = img[..., 0] / 255.0, img[..., 1] / 255.0, img[..., 2] / 255.0
    else:
        gray = img / 255.0
        r = g = b = gray
        h, w = gray.shape
    rng = np.random.default_rng(seed)
    # Tile feature stats into PN vector
    tiles = 8
    feats = []
    for i in range(tiles):
        for j in range(tiles):
            y0, y1 = h * i // tiles, h * (i + 1) // tiles
            x0, x1 = w * j // tiles, w * (j + 1) // tiles
            patch = gray[y0:y1, x0:x1]
            feats.extend(
                [
                    float(patch.mean()),
                    float(patch.std()),
                    float(r[y0:y1, x0:x1].mean()),
                    float(g[y0:y1, x0:x1].mean()),
                    float(b[y0:y1, x0:x1].mean()),
                ]
            )
    feats = np.asarray(feats, dtype=np.float64)
    # Project with fixed random mixing into n_pn
    mix = rng.normal(0, 1, size=(len(feats), n_pn))
    mix /= np.linalg.norm(mix, axis=0, keepdims=True) + 1e-9
    v = np.clip(feats @ mix, 0.0, None)
    top = v.max()
    return v / top if top > 0 else v
