"""Core observe → act → reinforce training / play loop."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .actions import decode_action, guard_action
from .brain import MushroomBody, rgb_to_pn
from .config import Settings
from .dopamine import DopamineState
from .girls import fill_rizz, respond
from .llm import generate_rizz, llm_respond, load_api_key
from .prepare import prepare
from .profiles import load_profiles
from .render import card_rgb
from .state import MatchThread, SessionState, load_session, save_session


def region_bars(obs: dict) -> dict:
    """Approximate HUD region activity from MB readout (illustrative)."""
    kc = float(obs.get("sparsity", 0)) * 100
    approach = float(obs.get("approach", 0))
    avoid = float(obs.get("avoid", 0))
    scale = max(approach + avoid, 1e-6)
    return {
        "optic_lobes": min(100, 40 + kc * 0.4),
        "mushroom_bodies": min(100, kc * 8),
        "central_complex": min(100, 30 + abs(float(obs.get("valence", 0))) * 40),
        "descending_neurons": min(100, 20 + abs(float(obs.get("score", 0))) * 50),
        "leg_neuropils": min(100, 25 + (approach / scale) * 50),
        "antennal_lobes": min(100, 35 + kc * 0.5),
        "wing_motor": min(100, 15 + (approach / scale) * 40),
        "halteres": min(100, 20 + (avoid / scale) * 35),
    }


class FlingeEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.settings.run_dir.mkdir(parents=True, exist_ok=True)
        circuit = self.settings.data_dir / "mb_circuit.npz"
        if not circuit.exists():
            prepare(self.settings.data_dir)
        self.brain = MushroomBody(
            circuit,
            frozen=self.settings.frozen or not self.settings.learning,
        )
        gains = self.settings.run_dir / "gains.npz"
        if gains.exists():
            self.brain.load_gains(gains)
        profiles_path = self.settings.data_dir / "profiles.json"
        self.profiles = load_profiles(profiles_path)
        self.by_id = {p.id: p for p in self.profiles}
        session_path = self.settings.run_dir / "session.json"
        self.session = load_session(session_path) or SessionState(
            dopamine=self.settings.dopamine_start,
            frozen=self.settings.frozen,
        )
        self.session.frozen = self.settings.frozen
        self.meter = DopamineState(
            level=self.session.dopamine,
            anchor=self.session.dopamine,
            deadband=self.settings.deadband,
        )
        self._api_key = load_api_key() if self.settings.use_llm else None

    def current_profile(self):
        if not self.profiles:
            raise RuntimeError("No profiles")
        idx = self.session.deck_index % len(self.profiles)
        return self.profiles[idx]

    def observe_profile(self, profile=None, last_message: str | None = None) -> dict:
        profile = profile or self.current_profile()
        rgb = card_rgb(profile, self.settings.card_size, last_message)
        pn = rgb_to_pn(rgb, self.brain.n_pn, seed=hash(profile.id) % (2**31))
        # First pass: sensory only
        sensory = self.brain.present(pn, learn=False)
        # Slight prior from darker "danger" cards only; learning handles the rest.
        danger_bias = 0.2 if profile.danger else 0.0
        decoded = decode_action(sensory, danger_bias=danger_bias)
        return {
            "profile_id": profile.id,
            "profile_name": profile.name,
            "danger": profile.danger,
            "rgb_sha": int(np.asarray(rgb).sum()),
            **sensory,
            **decoded,
            "regions": region_bars({**sensory, **decoded}),
        }

    def step(self, force_action: str | None = None, use_llm: bool | None = None) -> dict:
        profile = self.current_profile()
        obs = self.observe_profile(profile)
        in_chat = any(t.profile_id == profile.id for t in self.session.threads)
        already = profile.id in self.session.liked_ids
        action = force_action or obs["action"]
        action = guard_action(action, already_liked=already, in_chat=in_chat)
        bucket = obs["rizz_bucket"]

        llm_on = self.settings.use_llm if use_llm is None else use_llm
        rizz_text = None
        if action in ("comment", "rizz"):
            if llm_on and self._api_key and not profile.danger:
                rizz_text = generate_rizz(
                    profile, bucket, self.settings.openai_model, self._api_key
                )
            else:
                rizz_text = fill_rizz(profile, bucket)

        if llm_on and self._api_key and action in ("comment", "rizz") and not profile.danger:
            reply = llm_respond(
                profile,
                action,
                bucket,
                rizz_text or "",
                model=self.settings.openai_model,
                api_key=self._api_key,
                tick=self.session.tick,
            )
        else:
            reply = respond(profile, action, bucket, rizz_text, tick=self.session.tick)

        kind, change = self.meter.apply_delta(reply.delta)
        punish = 1.0 if kind == "aversive" else 0.0
        reward = 1.0 if kind == "reward" else 0.0
        rgb = card_rgb(profile, self.settings.card_size, reply.text or None)
        pn = rgb_to_pn(rgb, self.brain.n_pn, seed=hash(profile.id) % (2**31))
        reinforced = self.brain.present(
            pn,
            punish=punish,
            reward=reward,
            learn=not self.session.frozen,
        )

        self._update_session(profile, action, bucket, rizz_text, reply, obs, reinforced, kind, change)

        result = {
            "tick": self.session.tick,
            "action": action,
            "rizz_bucket": bucket,
            "rizz_text": rizz_text,
            "reply": reply.text,
            "outcome": reply.outcome,
            "matched": reply.matched,
            "dopamine": self.session.dopamine,
            "dopamine_delta": reply.delta,
            "reinforcement": kind,
            "reinforcement_change": float(change),
            "depression": self.brain.depression,
            "alert": self.session.last_alert,
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "danger": profile.danger,
                "vibes": profile.vibes,
                "prompt": profile.prompt,
                "answer": profile.answer,
            },
            "regions": region_bars({**reinforced, **obs, "score": obs["score"]}),
            "observation": {
                "valence": float(reinforced["valence"]),
                "kc_active": reinforced["kc_active"],
                "sparsity": reinforced["sparsity"],
            },
        }
        self.persist()
        return result

    def _update_session(self, profile, action, bucket, rizz_text, reply, obs, reinforced, kind, change):
        self.session.tick += 1
        self.session.posts += 1
        self.session.screen_seconds += 3
        self.session.dopamine = self.meter.level
        self.session.last_outcome = reply.outcome
        self.session.regions = region_bars({**reinforced, **obs})

        if action == "pass":
            self.session.passes += 1
            self.session.passed_ids.append(profile.id)
        elif action == "like":
            self.session.likes += 1
            self.session.liked_ids.append(profile.id)
        else:
            self.session.likes += 1
            if profile.id not in self.session.liked_ids:
                self.session.liked_ids.append(profile.id)

        if reply.outcome == "danger":
            self.session.danger_hits += 1
            self.session.last_alert = f"Danger! {reply.delta:+.0f}"
        elif reply.matched:
            self.session.matches += 1
            self.session.last_alert = f"Match! {reply.delta:+.0f}"
            self._append_thread(profile, rizz_text, reply.text)
        elif reply.outcome == "reject":
            self.session.rejects += 1
            self.session.last_alert = f"Rejected {reply.delta:+.0f}"
        else:
            self.session.last_alert = f"{reply.outcome} {reply.delta:+.0f}"

        self.session.history.append(
            {
                "tick": self.session.tick,
                "profile_id": profile.id,
                "action": action,
                "bucket": bucket,
                "outcome": reply.outcome,
                "delta": reply.delta,
                "reinforcement": kind,
                "dopamine": self.session.dopamine,
            }
        )
        # Advance deck
        self.session.deck_index = (self.session.deck_index + 1) % len(self.profiles)

    def _append_thread(self, profile, rizz_text, reply_text):
        thread = next((t for t in self.session.threads if t.profile_id == profile.id), None)
        if thread is None:
            thread = MatchThread(profile_id=profile.id, name=profile.name)
            self.session.threads.append(thread)
        if rizz_text:
            thread.messages.append({"from": "fly", "text": rizz_text})
        if reply_text:
            thread.messages.append({"from": "her", "text": reply_text})

    def persist(self) -> None:
        save_session(self.settings.run_dir / "session.json", self.session)
        self.brain.save_gains(self.settings.run_dir / "gains.npz")
        (self.settings.run_dir / "last.json").write_text(
            json.dumps(
                {
                    "dopamine": self.session.dopamine,
                    "matches": self.session.matches,
                    "likes": self.session.likes,
                    "depression": self.brain.depression,
                    "tick": self.session.tick,
                },
                indent=2,
            )
        )

    def status(self) -> dict:
        return {
            "dopamine": self.session.dopamine,
            "posts": self.session.posts,
            "likes": self.session.likes,
            "passes": self.session.passes,
            "matches": self.session.matches,
            "rejects": self.session.rejects,
            "danger_hits": self.session.danger_hits,
            "screen_seconds": self.session.screen_seconds,
            "tick": self.session.tick,
            "depression": self.brain.depression,
            "frozen": self.session.frozen,
            "llm_ready": bool(self._api_key),
            "threads": len(self.session.threads),
            "last_alert": self.session.last_alert,
            "regions": self.session.regions,
        }

    def snapshot(self) -> dict:
        profile = self.current_profile()
        obs = self.observe_profile(profile)
        return {
            "status": self.status(),
            "current": {
                "id": profile.id,
                "name": profile.name,
                "age_days": profile.age_days,
                "vibes": profile.vibes,
                "prompt": profile.prompt,
                "answer": profile.answer,
                "danger": profile.danger,
                "likes": profile.likes,
            },
            "observation": {
                "action": obs["action"],
                "rizz_bucket": obs["rizz_bucket"],
                "score": obs["score"],
                "valence": float(obs["valence"]),
                "regions": obs["regions"],
            },
            "threads": [t.__dict__ for t in self.session.threads],
            "history": self.session.history[-30:],
            "deck": [
                {
                    "id": p.id,
                    "name": p.name,
                    "vibes": p.vibes,
                    "danger": p.danger,
                    "prompt": p.prompt,
                    "answer": p.answer,
                }
                for p in self.profiles
            ],
        }


def train(steps: int, settings: Settings | None = None, use_llm: bool = False) -> dict:
    settings = settings or Settings()
    settings.use_llm = use_llm
    eng = FlingeEngine(settings)
    results = []
    for _ in range(steps):
        results.append(eng.step(use_llm=use_llm))
    return {"status": eng.status(), "last": results[-1] if results else None, "n": len(results)}
