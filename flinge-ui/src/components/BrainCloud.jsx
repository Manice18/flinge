import { useEffect, useRef } from "react";
import * as THREE from "three";

const REST = new THREE.Color("#7a8694");
const STIM = new THREE.Color("#4aa3ff");
const FIRE = new THREE.Color("#f0c33a");

const ACTION_FOCUS = {
  scrolling: { stim: 0.12, fire: 0.04, biasZ: 0.15 },
  like: { stim: 0.18, fire: 0.08, biasY: 0.2 },
  comment: { stim: 0.2, fire: 0.1, biasY: 0.15 },
  rizz: { stim: 0.22, fire: 0.14, biasY: 0.25 },
  match: { stim: 0.28, fire: 0.2, biasY: 0.3 },
  danger: { stim: 0.35, fire: 0.22, biasY: -0.1 },
  pass: { stim: 0.1, fire: 0.03, biasY: 0.05 },
  decide: { stim: 0.16, fire: 0.07, biasY: 0.2 },
  train: { stim: 0.25, fire: 0.12, biasY: 0.18 },
};

async function loadPositions(maxPoints = 28000) {
  try {
    const res = await fetch("/brain/positions.f32");
    if (!res.ok) throw new Error("positions.f32 missing");
    const buf = await res.arrayBuffer();
    const raw = new Float32Array(buf);
    const valid = [];
    for (let i = 0; i + 2 < raw.length; i += 3) {
      const x = raw[i];
      const y = raw[i + 1];
      const z = raw[i + 2];
      if (Number.isFinite(x) && Number.isFinite(y) && Number.isFinite(z)) {
        // Match fruitless connectome orientation: x, -z, y
        valid.push(x, -z, y);
      }
    }
    const stride = Math.max(1, Math.floor(valid.length / 3 / maxPoints));
    const out = [];
    for (let i = 0; i + 2 < valid.length; i += 3 * stride) {
      out.push(valid[i], valid[i + 1], valid[i + 2]);
    }
    return new Float32Array(out);
  } catch {
    const res = await fetch("/brain/context.json");
    const data = await res.json();
    const pts = data.points || [];
    const out = new Float32Array(pts.length * 3);
    for (let i = 0; i < pts.length; i++) {
      out[i * 3] = pts[i][0];
      out[i * 3 + 1] = -pts[i][2];
      out[i * 3 + 2] = pts[i][1];
    }
    return out;
  }
}

function normalize(positions) {
  let minX = Infinity,
    minY = Infinity,
    minZ = Infinity;
  let maxX = -Infinity,
    maxY = -Infinity,
    maxZ = -Infinity;
  for (let i = 0; i < positions.length; i += 3) {
    minX = Math.min(minX, positions[i]);
    maxX = Math.max(maxX, positions[i]);
    minY = Math.min(minY, positions[i + 1]);
    maxY = Math.max(maxY, positions[i + 1]);
    minZ = Math.min(minZ, positions[i + 2]);
    maxZ = Math.max(maxZ, positions[i + 2]);
  }
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  const cz = (minZ + maxZ) / 2;
  const scale = 2.6 / Math.max(maxX - minX, maxY - minY, maxZ - minZ, 1);
  for (let i = 0; i < positions.length; i += 3) {
    positions[i] = (positions[i] - cx) * scale;
    positions[i + 1] = (positions[i + 1] - cy) * scale;
    positions[i + 2] = (positions[i + 2] - cz) * scale;
  }
}

/**
 * Anatomical MaleCNS soma cloud — resting / stimulated / firing.
 * Activity is illustrative, driven by Flinge actions.
 */
export default function BrainCloud({ actionKey = "scrolling", intensity = 0.5 }) {
  const mountRef = useRef(null);
  const actionRef = useRef({ actionKey, intensity });

  useEffect(() => {
    actionRef.current = { actionKey, intensity };
  }, [actionKey, intensity]);

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;

    let disposed = false;
    let raf = 0;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#0b1016");

    const camera = new THREE.PerspectiveCamera(38, 1, 0.05, 40);
    camera.position.set(0, 0.15, 4.2);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    el.appendChild(renderer.domElement);

    const root = new THREE.Group();
    scene.add(root);

    let points = null;
    let colors = null;
    let positions = null;
    let n = 0;
    let state = null; // 0 rest, 1 stim, 2 fire
    let ages = null;
    let burstUntil = 0;

    function paintBase() {
      if (!colors) return;
      for (let i = 0; i < n; i++) {
        const c = state[i] === 2 ? FIRE : state[i] === 1 ? STIM : REST;
        const dim = state[i] === 0 ? 0.55 : 1;
        colors[i * 3] = c.r * dim;
        colors[i * 3 + 1] = c.g * dim;
        colors[i * 3 + 2] = c.b * dim;
      }
      points.geometry.attributes.color.needsUpdate = true;
    }

    function stimulate(force = false) {
      if (!state) return;
      const now = performance.now() / 1000;
      if (!force && now < burstUntil) return;
      const focus = ACTION_FOCUS[actionRef.current.actionKey] || ACTION_FOCUS.scrolling;
      const amp = 0.55 + actionRef.current.intensity * 0.7;
      const stimN = Math.floor(n * focus.stim * amp);
      const fireN = Math.floor(n * focus.fire * amp);
      // Soft decay previous
      for (let i = 0; i < n; i++) {
        if (state[i] > 0 && Math.random() < 0.35) state[i] = Math.max(0, state[i] - 1);
      }
      for (let k = 0; k < stimN; k++) {
        const i = Math.floor(Math.random() * n);
        const y = positions[i * 3 + 1];
        const z = positions[i * 3 + 2];
        const biasY = focus.biasY || 0;
        const biasZ = focus.biasZ || 0;
        if (biasY && Math.sign(y) !== Math.sign(biasY) && Math.random() < 0.55) continue;
        if (biasZ && Math.sign(z) !== Math.sign(biasZ) && Math.random() < 0.4) continue;
        state[i] = Math.max(state[i], 1);
        ages[i] = 0.6 + Math.random() * 0.8;
      }
      for (let k = 0; k < fireN; k++) {
        const i = Math.floor(Math.random() * n);
        state[i] = 2;
        ages[i] = 0.35 + Math.random() * 0.55;
      }
      burstUntil = now + 0.35;
      paintBase();
    }

    (async () => {
      try {
        positions = await loadPositions(30000);
        if (disposed) return;
        normalize(positions);
        n = positions.length / 3;
        state = new Uint8Array(n);
        ages = new Float32Array(n);

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        colors = new Float32Array(n * 3);
        for (let i = 0; i < n; i++) {
          colors[i * 3] = REST.r * 0.55;
          colors[i * 3 + 1] = REST.g * 0.55;
          colors[i * 3 + 2] = REST.b * 0.55;
        }
        geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

        points = new THREE.Points(
          geometry,
          new THREE.PointsMaterial({
            size: 0.018,
            vertexColors: true,
            transparent: true,
            opacity: 0.95,
            depthWrite: false,
            sizeAttenuation: true,
          })
        );
        root.add(points);
        root.rotation.x = -0.35;
        stimulate(true);
      } catch (err) {
        console.warn("Brain cloud failed", err);
      }
    })();

    function resize() {
      const w = el.clientWidth || 900;
      const h = el.clientHeight || 380;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(el);

    let lastAction = "";
    const clock = new THREE.Clock();

    function tick() {
      if (disposed) return;
      raf = requestAnimationFrame(tick);
      const dt = Math.min(0.05, clock.getDelta());
      const t = clock.elapsedTime;

      root.rotation.y = t * 0.12;
      camera.position.x = Math.sin(t * 0.15) * 0.35;
      camera.lookAt(0, 0.05, 0);

      const ak = actionRef.current.actionKey;
      if (ak !== lastAction) {
        lastAction = ak;
        stimulate(true);
      } else if (Math.random() < 0.04) {
        stimulate(false);
      }

      if (ages && state) {
        let dirty = false;
        for (let i = 0; i < n; i++) {
          if (ages[i] <= 0) continue;
          ages[i] -= dt;
          if (ages[i] <= 0 && state[i] > 0) {
            state[i] -= 1;
            ages[i] = state[i] > 0 ? 0.4 : 0;
            dirty = true;
          }
        }
        if (dirty) paintBase();
      }

      renderer.render(scene, camera);
    }
    tick();

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      ro.disconnect();
      renderer.dispose();
      if (renderer.domElement.parentNode === el) el.removeChild(renderer.domElement);
    };
  }, []);

  return <div className="brain-cloud" ref={mountRef} />;
}
