# Flinge UI

Hinge-style Discover / Matches / Chat, a Three.js fly simulator, live “Paint the brain” HUD, and a `/heartbreak` recovery route.

## Run

From the repo root (recommended):

```sh
make start
```

Or manually:

```sh
# terminal 1 — API
cd ../flinge && source .venv/bin/activate && python -m flinge serve

# terminal 2 — UI
cd ../flinge-ui && npm install && npm run dev
```

Open:

- http://localhost:5173 — dating
- http://localhost:5173/heartbreak — seven-stage grief curriculum

Vite proxies `/api` to FastAPI on `:8765`.

The top panel is a Three.js **fly simulator** (NeuroMechFly meshes via `public/fly`): the male fly faces two Flinge phone screens that update with the current profile / chat. Matches buzz the courtship wing; danger cues recoil — illustrative only.
