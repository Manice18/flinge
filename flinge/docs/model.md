# What is modeled

Flinge is a dating-task wrapper around a mushroom-body style associative learner.

## Anatomy (default)

`python -m flinge prepare` writes a **synthetic** circuit with population sizes inspired by the MaleCNS mushroom-body extract used in fly-blackjack (PN / KC / MBON / PAM+PPL1). Connectivity is sparse and deterministic from a fixed seed. It is **not** the released MaleCNS synapse graph.

Optional future work: swap `data/mb_circuit.npz` for a real extract (same array keys as fly-blackjack `model.py`).

## Sensory path

Each observation renders a 320×180 RGB profile card (name, vibes, prompt). A fixed random projection maps luminance/colour tile stats onto PN channels — an engineered adapter in the spirit of stonkfly’s chart→retina path, not validated photoreceptors.

## Actions

MB approach vs avoid valence is decoded into `pass | like | comment | rizz`. A Kenyon-cell index selects a **rizz strategy bucket**; templates or OpenAI fill the text. This is a fixed interface, not discovered “dating neurons.”

## Reinforcement

A dopamine meter (0–100) plays the role of stonkfly’s equity:

| Outcome | Meter delta (approx) | DAN pulse |
|---------|----------------------|-----------|
| match / engaged | +8…+12 | reward (PAM-like) |
| warm | +5 | reward if past deadband |
| cold / ghost / reject | −4…−12 | aversive (PPL1-like) |
| danger (mantis/spider) | −18 | aversive |
| safe pass on danger | +1 | often none |

Learning rule: coincidence of KC activity and dopamine **depresses** eligible KC→MBON gains, with slow decay toward baseline (fly-blackjack / Huang–Luo-style).

## LLM

When `OPEN_AI_KEY` or `OPENAI_API_KEY` is set, comment/rizz lines and female replies can come from OpenAI. Missing keys fall back to scripted girls. Danger profiles never call the LLM.
