import * as THREE from "three";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

// Anatomical assets: NeuroMechFly / NeLy-EPFL, Apache-2.0 (see public/fly/NOTICE).
// Animation is illustrative kinematics, not biomechanical output.
const cache = new Map();
const rad = Math.PI / 180;
const turn = new THREE.Quaternion();

async function loadAssets(base) {
  if (!cache.has(base)) {
    cache.set(
      base,
      (async () => {
        const response = await fetch(`${base}/model.json`);
        if (!response.ok) throw new Error(`Fly model: HTTP ${response.status}`);
        const model = await response.json();
        const loader = new STLLoader();
        const files = [...new Set(Object.values(model.meshes).map((x) => x.file))];
        const geometries = Object.fromEntries(
          await Promise.all(
            files.map(async (file) => {
              const geometry = await loader.loadAsync(`${base}/meshes/${file}`);
              geometry.scale(model.meshScale, model.meshScale, model.meshScale);
              geometry.computeVertexNormals();
              return [file, geometry];
            })
          )
        );
        return { model, geometries };
      })()
    );
  }
  return cache.get(base);
}

function pose(state, changes = {}) {
  for (const [name, node] of Object.entries(state.nodes)) {
    node.quaternion.copy(state.rest[name]);
    for (const dof of state.dofs[name] || []) {
      const degrees = (state.model.neutralDeg[dof.name] || 0) + (changes[dof.name] || 0);
      node.quaternion.multiply(turn.setFromAxisAngle(dof.vector, degrees * rad));
    }
  }
}

export async function createFly(assetBase) {
  const { model, geometries } = await loadAssets(assetBase.replace(/\/$/, ""));
  const group = new THREE.Group();
  group.name = "NeuroMechFly";
  const body = new THREE.Group();
  const state = { model, nodes: {}, rest: {}, dofs: {}, body };
  for (const name of model.segments) {
    const node = new THREE.Group();
    node.name = name;
    const conf = model.rest[name];
    node.position.fromArray(conf.pos);
    const [w, x, y, z] = conf.quat;
    state.rest[name] = new THREE.Quaternion(x, y, z, w).normalize();
    const wing = name.endsWith("_wing");
    const eye = name.includes("eye");
    const material = new THREE.MeshStandardMaterial({
      color: wing
        ? new THREE.Color("#c5d4c8")
        : eye
          ? new THREE.Color("#c43c2e")
          : name.includes("abdomen6")
            ? new THREE.Color("#3a3228")
            : new THREE.Color("#8a7358"),
      roughness: wing ? 0.35 : 0.55,
      metalness: wing ? 0.08 : 0,
      transparent: wing,
      opacity: wing ? 0.4 : 1,
      depthWrite: !wing,
      side: wing ? THREE.DoubleSide : THREE.FrontSide,
    });
    const spec = model.meshes[name];
    const mesh = new THREE.Mesh(geometries[spec.file], material);
    mesh.name = `${name}_mesh`;
    if (spec.mirror) mesh.scale.y = -1;
    mesh.castShadow = !wing;
    mesh.receiveShadow = !wing;
    node.add(mesh);
    state.nodes[name] = node;
  }
  for (const d of model.dofs) {
    (state.dofs[d.child] ||= []).push({
      ...d,
      vector: new THREE.Vector3().fromArray(
        Array.isArray(d.axis) ? d.axis : model.axisVector[d.axis]
      ),
    });
  }
  body.add(state.nodes[model.root]);
  for (const [parent, child] of model.joints) state.nodes[parent].add(state.nodes[child]);
  pose(state);
  body.updateMatrixWorld(true);
  body.rotation.x = -Math.PI / 2;
  group.add(body);
  group.updateMatrixWorld(true);
  body.position.y = -new THREE.Box3().setFromObject(body).min.y;
  group.userData.fly = state;
  return group;
}

export function animateFly(group, time, flight = 0, wingExtension = 0) {
  const state = group.userData.fly;
  if (!state) return;
  const airborne = THREE.MathUtils.clamp(Number(flight), 0, 1);
  const court = THREE.MathUtils.clamp(wingExtension, 0, 1);
  const changes = {};
  for (const side of ["l", "r"]) {
    const sign = side === "l" ? 1 : -1;
    const ext = side === "l" ? court : court * 0.35;
    changes[`c_thorax-${side}_wing-roll`] = sign * (airborne * 70 + ext * 65);
    changes[`c_thorax-${side}_wing-yaw`] =
      sign * (airborne * 24 * Math.sin(time * 85) + ext * 8 * Math.sin(time * 65));
    for (const leg of ["f", "m", "h"]) {
      changes[`${side}${leg}_coxa-${side}${leg}_trochanterfemur-pitch`] = airborne * -20;
      changes[`${side}${leg}_trochanterfemur-${side}${leg}_tibia-pitch`] = airborne * 25;
    }
  }
  pose(state, changes);
}

/**
 * Perched on phones: head pitched down, front tarsi holding glass + swipe.
 * Amplitudes tuned so legs reach the screen without spearing through it.
 */
export function animateDoomscroll(group, time, opts = {}) {
  const state = group.userData.fly;
  if (!state) return;
  const scroll = opts.scroll ?? 1;
  const court = THREE.MathUtils.clamp(opts.court ?? 0.2, 0, 1);
  const recoil = THREE.MathUtils.clamp(opts.recoil ?? 0, 0, 1);
  // Alternating swipe cycles on left / right front tarsi
  const swipeL = Math.sin(time * 3.6) * scroll;
  const swipeR = Math.sin(time * 3.6 + 2.1) * scroll;
  const hold = 1 - recoil * 0.5;

  const changes = {
    "c_thorax-c_head-pitch": 32 * hold + recoil * -10 + Math.sin(time * 1.1) * 2,
    "c_thorax-c_head-yaw": Math.sin(time * 0.5) * 4,
    "c_thorax-c_head-roll": Math.sin(time * 0.65) * 2,
    // Front legs reach forward onto the glass and scroll
    "c_thorax-lf_coxa-pitch": (-48 + swipeL * 14) * hold,
    "c_thorax-lf_coxa-yaw": -12 + swipeL * 8,
    "c_thorax-lf_coxa-roll": 12,
    "lf_coxa-lf_trochanterfemur-pitch": 28 + swipeL * 16,
    "lf_trochanterfemur-lf_tibia-pitch": -55 + swipeL * -12,
    "lf_tibia-lf_tarsus1-pitch": 25 + swipeL * 20,
    "lf_tarsus1-lf_tarsus2-pitch": 8 + swipeL * 10,
    "c_thorax-rf_coxa-pitch": (-46 + swipeR * 14) * hold,
    "c_thorax-rf_coxa-yaw": 12 + swipeR * 8,
    "c_thorax-rf_coxa-roll": -12,
    "rf_coxa-rf_trochanterfemur-pitch": 26 + swipeR * 16,
    "rf_trochanterfemur-rf_tibia-pitch": -52 + swipeR * -12,
    "rf_tibia-rf_tarsus1-pitch": 22 + swipeR * 20,
    "rf_tarsus1-rf_tarsus2-pitch": 8 + swipeR * 10,
    // Mid legs brace the bezel
    "c_thorax-lm_coxa-pitch": -18,
    "c_thorax-rm_coxa-pitch": -16,
    "lm_coxa-lm_trochanterfemur-pitch": 20,
    "rm_coxa-rm_trochanterfemur-pitch": 18,
    "lm_trochanterfemur-lm_tibia-pitch": -25,
    "rm_trochanterfemur-rm_tibia-pitch": -22,
    // Hind legs plant
    "c_thorax-lh_coxa-pitch": 8,
    "c_thorax-rh_coxa-pitch": 6,
  };

  for (const side of ["l", "r"]) {
    const sign = side === "l" ? 1 : -1;
    changes[`c_thorax-${side}_wing-roll`] = sign * (6 + court * 42);
    changes[`c_thorax-${side}_wing-yaw`] = sign * (court * 7 * Math.sin(time * 30));
  }

  pose(state, changes);
}
