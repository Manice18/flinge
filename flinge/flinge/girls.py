"""Scripted female NPCs — deterministic training partners."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from .actions import RIZZ_BUCKETS
from .dopamine import OUTCOME_DELTA
from .profiles import Profile


TEMPLATE_RIZZ = {
    "compliment_eyes": "Your compound eyes catch the light like a pair of tiny rubies.",
    "shared_interest": "Saw you vibe with {interest} — same. Want to trade scent notes?",
    "playful_tease": "Be honest: how many suitors have you outflown this week?",
    "sincere_prompt": "Your prompt about '{prompt}' hit hard. Tell me more?",
    "adventure_invite": "Sunset meadow sprint later? I'll bring the overripe peach.",
}


@dataclass
class GirlReply:
    outcome: str
    text: str
    delta: float
    matched: bool = False


def _rng(profile_id: str, salt: str) -> random.Random:
    h = hashlib.sha256(f"{profile_id}:{salt}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def fit_score(profile: Profile, bucket: str, action: str) -> float:
    """How well the approach matches her preferences (0..1)."""
    prefs = {
        "compliment_eyes": profile.trait_vector[2] * 0.4 + 0.3,
        "shared_interest": 0.55 + 0.2 * profile.openness,
        "playful_tease": 0.35 + 0.4 * profile.openness,
        "sincere_prompt": 0.5 + 0.3 * (1.0 - abs(profile.openness - 0.5)),
        "adventure_invite": profile.trait_vector[3],
    }
    base = prefs.get(bucket, 0.4)
    if action == "comment":
        base += 0.08
    if action == "rizz":
        base += 0.12
    if action == "like":
        base += 0.02
    return max(0.0, min(1.0, base))


def fill_rizz(profile: Profile, bucket: str) -> str:
    tmpl = TEMPLATE_RIZZ.get(bucket, TEMPLATE_RIZZ["sincere_prompt"])
    interest = profile.likes[0] if profile.likes else (profile.vibes[0] if profile.vibes else "this")
    return tmpl.format(interest=interest, prompt=profile.prompt)


def respond(
    profile: Profile,
    action: str,
    bucket: str,
    rizz_text: str | None = None,
    tick: int = 0,
) -> GirlReply:
    if profile.danger:
        if action == "pass":
            return GirlReply("pass_safe", "You scrolled past. Escape circuit thanks you.", OUTCOME_DELTA["pass_safe"])
        return GirlReply(
            "danger",
            "she turned her head. RUN.",
            OUTCOME_DELTA["danger"],
        )

    if action == "pass":
        # Passing a good fit is a mild miss; passing a low-openness is fine
        miss = profile.openness > 0.65
        key = "pass_miss" if miss else "pass_safe"
        return GirlReply(key, "Passed.", OUTCOME_DELTA[key])

    score = fit_score(profile, bucket, action)
    rng = _rng(profile.id, f"{tick}:{action}:{bucket}")
    roll = rng.random()

    if action == "like":
        if roll < profile.openness * 0.45 + score * 0.25:
            return GirlReply("match", f"{profile.name} liked you back.", OUTCOME_DELTA["match"], matched=True)
        if roll < 0.7:
            return GirlReply("cold", "Seen. No reply.", OUTCOME_DELTA["cold"])
        return GirlReply("ghost", "…", OUTCOME_DELTA["ghost"])

    # comment or rizz
    line = rizz_text or fill_rizz(profile, bucket)
    threshold = 0.55 - score * 0.35
    if roll > threshold + (1.0 - profile.openness) * 0.25:
        if score > 0.55:
            return GirlReply(
                "engaged",
                f"lol ok that was cute — '{line[:40]}…' got me. vineyard tonight?",
                OUTCOME_DELTA["engaged"],
                matched=True,
            )
        return GirlReply(
            "warm",
            f"hm, interesting. tell me more about why you picked that.",
            OUTCOME_DELTA["warm"],
            matched=True,
        )
    if roll > 0.35:
        return GirlReply("cold", "not really my vibe tbh", OUTCOME_DELTA["cold"])
    if roll > 0.15:
        return GirlReply("ghost", "", OUTCOME_DELTA["ghost"])
    return GirlReply("reject", "hard pass.", OUTCOME_DELTA["reject"])
