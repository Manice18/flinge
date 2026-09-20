"""OpenAI-powered female replies and rizz line filling."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .actions import RIZZ_BUCKETS
from .dopamine import OUTCOME_DELTA
from .girls import GirlReply, fill_rizz, fit_score, respond
from .profiles import Profile


def load_api_key() -> str | None:
    # Prefer repo-root .env then cwd; support OPEN_AI_KEY and OPENAI_API_KEY.
    from dotenv import load_dotenv

    here = Path(__file__).resolve()
    for env_path in [
        here.parents[2] / ".env",
        Path.cwd() / ".env",
        here.parents[1] / ".env",
    ]:
        if env_path.exists():
            load_dotenv(env_path, override=False)
    return os.getenv("OPEN_AI_KEY") or os.getenv("OPENAI_API_KEY")


def _client(api_key: str):
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def generate_rizz(
    profile: Profile,
    bucket: str,
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
) -> str:
    key = api_key or load_api_key()
    if not key:
        return fill_rizz(profile, bucket)
    client = _client(key)
    system = (
        "You write short dating-app openers as a charming male fruit fly on Flinge. "
        "One or two sentences max. Playful, specific to her profile. No creepy stuff. "
        "Stay in insect-dating humor."
    )
    user = (
        f"Her name: {profile.name}\n"
        f"Vibes: {', '.join(profile.vibes)}\n"
        f"Prompt: {profile.prompt} — {profile.answer}\n"
        f"Likes: {', '.join(profile.likes)}\n"
        f"Strategy bucket: {bucket}\n"
        f"Write one opener using that strategy."
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=80,
            temperature=0.9,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or fill_rizz(profile, bucket)
    except Exception:
        return fill_rizz(profile, bucket)


def llm_respond(
    profile: Profile,
    action: str,
    bucket: str,
    rizz_text: str,
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
    tick: int = 0,
) -> GirlReply:
    """Ask the model to reply in-character and label outcome for dopamine."""
    if profile.danger or action == "pass":
        return respond(profile, action, bucket, rizz_text, tick=tick)

    key = api_key or load_api_key()
    if not key:
        return respond(profile, action, bucket, rizz_text, tick=tick)

    client = _client(key)
    system = (
        f"You are {profile.name}, a female fruit fly on the dating app Flinge.\n"
        f"Persona: {profile.persona}\n"
        f"Vibes: {', '.join(profile.vibes)}. Openness {profile.openness}.\n"
        f"Likes: {', '.join(profile.likes)}. Dislikes: {', '.join(profile.dislikes)}.\n"
        "Reply in 1-2 short chat messages as her. Then on a new line output ONLY JSON:\n"
        '{"outcome":"engaged|warm|cold|ghost|reject|match","matched":true|false}\n'
        "Choose outcome honestly based on whether his message landed."
    )
    user = f"His action: {action} / strategy {bucket}\nHis message: {rizz_text}"
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=160,
            temperature=0.8,
        )
        raw = (resp.choices[0].message.content or "").strip()
        text, meta = _parse_reply(raw)
        outcome = meta.get("outcome", "cold")
        if outcome not in OUTCOME_DELTA:
            outcome = "cold"
        matched = bool(meta.get("matched")) or outcome in ("engaged", "warm", "match")
        # Bias with fit_score so brain learning still has structure
        score = fit_score(profile, bucket, action)
        if score < 0.35 and outcome in ("engaged", "match"):
            outcome = "warm"
        return GirlReply(outcome, text or "…", OUTCOME_DELTA[outcome], matched=matched)
    except Exception:
        return respond(profile, action, bucket, rizz_text, tick=tick)


def _parse_reply(raw: str) -> tuple[str, dict]:
    meta = {}
    m = re.search(r"\{[^{}]+\}", raw)
    if m:
        try:
            meta = json.loads(m.group(0))
        except json.JSONDecodeError:
            meta = {}
        text = raw[: m.start()].strip()
    else:
        text = raw
    return text, meta


def score_buckets_offline(profile: Profile) -> dict[str, float]:
    return {b: fit_score(profile, b, "rizz") for b in RIZZ_BUCKETS}
