const BASE = import.meta.env.VITE_API_BASE || "";

async function jsonFetch(path, opts) {
  const r = await fetch(`${BASE}${path}`, opts);
  if (!r.ok) throw new Error(`${path} failed`);
  return r.json();
}

export async function getSnapshot() {
  return jsonFetch("/api/snapshot");
}

export async function postStep(action = null, use_llm = true) {
  return jsonFetch("/api/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, use_llm }),
  });
}

export async function postTrain(n = 10) {
  return jsonFetch(`/api/train?n=${n}&use_llm=false`, { method: "POST" });
}

export async function postReset() {
  return jsonFetch("/api/reset", { method: "POST" });
}

export async function getHeartbreakSnapshot() {
  return jsonFetch("/api/heartbreak/snapshot");
}

export async function postHeartbreakStep(action = null) {
  return jsonFetch("/api/heartbreak/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
}

export async function postHeartbreakTrain(n = 12) {
  return jsonFetch(`/api/heartbreak/train?n=${n}`, { method: "POST" });
}

export async function postHeartbreakReset() {
  return jsonFetch("/api/heartbreak/reset", { method: "POST" });
}

export function formatScreen(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}
