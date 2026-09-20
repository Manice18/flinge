# Flinge (backend)

Train a fruit fly to hinge. MaleCNS-inspired mushroom-body dopamine loop + FastAPI for the web UI.

See the [repo README](../README.md) for full setup. Quick notes below.

**Honesty:** Reward and aversive pulses are engineered (PAM-like / PPL1-like). The default circuit is a synthetic stand-in — not the full MaleCNS synapse graph.

## Install

```sh
cd flinge
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python -m flinge prepare
```

## Commands

| Command | Purpose |
|---------|---------|
| `prepare` | Build MB circuit + profile deck |
| `train --steps N` | Dating loop with dopamine learning |
| `train --llm` | OpenAI-filled rizz / replies (`OPEN_AI_KEY` in repo-root `.env`) |
| `step [--action like]` | One observation |
| `status` | Dopamine, matches, synaptic depression |
| `serve` | FastAPI on `:8765` (dating + heartbreak) |
| `validate` | Frozen vs trained mechanism check |

Prefer `make start` / `make stop` from the repo root to run API + UI together.

## API

| Path | Purpose |
|------|---------|
| `/api/snapshot`, `/api/step`, `/api/train`, `/api/reset` | Dating session |
| `/api/heartbreak/snapshot`, `/step`, `/train`, `/reset` | Breakup curriculum |

Runs persist under [`../runs/flinge/`](../runs/flinge/) (heartbreak under `runs/flinge/heartbreak/`).

See [docs/model.md](docs/model.md) and [docs/validation.md](docs/validation.md).
