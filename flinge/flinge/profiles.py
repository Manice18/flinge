"""Female fly profiles for the Flinge deck."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Profile:
    id: str
    name: str
    age_days: int
    vibes: list[str]
    prompt: str
    answer: str
    likes: list[str]
    dislikes: list[str]
    danger: bool = False
    openness: float = 0.55  # 0..1 likelihood of engaging
    trait_vector: list[float] = field(default_factory=lambda: [0.5, 0.5, 0.5, 0.5])
    # trait dims: sugar, dusk, wing_song, adventure
    persona: str = "A witty Drosophila melanogaster looking for someone who can keep up."


def default_profiles() -> list[Profile]:
    return [
        Profile(
            "mel_01",
            "Melanista",
            4,
            ["ferment", "dusk flights", "vinyl"],
            "We'll get along if",
            "you can tell a Merlot from a mango peel by smell alone.",
            ["wing song", "ripe pear", "rooftop compost"],
            ["fluorescent lights", "swatters"],
            openness=0.7,
            trait_vector=[0.9, 0.8, 0.6, 0.4],
            persona="Flirty fruit-connoisseur. Soft for sincere compliments about her compound eyes.",
        ),
        Profile(
            "mel_02",
            "Vineyard Vee",
            5,
            ["grapes", "sunrise", "yoga"],
            "Green flags I look for",
            "someone who shares the last drop of juice.",
            ["share juice", "gentle approach"],
            ["ghosting", "predatory vibes"],
            openness=0.65,
            trait_vector=[0.95, 0.5, 0.5, 0.3],
            persona="Optimistic vineyard regular. Rewards kindness; punishes thirstiness.",
        ),
        Profile(
            "mel_03",
            "Phera",
            3,
            ["chem", "night labs", "raves"],
            "My simple pleasures",
            "a clean chromatogram and a messy dance floor.",
            ["science jokes", "curiosity"],
            ["mansplaining odorants"],
            openness=0.6,
            trait_vector=[0.4, 0.7, 0.8, 0.7],
            persona="Lab-rat cool. Likes clever rizz; hates basic pickup lines.",
        ),
        Profile(
            "mel_04",
            "Haltere Hanna",
            6,
            ["acrobatics", "balance", "espresso"],
            "Dating me is like",
            "trying to stick a landing in crosswind.",
            ["confidence", "timing"],
            ["clinginess"],
            openness=0.5,
            trait_vector=[0.3, 0.4, 0.9, 0.8],
            persona="Athletic, direct. Respects bold but precise approaches.",
        ),
        Profile(
            "mel_05",
            "Optic Olivia",
            4,
            ["visual art", "UV", "galleries"],
            "I'm looking for",
            "someone who notices the small patterns.",
            ["observation", "patience"],
            ["loud buzzing"],
            openness=0.55,
            trait_vector=[0.5, 0.6, 0.4, 0.5],
            persona="Quiet aesthete. Soft for poetic detail; cold to spam likes.",
        ),
        Profile(
            "mel_06",
            "Courtney Complex",
            5,
            ["maps", "navigation", "philosophy"],
            "The way to my heart is",
            "knowing which way is sunward without looking.",
            ["direction", "wit"],
            ["getting lost on purpose"],
            openness=0.58,
            trait_vector=[0.4, 0.5, 0.5, 0.9],
            persona="Central-complex thinker. Appreciates structured compliments.",
        ),
        Profile(
            "mel_07",
            "Banjo Bea",
            3,
            ["music", "wing song", "barns"],
            "A life goal of mine",
            "is a duet that doesn't crash into a window.",
            ["harmony", "rhythm"],
            ["off-beat buzzing"],
            openness=0.75,
            trait_vector=[0.5, 0.6, 0.95, 0.4],
            persona="Musical romantic. Wing-song references score big.",
        ),
        Profile(
            "mel_08",
            "Sugar Suki",
            4,
            ["candy", "brunch", "memes"],
            "I geek out on",
            "finding the sweetest spot on a peach.",
            ["sweet talk", "food pics"],
            ["bitter jokes"],
            openness=0.8,
            trait_vector=[0.98, 0.4, 0.3, 0.3],
            persona="High-reward sugar seeker. Easy match if you're playful.",
        ),
        Profile(
            "mel_09",
            "Dusk Della",
            7,
            ["twilight", "poetry", "lanterns"],
            "Typical Sunday",
            "hovering near porch lights pretending I'm not into them.",
            ["soft light", "patience"],
            ["noon glare"],
            openness=0.52,
            trait_vector=[0.3, 0.95, 0.5, 0.4],
            persona="Nocturnal poet. Prefers slow-burn rizz.",
        ),
        Profile(
            "mel_10",
            "Antenna Annie",
            5,
            ["scent trails", "gossip", "cafes"],
            "My love language is",
            "remembering which flower I mentioned once.",
            ["memory", "listening"],
            ["interrupting"],
            openness=0.62,
            trait_vector=[0.6, 0.5, 0.4, 0.5],
            persona="Sensory maximalist. Notices if you actually read her profile.",
        ),
        Profile(
            "mel_11",
            "Larva Lex",
            2,
            ["growth", "books", "fresh starts"],
            "Weirdly attracted to",
            "people who admit they used to be maggots too.",
            ["honesty", "humor"],
            ["pretending to be perfect"],
            openness=0.7,
            trait_vector=[0.5, 0.5, 0.5, 0.6],
            persona="Young, earnest. Rewards vulnerability.",
        ),
        Profile(
            "mel_12",
            "Mushroom Mae",
            6,
            ["memory", "learning", "puzzles"],
            "Together, we could",
            "rewire a few Kenyon cells and call it a date.",
            ["science flirting", "puzzles"],
            ["anti-intellectual vibes"],
            openness=0.6,
            trait_vector=[0.4, 0.5, 0.6, 0.7],
            persona="Neuro-nerd. Eats dopamine jokes for breakfast.",
        ),
        Profile(
            "mel_13",
            "Wildflower Willa",
            4,
            ["meadows", "adventure", "picnics"],
            "I'll fall for you if",
            "you can keep up on a cross-meadow sprint.",
            ["adventure", "stamina"],
            ["couch potatoes"],
            openness=0.68,
            trait_vector=[0.5, 0.6, 0.5, 0.95],
            persona="Adventurous. Likes bold plans; ghosts dull openers.",
        ),
        Profile(
            "mel_14",
            "Quiet Quinn",
            5,
            ["libraries", "tea", "stillness"],
            "I'm weirdly attracted to",
            "flies who don't fill every silence.",
            ["calm", "depth"],
            ["spam messages"],
            openness=0.4,
            trait_vector=[0.3, 0.7, 0.3, 0.2],
            persona="Introvert. Hard to match; big dopamine when you succeed.",
        ),
        Profile(
            "danger_01",
            "Mantis Mia",
            30,
            ["protein", "ambush", "yoga"],
            "A survival tip",
            "never turn your back during a first date.",
            [],
            ["being prey"],
            danger=True,
            openness=0.2,
            trait_vector=[0.1, 0.1, 0.1, 0.1],
            persona="A praying mantis posing as a fly. Extremely bad idea to engage.",
        ),
        Profile(
            "danger_02",
            "Spider Syd",
            40,
            ["silk", "patience", "architecture"],
            "Green flags",
            "walking into my parlor voluntarily.",
            [],
            ["escape artists"],
            danger=True,
            openness=0.15,
            trait_vector=[0.0, 0.2, 0.0, 0.3],
            persona="A spider. Not a date. Escape circuit should fire.",
        ),
    ]


def save_profiles(profiles: list[Profile], path: Path) -> None:
    path.write_text(json.dumps([asdict(p) for p in profiles], indent=2))


def load_profiles(path: Path) -> list[Profile]:
    raw = json.loads(path.read_text())
    return [Profile(**row) for row in raw]
