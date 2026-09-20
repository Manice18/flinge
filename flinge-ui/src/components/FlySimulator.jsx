import { useEffect, useRef } from "react";
import * as THREE from "three";
import { animateDoomscroll, createFly } from "../lib/flyModel.js";
import { drawChatPhone, drawProfilePhone } from "../lib/phoneTextures.js";

/**
 * Fly faces the Flinge phones and scrolls with front tarsi.
 * Model local: head +X. rotY(+π/2) aims head at −Z (into the phone wall).
 */
export default function FlySimulator({
  profile,
  alert = "",
  lastReply = "",
  lastAction = "",
  dopamine = 50,
  matched = false,
  messages = [],
  auto = false,
  scrollPulse = 0,
}) {
  const mountRef = useRef(null);
  const stateRef = useRef({
    profile,
    alert,
    lastReply,
    lastAction,
    dopamine,
    matched,
    messages,
    auto,
    scrollPulse,
  });

  useEffect(() => {
    stateRef.current = {
      profile,
      alert,
      lastReply,
      lastAction,
      dopamine,
      matched,
      messages,
      auto,
      scrollPulse,
    };
  }, [profile, alert, lastReply, lastAction, dopamine, matched, messages, auto, scrollPulse]);

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;

    let disposed = false;
    let raf = 0;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#bdbdc2");
    scene.fog = new THREE.Fog("#bdbdc2", 6, 16);

    const camera = new THREE.PerspectiveCamera(38, 1, 0.05, 40);
    // Over right shoulder — see red eyes + tarsi on glass
    camera.position.set(1.35, 1.25, 2.35);
    camera.lookAt(0.05, 0.75, 0.35);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;
    el.appendChild(renderer.domElement);

    scene.add(new THREE.HemisphereLight(0xffffff, 0x9a9aa0, 1.25));
    const key = new THREE.DirectionalLight(0xfff4e6, 1.5);
    key.position.set(2, 5, 4);
    key.castShadow = true;
    scene.add(key);
    const fill = new THREE.DirectionalLight(0xd0d8e8, 0.5);
    fill.position.set(-3, 2, 2);
    scene.add(fill);

    const ground = new THREE.Mesh(
      new THREE.CircleGeometry(10, 48),
      new THREE.MeshStandardMaterial({ color: 0xa8a8ae, roughness: 0.95, metalness: 0 })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    const leftCanvas = document.createElement("canvas");
    leftCanvas.width = 400;
    leftCanvas.height = 720;
    const rightCanvas = document.createElement("canvas");
    rightCanvas.width = 400;
    rightCanvas.height = 720;
    const leftTex = new THREE.CanvasTexture(leftCanvas);
    const rightTex = new THREE.CanvasTexture(rightCanvas);
    leftTex.colorSpace = THREE.SRGBColorSpace;
    rightTex.colorSpace = THREE.SRGBColorSpace;

    function makePhone(tex) {
      const group = new THREE.Group();
      // Downsized vs earlier (~20% smaller)
      const body = new THREE.Mesh(
        new THREE.BoxGeometry(0.68, 1.35, 0.055),
        new THREE.MeshStandardMaterial({ color: 0x1a1a1c, roughness: 0.35, metalness: 0.4 })
      );
      body.castShadow = true;
      const screen = new THREE.Mesh(
        new THREE.PlaneGeometry(0.6, 1.22),
        new THREE.MeshBasicMaterial({ map: tex })
      );
      screen.position.z = 0.032;
      group.add(body, screen);
      return group;
    }

    // Phone wall just ahead of the fly — tilted like a propped tablet pair
    const phoneWall = new THREE.Group();
    phoneWall.position.set(0.12, 0.72, 0.15);
    phoneWall.rotation.x = -0.42;

    const leftPhone = makePhone(leftTex);
    leftPhone.position.set(-0.38, 0, 0.02);
    leftPhone.rotation.y = 0.1;
    phoneWall.add(leftPhone);

    const rightPhone = makePhone(rightTex);
    rightPhone.position.set(0.38, -0.01, -0.02);
    rightPhone.rotation.y = -0.08;
    phoneWall.add(rightPhone);
    scene.add(phoneWall);

    let fly = null;
    const mood = { court: 0.15, recoil: 0, scroll: 1, burst: 0, lastPulse: 0 };

    // Head +X → rotY(+π/2) faces −Z into the phones; slight −yaw aims at wall center.
    // Raised + pitched so front tarsi land on the glass.
    const FLY = {
      x: 0.02,
      y: 0.28,
      z: 1.05,
      scale: 0.125,
      yaw: Math.PI / 2 - 0.18,
      pitch: 0.55,
      roll: 0.06,
    };

    function resize() {
      const w = el.clientWidth || 800;
      const h = el.clientHeight || 420;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(el);

    function paintPhones() {
      const s = stateRef.current;
      const badge = s.lastAction
        ? s.auto
          ? `auto → ${s.lastAction}`
          : `tarsi → ${s.lastAction}`
        : s.auto
          ? "auto scrolling…"
          : "scrolling…";
      drawProfilePhone(leftCanvas, s.profile, { badge });
      drawChatPhone(rightCanvas, s.profile, s.messages, s.alert || s.lastReply);
      leftTex.needsUpdate = true;
      rightTex.needsUpdate = true;
    }
    paintPhones();

    (async () => {
      try {
        fly = await createFly("/fly");
        if (disposed) return;
        fly.scale.setScalar(FLY.scale);
        fly.rotation.order = "YXZ";
        fly.position.set(FLY.x, FLY.y, FLY.z);
        fly.rotation.set(FLY.pitch, FLY.yaw, FLY.roll);
        scene.add(fly);
      } catch (err) {
        console.warn("Fly mesh load failed", err);
        const proxy = new THREE.Group();
        const body = new THREE.Mesh(
          new THREE.CapsuleGeometry(0.14, 0.28, 6, 12),
          new THREE.MeshStandardMaterial({ color: 0x8a7358 })
        );
        body.rotation.z = Math.PI / 2;
        const eyeL = new THREE.Mesh(
          new THREE.SphereGeometry(0.1, 16, 12),
          new THREE.MeshStandardMaterial({ color: 0xc43c2e, emissive: 0x401010 })
        );
        eyeL.position.set(0.22, 0.06, 0.1);
        const eyeR = eyeL.clone();
        eyeR.position.z = -0.1;
        proxy.add(body, eyeL, eyeR);
        proxy.position.set(FLY.x, FLY.y + 0.12, FLY.z);
        proxy.rotation.order = "YXZ";
        proxy.rotation.set(FLY.pitch * 0.5, FLY.yaw, 0);
        scene.add(proxy);
        fly = proxy;
      }
    })();

    const clock = new THREE.Clock();
    let lastPaint = 0;

    function tick() {
      if (disposed) return;
      raf = requestAnimationFrame(tick);
      const t = clock.getElapsedTime();
      const s = stateRef.current;
      const danger = Boolean(s.profile?.danger) || /danger/i.test(s.alert || "");
      const happy = s.matched || /match|engaged|warm/i.test(s.alert || "");

      mood.court += ((happy ? 0.55 : 0.14) - mood.court) * 0.04;
      mood.recoil += ((danger ? 1 : 0) - mood.recoil) * 0.08;

      // Auto mode keeps continuous tarsus motion; each decision pulses harder
      if (s.scrollPulse !== mood.lastPulse) {
        mood.lastPulse = s.scrollPulse;
        mood.burst = 1;
      }
      mood.burst *= 0.92;
      const autoBoost = s.auto ? 1.15 : 0.75;
      const targetScroll = danger ? 0.2 : autoBoost + mood.burst * 0.85;
      mood.scroll += (targetScroll - mood.scroll) * 0.08;

      if (fly?.userData?.fly) {
        const swipeRate = s.auto ? 1.35 : 1;
        animateDoomscroll(fly, t * swipeRate, {
          scroll: mood.scroll,
          court: mood.court,
          recoil: mood.recoil,
        });
        // Stay locked onto the phones; micro bob while scrolling
        fly.position.x = FLY.x + Math.sin(t * 1.4) * 0.008;
        fly.position.y = FLY.y + Math.sin(t * 2.2) * 0.006 + mood.burst * 0.01;
        fly.position.z = FLY.z + mood.recoil * 0.08;
        fly.rotation.x = FLY.pitch - mood.recoil * 0.12 + Math.sin(t * 1.0) * 0.02;
        fly.rotation.y = FLY.yaw + Math.sin(t * 0.5) * 0.03;
        fly.rotation.z = FLY.roll + Math.sin(t * 1.3) * 0.015;
      } else if (fly) {
        fly.position.y = FLY.y + 0.12 + Math.sin(t * 2) * 0.015;
      }

      // Feed scrolls under the tarsi on each decision
      const drift = 0.014 * mood.scroll + mood.burst * 0.02;
      leftPhone.position.y = Math.sin(t * (s.auto ? 2.2 : 1.5)) * drift;
      rightPhone.position.y = -0.01 + Math.sin(t * (s.auto ? 2.2 : 1.5) + 1) * drift * 0.7;

      camera.position.x = 1.35 + Math.sin(t * 0.1) * 0.035;
      camera.position.y = 1.25 + Math.sin(t * 0.12) * 0.02;
      camera.lookAt(0.05, 0.72, 0.4);

      if (t - lastPaint > 0.35) {
        paintPhones();
        lastPaint = t;
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

  return (
    <section className="simulator">
      <div className="simulator-label dark">
        <span>Fly simulator</span>
        <small>
          {auto ? "auto deciding · tarsi scrolling" : "facing Flinge · tarsi scrolling"}
        </small>
      </div>
      <div className="simulator-stage" ref={mountRef} />
      {alert ? (
        <div className={`simulator-toast ${/danger/i.test(alert) ? "danger" : ""}`}>{alert}</div>
      ) : null}
    </section>
  );
}
