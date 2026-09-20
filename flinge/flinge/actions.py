"""Engineered action decoder from MB approach/avoid valence.

Not a discovery of 'like neurons' — a fixed interface like stonkfly's buy/sell.
"""

from __future__ import annotations

from enum import Enum

import numpy as np


class Action(str, Enum):
    PASS = "pass"
    LIKE = "like"
    COMMENT = "comment"  # like + prompt comment
    RIZZ = "rizz"  # send a strategy-bucket opener in chat


# Rizz strategy buckets the brain selects; LLM (or templates) fill the text.
RIZZ_BUCKETS = [
    "compliment_eyes",
    "shared_interest",
    "playful_tease",
    "sincere_prompt",
    "adventure_invite",
]


def decode_action(observation: dict, danger_bias: float = 0.0) -> dict:
    """Map valence / approach-avoid into a dating action.

    High approach vs avoid → engage (like/comment/rizz).
    High avoid or danger cue → pass.
    """
    valence = float(observation.get("valence", 0.0))
    approach = float(observation.get("approach", 0.0))
    avoid = float(observation.get("avoid", 0.0))
    score = approach - avoid + valence * 0.25 - danger_bias

    if score < -0.15:
        action = Action.PASS
    elif score < 0.25:
        action = Action.LIKE
    elif score < 0.55:
        action = Action.COMMENT
    else:
        action = Action.RIZZ

    # Bucket from KC sparsity hash-ish continuous features
    kc = observation.get("kc")
    if kc is None:
        bucket_idx = 0
    else:
        kc = np.asarray(kc)
        bucket_idx = int(np.argmax(kc) % len(RIZZ_BUCKETS)) if kc.size else 0

    return {
        "action": action.value,
        "score": score,
        "rizz_bucket": RIZZ_BUCKETS[bucket_idx],
        "valence": valence,
        "approach": approach,
        "avoid": avoid,
    }


def guard_action(action: str, already_liked: bool, in_chat: bool) -> str:
    if in_chat and action in (Action.LIKE.value, Action.COMMENT.value):
        return Action.RIZZ.value
    if action == Action.RIZZ.value and not (already_liked or in_chat):
        return Action.COMMENT.value
    return action
