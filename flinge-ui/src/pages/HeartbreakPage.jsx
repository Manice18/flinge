import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import BrainPanel from "../components/BrainPanel.jsx";
import FlySimulator from "../components/FlySimulator.jsx";
import {
  getHeartbreakSnapshot,
  postHeartbreakReset,
  postHeartbreakStep,
  postHeartbreakTrain,
} from "../lib/api.js";

const AUTO_MS = 2600;

export default function HeartbreakPage() {
  const [snap, setSnap] = useState(null);
  const [busy, setBusy] = useState(false);
  const [auto, setAuto] = useState(true);
  const [error, setError] = useState("");
  const [lastLine, setLastLine] = useState("");
  const [lastAction, setLastAction] = useState("scrolling");
  const [scrollPulse, setScrollPulse] = useState(0);
  const inFlight = useRef(false);

  const refresh = useCallback(async () => {
    try {
      const data = await getHeartbreakSnapshot();
      setSnap(data);
      setError("");
      if (data.line) setLastLine(data.line);
    } catch {
      setError("API offline — run `python -m flinge serve`");
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [refresh]);

  const runStep = useCallback(
    async (action = null) => {
      if (inFlight.current) return;
      inFlight.current = true;
      setScrollPulse((n) => n + 1);
      try {
        const result = await postHeartbreakStep(action);
        setLastAction(result.action || "rest");
        setLastLine(result.line || "");
        setScrollPulse((n) => n + 1);
        await refresh();
      } catch (e) {
        setError(String(e.message || e));
      } finally {
        inFlight.current = false;
      }
    },
    [refresh]
  );

  useEffect(() => {
    if (!auto) return undefined;
    let cancelled = false;
    const tick = async () => {
      if (cancelled || snap?.status?.completed) return;
      await runStep(null);
    };
    tick();
    const id = setInterval(tick, AUTO_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [auto, runStep, snap?.status?.completed]);

  async function train() {
    setAuto(false);
    setBusy(true);
    try {
      await postHeartbreakTrain(20);
      setLastAction("train");
      await refresh();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function reset() {
    setAuto(false);
    setBusy(true);
    try {
      await postHeartbreakReset();
      setLastLine("");
      setLastAction("scrolling");
      await refresh();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  const status = snap?.status || {};
  const stage = snap?.stage || {};
  const stages = snap?.stages || [];
  const ex = snap?.ex || { name: "Ex" };
  const progress = Math.min(100, Number(status.stage_progress) || 0);
  const alert = status.last_alert || "";
  const actionButtons = Array.isArray(snap?.actions) ? snap.actions : [];

  const profile = {
    id: ex.id || "ex",
    name: ex.name || "Ex",
    age_days: ex.age_days || 5,
    vibes: ex.vibes || [],
    prompt: stage.prompt || "Heartbreak",
    answer: stage.ex_line || lastLine || "…",
    danger: false,
  };

  return (
    <div className="app heartbreak-app">
      <header className="topbar">
        <h1 className="brand">
          Fl<span>inge</span>
        </h1>
        <nav className="route-nav">
          <Link to="/">Flinge</Link>
          <Link to="/heartbreak" className="active">
            Heartbreak
          </Link>
        </nav>
        <div className="stats">
          <span className="stat-pill">
            Dopamine <strong>{Math.round(status.dopamine ?? 35)}%</strong>
          </span>
          <span>
            Resilience <strong>{Math.round(status.resilience ?? 0)}</strong>
          </span>
          <span>
            Rumination <strong>{Math.round(status.rumination ?? 0)}</strong>
          </span>
          {auto && !status.completed ? (
            <span className="stat-pill auto-live">Auto · healing</span>
          ) : null}
          {status.completed ? <span className="stat-pill">Grown</span> : null}
        </div>
        {alert ? <div className="alert">{alert}</div> : null}
      </header>

      {error ? <p className="error">{error}</p> : null}

      <ol className="stage-rail">
        {stages.map((s, i) => {
          const active = i === (status.stage_index ?? 0);
          const done = i < (status.stage_index ?? 0) || status.completed;
          return (
            <li key={s.id} className={`${active ? "active" : ""} ${done ? "done" : ""}`}>
              <span className="stage-num">{s.order}</span>
              <span className="stage-name">{s.name}</span>
            </li>
          );
        })}
      </ol>

      <div className="layout layout-top">
        <FlySimulator
          profile={profile}
          alert={alert}
          lastReply={lastLine}
          lastAction={lastAction}
          dopamine={status.dopamine ?? 35}
          matched={false}
          messages={[
            { from: "her", text: stage.ex_line || "…" },
            { from: "fly", text: lastLine || "learning to let go…" },
          ]}
          auto={auto}
          scrollPulse={scrollPulse}
        />

        <section className="phone heartbreak-panel">
          <div className="phone-body">
            <div className="hb-stage-card">
              <p className="prompt-label">{stage.prompt || `Stage ${(status.stage_index ?? 0) + 1} of 7`}</p>
              <h2>{stage.name || "…"}</h2>
              <p className="prompt-answer">{stage.blurb}</p>
              <div className="hb-progress">
                <div className="track">
                  <div
                    className="fill hb-fill"
                    style={{ transform: `scaleX(${Math.max(0, Math.min(100, progress)) / 100})` }}
                  />
                </div>
                <span>{Math.round(status.stage_progress || 0)} / 100</span>
              </div>
              <p className="footer-line">
                Ex: <strong>{ex.name}</strong> · fly leans{" "}
                <strong>{snap?.observation?.action || lastAction}</strong>
              </p>
            </div>

            <div className="actions hb-actions">
              {actionButtons.map((a) => (
                <button
                  key={a}
                  type="button"
                  disabled={busy || status.completed}
                  onClick={() => {
                    setAuto(false);
                    runStep(a);
                  }}
                >
                  {a.replace("_", " ")}
                </button>
              ))}
            </div>

            <div className="toolbar">
              <button
                type="button"
                className={`accent ${auto ? "auto-on" : ""}`}
                onClick={() => setAuto((v) => !v)}
                disabled={status.completed}
              >
                {auto ? "Pause auto" : "Auto heal"}
              </button>
              <button type="button" disabled={busy || auto || status.completed} onClick={() => runStep(null)}>
                One step
              </button>
              <button type="button" disabled={busy} onClick={train}>
                Train ×20
              </button>
              <button type="button" disabled={busy} onClick={reset}>
                Reset grief
              </button>
            </div>

            {lastLine ? <p className="footer-line">Now: {lastLine}</p> : null}
            {status.completed ? (
              <p className="footer-line auto-hint">
                Growth complete — <Link to="/">return to Flinge</Link> when ready.
              </p>
            ) : null}
          </div>
        </section>
      </div>

      <BrainPanel
        regions={status.regions || snap?.observation?.regions || {}}
        alert={alert}
        dopamine={status.dopamine ?? 35}
        footer={lastLine}
        lastAction={status.completed ? "grow" : lastAction}
      />
    </div>
  );
}
