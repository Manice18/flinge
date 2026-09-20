import BrainCloud from "./BrainCloud.jsx";

const COLORS = {
  optic_lobes: "#5ec8ff",
  mushroom_bodies: "#c084fc",
  central_complex: "#f472b6",
  descending_neurons: "#fb923c",
  leg_neuropils: "#f87171",
  antennal_lobes: "#facc15",
  wing_motor: "#e8e8ec",
  halteres: "#4ade80",
};

const LABELS = {
  optic_lobes: "Optic lobes",
  mushroom_bodies: "Mushroom bodies",
  central_complex: "Central complex",
  descending_neurons: "Descending neurons",
  leg_neuropils: "Leg neuropils",
  antennal_lobes: "Antennal lobes",
  wing_motor: "Wing motor",
  halteres: "Halteres",
};

const BAR_ORDER = [
  "optic_lobes",
  "mushroom_bodies",
  "central_complex",
  "descending_neurons",
  "leg_neuropils",
  "antennal_lobes",
  "wing_motor",
  "halteres",
];

const ACTION_COPY = {
  pass: { title: "PASSING", sub: "avoidance pool wins · profile skipped" },
  like: { title: "LIKING", sub: "mushroom bodies stamp the card" },
  comment: { title: "COMMENTING", sub: "prompt circuit engages the profile" },
  rizz: { title: "RIZZING", sub: "PAM-like reward anticipation · opener fired" },
  decide: { title: "DECIDING", sub: "central complex arbitrates approach vs avoid" },
  train: { title: "TRAINING", sub: "KC→MBON efficacies updating" },
  match: { title: "MATCH", sub: "reward pulse · courtship wing primed" },
  danger: { title: "DANGER", sub: "escape circuit primed · PPL1 aversive" },
  scrolling: { title: "SCROLLING", sub: "descending neurons drive the tarsus swipe" },
  ruminate: { title: "RUMINATING", sub: "KC loops replay the last flight" },
  reach_out: { title: "REACHING OUT", sub: "descending neurons draft the unsent text" },
  blame: { title: "BLAMING", sub: "aversive PPL1 surge · anger outward" },
  bargain: { title: "BARGAINING", sub: "MB fantasy of one more chance" },
  rest: { title: "RESTING", sub: "quiet recovery · dopamine settling" },
  accept: { title: "ACCEPTING", sub: "reality named · approach/avoid rebalance" },
  grow: { title: "GROWING", sub: "new meadow · self-improvement PAM pulse" },
};

function resolveAction(lastAction, alert) {
  if (/danger/i.test(alert || "")) return "danger";
  if (/match/i.test(alert || "")) return "match";
  const a = (lastAction || "").toLowerCase();
  if (ACTION_COPY[a]) return a;
  return "scrolling";
}

export function modulateRegions(base = {}, actionKey = "scrolling") {
  const r = { ...base };
  const bump = (key, amount) => {
    r[key] = Math.min(100, Number(r[key] || 20) + amount);
  };
  switch (actionKey) {
    case "scrolling":
      bump("optic_lobes", 18);
      bump("descending_neurons", 28);
      bump("leg_neuropils", 35);
      break;
    case "like":
    case "comment":
      bump("mushroom_bodies", 30);
      bump("optic_lobes", 15);
      break;
    case "rizz":
    case "match":
      bump("mushroom_bodies", 30);
      bump("wing_motor", 25);
      bump("central_complex", 18);
      break;
    case "danger":
      bump("optic_lobes", 40);
      bump("descending_neurons", 45);
      bump("leg_neuropils", 40);
      bump("wing_motor", 30);
      break;
    case "train":
      bump("mushroom_bodies", 40);
      break;
    case "decide":
      bump("central_complex", 35);
      break;
    case "ruminate":
    case "bargain":
    case "reach_out":
      bump("mushroom_bodies", 35);
      bump("central_complex", 20);
      bump("antennal_lobes", 15);
      break;
    case "blame":
      bump("descending_neurons", 35);
      bump("optic_lobes", 20);
      bump("leg_neuropils", 15);
      break;
    case "rest":
      bump("halteres", 25);
      bump("antennal_lobes", 10);
      break;
    case "accept":
    case "grow":
      bump("mushroom_bodies", 28);
      bump("central_complex", 22);
      bump("wing_motor", 18);
      bump("halteres", 15);
      break;
    default:
      break;
  }
  return r;
}

export default function BrainPanel({
  regions = {},
  alert = "",
  dopamine = 0,
  footer = "",
  lastAction = "",
}) {
  const actionKey = resolveAction(lastAction, alert);
  const copy = ACTION_COPY[actionKey] || ACTION_COPY.scrolling;
  const live = modulateRegions(regions, actionKey);
  const intensity = Math.min(1, (dopamine || 50) / 100);

  return (
    <section className="brain-section paint-brain" aria-label="Paint the brain">
      <div className="brain-section-inner">
        <div className="brain-head paint-head">
          <div>
            <h3>Paint the brain</h3>
            <p className="paint-caption">Live soma cloud · actions light neurons</p>
          </div>
          <small>CNS · live</small>
        </div>

        <div className="paint-stage">
          <span className="paint-side left">L</span>
          <span className="paint-side right">R</span>
          <BrainCloud actionKey={actionKey} intensity={intensity} />
          <div className="cns-action paint-action" key={actionKey}>
            <div className="cns-action-title">{copy.title}</div>
            <div className="cns-action-sub">{copy.sub}</div>
          </div>
          <div className="paint-legend">
            <span>
              <i className="lg rest" /> Resting
            </span>
            <span>
              <i className="lg stim" /> Stimulated
            </span>
            <span>
              <i className="lg fire" /> Firing
            </span>
          </div>
        </div>

        <div className="bars bars-grid bars-grid-wide">
          {BAR_ORDER.map((key) => {
            const v = Math.round(Number(live[key] || 0));
            return (
              <div className="bar-row" key={key}>
                <span className="bar-dot" style={{ background: COLORS[key] }} />
                <span className="bar-label">{LABELS[key]}</span>
                <div className="track">
                  <div
                    className="fill"
                    style={{
                      transform: `scaleX(${Math.max(0, Math.min(100, v)) / 100})`,
                      background: COLORS[key],
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        <p className="footer-line brain-footer">
          Dopamine <em>{Math.round(dopamine)}%</em>
          {footer ? ` · ${footer.slice(0, 80)}` : ` · ${copy.title.toLowerCase()}`}
        </p>
      </div>
    </section>
  );
}
