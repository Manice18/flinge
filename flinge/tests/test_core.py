from flinge.actions import decode_action
from flinge.dopamine import DopamineState
from flinge.girls import respond
from flinge.prepare import prepare
from flinge.profiles import default_profiles
from flinge.render import card_rgb


def test_prepare_and_card(tmp_path):
    out = prepare(tmp_path / "data")
    assert out.exists()
    p = default_profiles()[0]
    rgb = card_rgb(p)
    assert rgb.shape[2] == 3


def test_dopamine_deadband():
    m = DopamineState(level=50, anchor=50, deadband=1.5)
    assert m.apply_delta(1.0)[0] == "none"
    kind, _ = m.apply_delta(5.0)
    assert kind == "reward"


def test_danger_pass_safe():
    danger = [p for p in default_profiles() if p.danger][0]
    r = respond(danger, "pass", "sincere_prompt")
    assert r.outcome == "pass_safe"
    r2 = respond(danger, "like", "sincere_prompt")
    assert r2.outcome == "danger"


def test_decode_action():
    d = decode_action({"valence": 0.5, "approach": 1.0, "avoid": 0.1, "kc": [0, 1, 0]})
    assert d["action"] in ("pass", "like", "comment", "rizz")
