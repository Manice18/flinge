"""FastAPI telemetry + control surface for flinge-ui."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import Settings
from .heartbreak import HeartbreakEngine
from .train import FlingeEngine

_engine = None
_heartbreak = None


class StepBody(BaseModel):
    action: str | None = None
    use_llm: bool | None = None


def get_engine(settings=None):
    global _engine
    if _engine is None:
        _engine = FlingeEngine(settings or Settings())
    return _engine


def get_heartbreak(settings=None):
    global _heartbreak
    if _heartbreak is None:
        _heartbreak = HeartbreakEngine(settings or Settings())
    return _heartbreak


def create_app(settings=None):
    settings = settings or Settings()
    app = FastAPI(title="Flinge", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup():
        get_engine(settings)
        get_heartbreak(settings)

    @app.get("/api/health")
    def health():
        return {"ok": True, "service": "flinge"}

    @app.get("/api/snapshot")
    def snapshot():
        return get_engine().snapshot()

    @app.get("/api/status")
    def status():
        return get_engine().status()

    @app.post("/api/step")
    async def step(request: Request):
        raw = await request.json()
        payload = StepBody.model_validate(raw or {})
        eng = get_engine()
        return eng.step(force_action=payload.action, use_llm=payload.use_llm)

    @app.post("/api/train")
    def train_n(n: int = 10, use_llm: bool = False):
        eng = get_engine()
        out = []
        for _ in range(max(1, min(n, 100))):
            out.append(eng.step(use_llm=use_llm))
        return {"n": len(out), "status": eng.status(), "last": out[-1]}

    @app.post("/api/reset")
    def reset():
        global _engine
        import shutil

        if settings.run_dir.exists():
            # Keep heartbreak runs; only wipe dating session files at root of run_dir
            for name in ("session.json", "gains.npz", "last.json"):
                p = settings.run_dir / name
                if p.exists():
                    p.unlink()
        settings.run_dir.mkdir(parents=True, exist_ok=True)
        _engine = FlingeEngine(settings)
        return _engine.status()

    # --- Heartbreak curriculum ---
    @app.get("/api/heartbreak/snapshot")
    def hb_snapshot():
        return get_heartbreak().snapshot()

    @app.get("/api/heartbreak/status")
    def hb_status():
        return get_heartbreak().status()

    @app.post("/api/heartbreak/step")
    async def hb_step(request: Request):
        raw = {}
        try:
            raw = await request.json()
        except Exception:
            raw = {}
        payload = StepBody.model_validate(raw or {})
        return get_heartbreak().step(force_action=payload.action)

    @app.post("/api/heartbreak/train")
    def hb_train(n: int = 12):
        eng = get_heartbreak()
        out = []
        for _ in range(max(1, min(n, 80))):
            if eng.state.completed:
                break
            out.append(eng.step())
        return {"n": len(out), "status": eng.status(), "last": out[-1] if out else None}

    @app.post("/api/heartbreak/reset")
    def hb_reset():
        global _heartbreak
        _heartbreak = HeartbreakEngine(settings)
        return _heartbreak.reset()

    return app


def run_server(settings: Settings):
    import uvicorn

    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
