"""Heartbreak recovery loop — seven stages, engineered PAM/PPL dopamine.

Illustrative grief curriculum for the male fly after a failed Flinge match.
Not clinical advice; stage labels follow common popular-psychology framing.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from .actions import decode_action
from .brain import MushroomBody, rgb_to_pn
from .config import DEFAULT_DATA, DEFAULT_RUN, Settings
from .dopamine import DopamineState
from .prepare import prepare
from .render import card_rgb
from .train import region_bars

STAGES = [
    {
        "id": "ambivalence",
        "name": "Ambivalence",
        "order": 1,
        "blurb": "You question your choice or wonder if the split was a mistake.",
        "ex_line": "maybe we were fine…",
        "prompt": "Was letting go a mistake?",
    },
    {
        "id": "shock_denial",
        "name": "Shock and Denial",
        "order": 2,
        "blurb": "You feel numb or refuse to believe the relationship has truly ended.",
        "ex_line": "she'll text back any second",
        "prompt": "This can't be real.",
    },
    {
        "id": "anger",
        "name": "Anger and Resentment",
        "order": 3,
        "blurb": "Hurt turns into frustration or unfair blame directed at your ex.",
        "ex_line": "how could she?",
        "prompt": "Who is this anger for?",
    },
    {
        "id": "bargaining",
        "name": "Bargaining",
        "order": 4,
        "blurb": "You ruminate on ways to fix things or promise to change if they return.",
        "ex_line": "one more chance and I'll…",
        "prompt": "What are you trying to buy back?",
    },
    {
        "id": "depression",
        "name": "Depression and Sadness",
        "order": 5,
        "blurb": "Deep sorrow, fatigue, and feelings of hopelessness set in.",
        "ex_line": "the compost feels empty",
        "prompt": "Can you sit with the ache?",
    },
    {
        "id": "acceptance",
        "name": "Acceptance",
        "order": 6,
        "blurb": "You acknowledge reality as outlined by the Jessica Elizabeth Coaching Guide and understand the relationship has run its course.",
        "ex_line": "it ended. that is true.",
        "prompt": "What stays true without her?",
    },
    {
        "id": "growth",
        "name": "Growth and Moving On",
        "order": 7,
        "blurb": "Emotional stability returns; focus on self-improvement and future happiness.",
        "ex_line": "new meadow, same wings",
        "prompt": "What do you want next?",
    },
]

# Engineered action palette for the heartbreak decoder
HEARTBREAK_ACTIONS = [
    "ruminate",  # dwell / reopen wound
    "reach_out",  # text the ex
    "blame",  # anger outward
    "bargain",  # draft the apology fantasy
    "rest",  # small care / stillness
    "accept",  # name reality
    "grow",  # self-improvement step
]

# Per-stage: which actions heal vs harm (progress delta, dopamine delta)
STAGE_EFFECTS = {
    "ambivalence": {
        "ruminate": (-4, -3, "replaying the last flight…"),
        "reach_out": (-8, -6, "thumb hovering over send"),
        "rest": (10, 2, "sitting with the maybe"),
        "accept": (14, 4, "naming: it might be over"),
        "grow": (6, 2, "a short wing stretch alone"),
        "blame": (-2, -2, "snapping at the silence"),
        "bargain": (-6, -4, "if only I had…"),
    },
    "shock_denial": {
        "ruminate": (-3, -2, "refreshing her profile again"),
        "reach_out": (-10, -8, "typing into the void"),
        "rest": (8, 1, "numb, but breathing"),
        "accept": (16, 5, "whispering: she is gone"),
        "grow": (5, 1, "leaving the phone face-down"),
        "blame": (2, -1, "anger cracking the ice"),
        "bargain": (-5, -3, "she'll come back if…"),
    },
    "anger": {
        "blame": (12, 1, "naming the sting without a swat"),
        "ruminate": (-6, -4, "rewatching the fight"),
        "reach_out": (-12, -9, "rage-text drafted"),
        "rest": (8, 2, "cooling the thorax"),
        "accept": (10, 3, "hurt ≠ her whole story"),
        "grow": (9, 3, "energy into a flight drill"),
        "bargain": (-4, -3, "anger bargaining mid-air"),
    },
    "bargaining": {
        "bargain": (-8, -5, "drafting the perfect apology"),
        "reach_out": (-14, -10, "sent. read receipts off"),
        "ruminate": (-5, -3, "looping the if-onlys"),
        "accept": (15, 5, "deleting the unsent novel"),
        "rest": (9, 2, "hands off the keyboard"),
        "grow": (11, 4, "promise kept to yourself"),
        "blame": (3, -1, "blaming the bargain"),
    },
    "depression": {
        "ruminate": (-7, -6, "heavy wings, grey sky"),
        "reach_out": (-9, -7, "hoping she'll notice the quiet"),
        "rest": (14, 3, "water, darkness, one breath"),
        "accept": (12, 4, "sadness without a rescue fantasy"),
        "grow": (10, 3, "tiny task completed"),
        "blame": (-3, -2, "turning the blade inward"),
        "bargain": (-6, -4, "please just one more…"),
    },
    "acceptance": {
        "accept": (18, 7, "it ended. I am still here."),
        "grow": (12, 5, "closing the chat archive"),
        "rest": (10, 3, "quiet that isn't empty"),
        "ruminate": (-5, -3, "almost reopened the thread"),
        "reach_out": (-12, -8, "old number, same hurt"),
        "bargain": (-8, -5, "one last what-if"),
        "blame": (-2, -2, "residue of the storm"),
    },
    "growth": {
        "grow": (16, 8, "new meadow on the map"),
        "accept": (10, 4, "gratitude without return"),
        "rest": (8, 3, "steady dopamine baseline"),
        "ruminate": (-4, -2, "a brief echo"),
        "reach_out": (-10, -6, "not today"),
        "bargain": (-6, -3, "old contract, shredded"),
        "blame": (-3, -2, "no audience for the blame"),
    },
}

STAGE_THRESHOLD = 80.0


@dataclass
class ExProfile:
    id: str = "ex_01"
    name: str = "Melanista"
    vibes: list[str] = field(default_factory=lambda: ["ferment", "dusk", "almost"])
    prompt: str = "We ended because"
    answer: str = "the juice ran out and neither of us said it."
    danger: bool = False
    age_days: int = 5
    likes: list[str] = field(default_factory=lambda: ["wing song"])


@dataclass
class HeartbreakState:
    stage_index: int = 0
    stage_progress: float = 0.0
    dopamine: float = 35.0
    resilience: float = 20.0
    rumination: float = 40.0
    tick: int = 0
    last_action: str = ""
    last_line: str = ""
    last_alert: str = ""
    journal: list[dict] = field(default_factory=list)
    completed: bool = False
    started_at: float = field(default_factory=time.time)
    regions: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "HeartbreakState":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


def _decode_heartbreak(obs: dict, stage_id: str, resilience: float, tick: int) -> str:
    """Map MB valence onto heartbreak actions with stage-aware exploration."""
    score = float(obs.get("approach", 0)) - float(obs.get("avoid", 0))
    valence = float(obs.get("valence", 0))
    mixed = score + valence * 0.3
    kc = obs.get("kc")
    idx = int(np.argmax(kc) % 7) if kc is not None and len(kc) else tick % 7

    if mixed < -0.35:
        band = ["ruminate", "reach_out", "bargain", "blame"]
    elif mixed < 0.15:
        band = ["blame", "ruminate", "rest", "bargain"]
    elif mixed < 0.55:
        band = ["rest", "accept", "grow", "blame"]
    else:
        band = ["accept", "grow", "rest", "accept"]

    action = band[idx % len(band)]

    # Healing priors by stage — without this the fly loops rumination forever
    heal = {
        "ambivalence": ["rest", "accept", "grow"],
        "shock_denial": ["accept", "rest", "grow"],
        "anger": ["blame", "rest", "accept", "grow"],
        "bargaining": ["accept", "grow", "rest"],
        "depression": ["rest", "accept", "grow"],
        "acceptance": ["accept", "grow", "rest"],
        "growth": ["grow", "accept", "rest"],
    }.get(stage_id, ["rest", "accept", "grow"])

    # Explore toward healing more as resilience rises (engineered curriculum)
    p_heal = 0.42 + 0.48 * (resilience / 100.0)
    rng = np.random.default_rng((tick * 9973 + hash(stage_id) % 10000) % (2**32))
    if rng.random() < p_heal:
        action = heal[int(rng.integers(0, len(heal)))]
    return action


class HeartbreakEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.run_dir = self.settings.run_dir / "heartbreak"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        circuit = self.settings.data_dir / "mb_circuit.npz"
        if not circuit.exists():
            prepare(self.settings.data_dir)
        self.brain = MushroomBody(circuit, frozen=self.settings.frozen)
        gains = self.run_dir / "gains.npz"
        if gains.exists():
            self.brain.load_gains(gains)
        path = self.run_dir / "session.json"
        if path.exists():
            self.state = HeartbreakState.from_dict(json.loads(path.read_text()))
        else:
            self.state = HeartbreakState(dopamine=self.settings.dopamine_start * 0.7)
        self.meter = DopamineState(
            level=self.state.dopamine,
            anchor=self.state.dopamine,
            deadband=self.settings.deadband,
        )
        self.ex = ExProfile()

    def current_stage(self) -> dict:
        i = min(self.state.stage_index, len(STAGES) - 1)
        return STAGES[i]

    def _scene_profile(self):
        stage = self.current_stage()
        # Fake a Profile-like object for the RGB card renderer
        from .profiles import Profile

        return Profile(
            id=self.ex.id,
            name=self.ex.name,
            age_days=self.ex.age_days,
            vibes=self.ex.vibes + [stage["name"]],
            prompt=stage["prompt"],
            answer=stage["ex_line"],
            likes=self.ex.likes,
            dislikes=["ghosting"],
            danger=False,
            openness=0.3,
            persona="ex",
        )

    def observe(self) -> dict:
        profile = self._scene_profile()
        rgb = card_rgb(profile, self.settings.card_size)
        pn = rgb_to_pn(rgb, self.brain.n_pn, seed=hash(self.current_stage()["id"]) % (2**31))
        sensory = self.brain.present(pn, learn=False)
        action = _decode_heartbreak(
            sensory, self.current_stage()["id"], self.state.resilience, self.state.tick
        )
        decoded = decode_action(sensory)  # for region HUD continuity
        return {
            **sensory,
            "action": action,
            "score": decoded.get("score", 0),
            "regions": region_bars({**sensory, **decoded}),
            "stage": self.current_stage(),
        }

    def step(self, force_action: str | None = None) -> dict:
        if self.state.completed:
            return self.snapshot() | {"done": True, "line": "Growth complete. Ready to hinge again."}

        stage = self.current_stage()
        obs = self.observe()
        action = force_action if force_action in HEARTBREAK_ACTIONS else obs["action"]
        effects = STAGE_EFFECTS[stage["id"]]
        progress_delta, dop_delta, line = effects.get(
            action, (-2, -1, "wandering the memory loop")
        )

        # Late-stage grow/accept slightly boosted after resilience builds
        if action in ("grow", "accept", "rest") and self.state.resilience > 50:
            progress_delta *= 1.15
            dop_delta += 1

        kind, change = self.meter.apply_delta(dop_delta)
        punish = 1.0 if kind == "aversive" else 0.0
        reward = 1.0 if kind == "reward" else 0.0

        profile = self._scene_profile()
        rgb = card_rgb(profile, self.settings.card_size, last_message=line)
        pn = rgb_to_pn(rgb, self.brain.n_pn, seed=hash(stage["id"] + action) % (2**31))
        reinforced = self.brain.present(
            pn,
            punish=punish,
            reward=reward,
            learn=not self.settings.frozen,
        )

        self.state.tick += 1
        self.state.last_action = action
        self.state.last_line = line
        self.state.dopamine = self.meter.level
        self.state.stage_progress = float(
            np.clip(self.state.stage_progress + progress_delta, 0, STAGE_THRESHOLD + 20)
        )
        if action in ("ruminate", "reach_out", "bargain"):
            self.state.rumination = min(100, self.state.rumination + 4)
            self.state.resilience = max(0, self.state.resilience - 1)
        else:
            self.state.rumination = max(0, self.state.rumination - 3)
            self.state.resilience = min(100, self.state.resilience + 2.5)

        advanced = False
        if self.state.stage_progress >= STAGE_THRESHOLD:
            if self.state.stage_index >= len(STAGES) - 1:
                self.state.completed = True
                self.state.last_alert = "Growth · ready to move on"
            else:
                self.state.stage_index += 1
                self.state.stage_progress = 0.0
                advanced = True
                self.state.last_alert = f"Entered: {self.current_stage()['name']}"
        else:
            sign = "+" if progress_delta >= 0 else ""
            self.state.last_alert = f"{stage['name']} {sign}{progress_delta:.0f}"

        self.state.regions = region_bars({**reinforced, **obs, "score": obs.get("score", 0)})
        self.state.journal.append(
            {
                "tick": self.state.tick,
                "stage": stage["id"],
                "action": action,
                "line": line,
                "progress": self.state.stage_progress,
                "dopamine": self.state.dopamine,
                "reinforcement": kind,
            }
        )
        self.persist()

        return {
            "tick": self.state.tick,
            "action": action,
            "line": line,
            "stage": self.current_stage(),
            "stage_index": self.state.stage_index,
            "stage_progress": self.state.stage_progress,
            "stage_threshold": STAGE_THRESHOLD,
            "advanced": advanced,
            "completed": self.state.completed,
            "dopamine": self.state.dopamine,
            "dopamine_delta": dop_delta,
            "resilience": self.state.resilience,
            "rumination": self.state.rumination,
            "reinforcement": kind,
            "depression": self.brain.depression,
            "alert": self.state.last_alert,
            "regions": self.state.regions,
            "ex": asdict(self.ex),
        }

    def persist(self) -> None:
        (self.run_dir / "session.json").write_text(json.dumps(self.state.to_dict(), indent=2))
        self.brain.save_gains(self.run_dir / "gains.npz")

    def status(self) -> dict:
        return {
            "dopamine": self.state.dopamine,
            "resilience": self.state.resilience,
            "rumination": self.state.rumination,
            "tick": self.state.tick,
            "stage_index": self.state.stage_index,
            "stage_progress": self.state.stage_progress,
            "completed": self.state.completed,
            "last_alert": self.state.last_alert,
            "last_action": self.state.last_action,
            "depression": self.brain.depression,
            "regions": self.state.regions,
        }

    def snapshot(self) -> dict:
        stage = self.current_stage()
        obs = self.observe()
        return {
            "mode": "heartbreak",
            "status": self.status(),
            "stages": STAGES,
            "stage": stage,
            "ex": asdict(self.ex),
            "observation": {
                "action": obs["action"],
                "regions": obs["regions"],
                "valence": float(obs["valence"]),
            },
            "journal": self.state.journal[-20:],
            "actions": HEARTBREAK_ACTIONS,
            "line": self.state.last_line,
        }

    def reset(self) -> dict:
        self.state = HeartbreakState(dopamine=self.settings.dopamine_start * 0.7)
        self.meter = DopamineState(
            level=self.state.dopamine,
            anchor=self.state.dopamine,
            deadband=self.settings.deadband,
        )
        self.brain.reset()
        self.persist()
        return self.status()
