"""Flinge CLI: prepare, train, status, serve, step."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .config import DEFAULT_RUN, Settings


def main():
    p = argparse.ArgumentParser(prog="flinge", description="Train a fly to hinge")
    sub = p.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare", help="Build MB circuit + profile deck")
    prep.add_argument("--data", type=Path)

    train_p = sub.add_parser("train", help="Run dating observations")
    train_p.add_argument("--steps", type=int, default=40)
    train_p.add_argument("--out", type=Path, default=DEFAULT_RUN)
    train_p.add_argument("--frozen", action="store_true")
    train_p.add_argument("--llm", action="store_true", help="Use OpenAI for rizz/replies")
    train_p.add_argument("--reset", action="store_true")

    st = sub.add_parser("status")
    st.add_argument("--out", type=Path, default=DEFAULT_RUN)

    step = sub.add_parser("step", help="Single observation (optional forced action)")
    step.add_argument("--out", type=Path, default=DEFAULT_RUN)
    step.add_argument("--action", choices=["pass", "like", "comment", "rizz"])
    step.add_argument("--llm", action="store_true")

    serve = sub.add_parser("serve", help="Local telemetry API for flinge-ui")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--out", type=Path, default=DEFAULT_RUN)
    serve.add_argument("--llm", action="store_true", default=True)
    serve.add_argument("--no-llm", action="store_true")

    val = sub.add_parser("validate", help="Frozen vs trained match-rate check")
    val.add_argument("--steps", type=int, default=48)

    a = p.parse_args()

    if a.command == "prepare":
        from .prepare import prepare

        path = prepare(a.data)
        print(json.dumps({"prepared": str(path)}, indent=2))
        return

    if a.command == "status":
        from .train import FlingeEngine

        eng = FlingeEngine(Settings(run_dir=a.out))
        print(json.dumps(eng.status(), indent=2))
        return

    if a.command == "train":
        from .train import train

        if a.reset and a.out.exists():
            shutil.rmtree(a.out)
        settings = Settings(run_dir=a.out, frozen=a.frozen, use_llm=a.llm)
        result = train(a.steps, settings, use_llm=a.llm)
        print(json.dumps(result["status"], indent=2))
        return

    if a.command == "step":
        from .train import FlingeEngine

        eng = FlingeEngine(Settings(run_dir=a.out, use_llm=a.llm))
        print(json.dumps(eng.step(force_action=a.action, use_llm=a.llm), indent=2, default=str))
        return

    if a.command == "serve":
        from .serve import run_server

        use_llm = not a.no_llm
        run_server(Settings(run_dir=a.out, use_llm=use_llm, host=a.host, port=a.port))
        return

    if a.command == "validate":
        from .validate import run_validation

        print(json.dumps(run_validation(a.steps), indent=2))
        return


if __name__ == "__main__":
    main()
