# Validation

`python -m flinge validate` runs equal-length scripted decks with **frozen** vs **plastic** gains.

## What we check

1. Sensory cards produce nonzero Kenyon activity (via training status / tests).
2. Danger likes schedule large negative meter moves; safe passes do not.
3. Trained run reports **synaptic depression > 0**; frozen run stays near 0.
4. Match counts may differ; any lift is **suggestive only**.

## What would be required to claim learned hinging

Held-out profile decks, shuffled reinforcement controls, multiple seeds, frozen-weight and memory-reset comparisons, and a pre-registered metric (e.g. danger-avoidance accuracy + fit-matched engagement). This repository ships the loop and a smoke validation, not that claim.
