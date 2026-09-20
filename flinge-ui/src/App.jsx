import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import BrainPanel from "./components/BrainPanel.jsx";
import FlySimulator from "./components/FlySimulator.jsx";
import ProfileCard from "./components/ProfileCard.jsx";
import {
  formatScreen,
  getSnapshot,
  postReset,
  postStep,
  postTrain,
} from "./lib/api.js";

const AUTO_MS = 2800;

function applyStepResult(result, setters) {
  const { setLastReply, setLastAction, setLastMatched, setTab } = setters;
  setLastReply(result.reply || result.alert || "");
  setLastMatched(Boolean(result.matched));
  if (/danger/i.test(result.alert || "") || result.outcome === "danger") {
    setLastAction("danger");
  } else if (result.matched) {
    setLastAction(result.action === "rizz" ? "rizz" : "match");
  } else {
    setLastAction(result.action || "decide");
  }
  if (result.matched) setTab("matches");
}

export default function App() {
  const [snap, setSnap] = useState(null);
  const [tab, setTab] = useState("discover");
  const [busy, setBusy] = useState(false);
  const [auto, setAuto] = useState(true);
  const [error, setError] = useState("");
  const [lastReply, setLastReply] = useState("");
  const [lastAction, setLastAction] = useState("scrolling");
  const [lastMatched, setLastMatched] = useState(false);
  const [activeThread, setActiveThread] = useState(0);
  const [scrollPulse, setScrollPulse] = useState(0);
  const threadRef = useRef(null);

  const inFlight = useRef(false);
  const resultSetters = { setLastReply, setLastAction, setLastMatched, setTab };

  const refresh = useCallback(async () => {
    try {
      const data = await getSnapshot();
      setSnap(data);
      setError("");
    } catch {
      setError("API offline — run `python -m flinge serve` in flinge/");
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [refresh]);

  const runFlyStep = useCallback(
    async ({ action = null, useLlm = false, fromAuto = false } = {}) => {
      if (inFlight.current) return null;
      inFlight.current = true;
      if (!fromAuto) setBusy(true);
      setError("");
      // Kick tarsus animation immediately while the request runs
      setScrollPulse((n) => n + 1);
      setLastAction((prev) => (action ? action : prev === "scrolling" ? "decide" : "scrolling"));
      try {
        const result = await postStep(action, useLlm);
        applyStepResult(result, resultSetters);
        setScrollPulse((n) => n + 1);
        await refresh();
        return result;
      } catch (e) {
        setError(String(e.message || e));
        return null;
      } finally {
        inFlight.current = false;
        if (!fromAuto) setBusy(false);
      }
    },
    [refresh]
  );

  // Autonomous loop — fly decoder picks pass/like/comment/rizz
  useEffect(() => {
    if (!auto) return undefined;
    let cancelled = false;
    const tick = async () => {
      if (cancelled) return;
      await runFlyStep({ action: null, useLlm: false, fromAuto: true });
    };
    tick();
    const id = setInterval(tick, AUTO_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [auto, runFlyStep]);

  async function act(action) {
    setAuto(false);
    await runFlyStep({ action, useLlm: true, fromAuto: false });
  }

  async function letFlyDecide() {
    await runFlyStep({ action: null, useLlm: true, fromAuto: false });
  }

  async function train() {
    setAuto(false);
    setBusy(true);
    try {
      await postTrain(12);
      setLastAction("train");
      setScrollPulse((n) => n + 1);
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
      await postReset();
      setLastReply("");
      setLastAction("scrolling");
      setLastMatched(false);
      await refresh();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  const status = snap?.status || {};
  const current = snap?.current;
  const obs = snap?.observation;
  const threads = snap?.threads || [];
  const alert = status.last_alert || "";
  const alertDanger = /danger/i.test(alert);
  const activeThreadData = threads[activeThread] || threads[0];
  const activeMsgs = activeThreadData?.messages || [];

  useEffect(() => {
    if (tab !== "chat" || !threadRef.current) return;
    threadRef.current.scrollTop = threadRef.current.scrollHeight;
  }, [tab, activeThread, activeMsgs.length, activeMsgs[activeMsgs.length - 1]?.text]);

  return (
    <div className="app">
      <header className="topbar">
        <h1 className="brand">
          Fl<span>inge</span>
        </h1>
        <nav className="route-nav">
          <Link to="/" className="active">
            Flinge
          </Link>
          <Link to="/heartbreak">Heartbreak</Link>
        </nav>
        <div className="stats">
          <span className="stat-pill">
            Dopamine <strong>{Math.round(status.dopamine ?? 50)}%</strong>
          </span>
          <span>
            Posts <strong>{status.posts ?? 0}</strong>
          </span>
          <span>
            Matches <strong>{status.matches ?? 0}</strong>
          </span>
          <span>
            Screen <strong>{formatScreen(status.screen_seconds ?? 0)}</strong>
          </span>
          {auto ? (
            <span className="stat-pill auto-live">Auto · deciding</span>
          ) : null}
        </div>
        {alert ? (
          <div className={`alert ${alertDanger ? "danger" : ""}`}>{alert}</div>
        ) : null}
      </header>

      {error ? <p className="error">{error}</p> : null}

      <div className="layout layout-top">
        <FlySimulator
          profile={current}
          alert={alert}
          lastReply={lastReply}
          lastAction={lastAction}
          dopamine={status.dopamine ?? 50}
          matched={lastMatched}
          messages={activeMsgs}
          auto={auto}
          scrollPulse={scrollPulse}
        />

        <section className="phone">
          <div className="tabs">
            {["discover", "matches", "chat"].map((t) => (
              <button
                key={t}
                className={tab === t ? "active" : ""}
                onClick={() => setTab(t)}
                type="button"
              >
                {t}
              </button>
            ))}
          </div>

          {tab === "discover" ? (
            <div className="phone-body">
              <ProfileCard profile={current} proposed={obs} />
              <div className="actions">
                <button type="button" className="ghost" disabled={busy} onClick={() => act("pass")}>
                  Pass
                </button>
                <button type="button" disabled={busy} onClick={() => act("like")}>
                  Like
                </button>
                <button type="button" disabled={busy} onClick={() => act("comment")}>
                  Comment
                </button>
                <button
                  type="button"
                  className="primary"
                  disabled={busy}
                  onClick={() => act("rizz")}
                >
                  Rizz
                </button>
              </div>
              <div className="toolbar">
                <button
                  type="button"
                  className={`accent ${auto ? "auto-on" : ""}`}
                  disabled={busy && !auto}
                  onClick={() => setAuto((v) => !v)}
                >
                  {auto ? "Pause auto" : "Auto decide"}
                </button>
                <button type="button" disabled={busy || auto} onClick={letFlyDecide}>
                  One step
                </button>
                <button type="button" disabled={busy} onClick={train}>
                  Train ×12
                </button>
                <button type="button" disabled={busy} onClick={reset}>
                  Reset brain
                </button>
              </div>
              {lastReply ? <p className="footer-line">Last reply: {lastReply}</p> : null}
              {auto ? (
                <p className="footer-line auto-hint">
                  Fly is choosing on its own every few seconds — watch the tarsi.
                </p>
              ) : null}
            </div>
          ) : null}

          {tab === "matches" ? (
            <div className="match-list">
              {threads.length === 0 ? (
                <p className="footer-line">No matches yet — rizz harder.</p>
              ) : (
                threads.map((t, i) => (
                  <button
                    key={t.profile_id}
                    type="button"
                    onClick={() => {
                      setActiveThread(i);
                      setTab("chat");
                    }}
                  >
                    {t.name} · {t.messages?.length || 0} msgs
                  </button>
                ))
              )}
            </div>
          ) : null}

          {tab === "chat" ? (
            <div className="thread" ref={threadRef}>
              {activeThreadData ? (
                <>
                  <div className="thread-head">
                    <strong>{activeThreadData.name}</strong>
                    <span>{activeMsgs.length} msgs</span>
                  </div>
                  {activeMsgs.map((m, i) => (
                    <div key={`${activeThreadData.profile_id}-${i}`} className={`bubble ${m.from === "fly" ? "fly" : "her"}`}>
                      {m.text}
                    </div>
                  ))}
                </>
              ) : (
                <p className="footer-line thread-empty">Pick a match to read the thread.</p>
              )}
            </div>
          ) : null}
        </section>
      </div>

      <BrainPanel
        regions={status.regions || obs?.regions || {}}
        alert={alert}
        dopamine={status.dopamine ?? 50}
        footer={lastReply}
        lastAction={lastAction}
      />
    </div>
  );
}
