/** Draw Flinge phone UI onto a canvas for Three.js textures. */

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

export function drawProfilePhone(canvas, profile, opts = {}) {
  const w = canvas.width;
  const h = canvas.height;
  const ctx = canvas.getContext("2d");
  const danger = Boolean(profile?.danger);
  const bg = danger ? "#2a1214" : "#1c1814";
  const accent = danger ? "#e85d4c" : "#e8b86a";
  const ink = "#f6efe4";

  ctx.fillStyle = "#0a0908";
  ctx.fillRect(0, 0, w, h);

  // bezel
  roundRect(ctx, 8, 8, w - 16, h - 16, 28);
  ctx.fillStyle = bg;
  ctx.fill();

  // status bar
  ctx.fillStyle = accent;
  ctx.font = "600 18px DM Sans, sans-serif";
  ctx.fillText("Flinge", 36, 48);
  ctx.fillStyle = ink;
  ctx.font = "14px DM Sans, sans-serif";
  ctx.fillText("Discover", 36, 72);

  // avatar
  const cx = w / 2;
  const cy = 170;
  ctx.beginPath();
  ctx.arc(cx, cy, 54, 0, Math.PI * 2);
  ctx.fillStyle = accent;
  ctx.fill();
  ctx.fillStyle = bg;
  ctx.font = "700 42px Fraunces, serif";
  ctx.textAlign = "center";
  ctx.fillText((profile?.name || "?")[0], cx, cy + 14);
  ctx.textAlign = "left";

  const name = profile?.name || "Loading…";
  const age = profile?.age_days != null ? `, ${profile.age_days}d` : "";
  ctx.fillStyle = ink;
  ctx.font = "700 28px Fraunces, serif";
  ctx.textAlign = "center";
  ctx.fillText(`${name}${age}`, cx, 260);

  ctx.fillStyle = "#c4b4a0";
  ctx.font = "16px DM Sans, sans-serif";
  const vibes = (profile?.vibes || []).slice(0, 3).join(" · ");
  ctx.fillText(vibes.slice(0, 36), cx, 290);

  ctx.fillStyle = accent;
  ctx.font = "600 13px DM Sans, sans-serif";
  ctx.fillText((profile?.prompt || "").toUpperCase().slice(0, 28), cx, 340);

  ctx.fillStyle = ink;
  ctx.font = "18px DM Sans, sans-serif";
  wrapText(ctx, profile?.answer || "", cx, 372, w - 80, 24);

  if (danger) {
    ctx.fillStyle = accent;
    roundRect(ctx, w / 2 - 70, 430, 140, 36, 10);
    ctx.fill();
    ctx.fillStyle = "#1a0908";
    ctx.font = "700 16px DM Sans, sans-serif";
    ctx.fillText("DANGER", cx, 454);
  }

  if (opts.badge) {
    ctx.fillStyle = "rgba(232,184,106,0.9)";
    roundRect(ctx, 24, h - 70, w - 48, 40, 12);
    ctx.fill();
    ctx.fillStyle = "#1a1410";
    ctx.font = "600 15px DM Sans, sans-serif";
    ctx.fillText(opts.badge.slice(0, 34), cx, h - 44);
  }

  ctx.textAlign = "left";
}

export function drawChatPhone(canvas, profile, messages = [], alert = "") {
  const w = canvas.width;
  const h = canvas.height;
  const ctx = canvas.getContext("2d");
  const danger = Boolean(profile?.danger) || /danger/i.test(alert);

  ctx.fillStyle = "#0a0908";
  ctx.fillRect(0, 0, w, h);
  roundRect(ctx, 8, 8, w - 16, h - 16, 28);
  ctx.fillStyle = danger ? "#241014" : "#141210";
  ctx.fill();

  ctx.fillStyle = danger ? "#e85d4c" : "#e8b86a";
  ctx.font = "700 20px Fraunces, serif";
  ctx.fillText(profile?.name || "Match", 36, 52);
  ctx.fillStyle = "#c4b4a0";
  ctx.font = "14px DM Sans, sans-serif";
  ctx.fillText("Messages", 36, 74);

  let y = 110;
  const recent = messages.slice(-5);
  if (recent.length === 0 && alert) {
    ctx.fillStyle = "#f6efe4";
    ctx.font = "16px DM Sans, sans-serif";
    wrapText(ctx, alert, w / 2, 200, w - 70, 22);
  }
  for (const m of recent) {
    const fromFly = m.from === "fly";
    const bubbleW = w - 90;
    const lines = wrapLines(ctx, m.text || "", bubbleW - 24, "15px DM Sans, sans-serif");
    const bh = lines.length * 20 + 24;
    const x = fromFly ? w - 30 - bubbleW : 30;
    ctx.fillStyle = fromFly ? "#3d2e22" : danger ? "#4a2020" : "#243028";
    roundRect(ctx, x, y, bubbleW, bh, 14);
    ctx.fill();
    ctx.fillStyle = "#f6efe4";
    ctx.font = "15px DM Sans, sans-serif";
    lines.forEach((line, i) => ctx.fillText(line, x + 12, y + 22 + i * 20));
    y += bh + 12;
    if (y > h - 80) break;
  }

  if (danger) {
    ctx.fillStyle = "rgba(232,93,76,0.95)";
    roundRect(ctx, 24, h - 64, w - 48, 40, 12);
    ctx.fill();
    ctx.fillStyle = "#1a0908";
    ctx.font = "700 15px DM Sans, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText((alert || "she turned her head. RUN.").slice(0, 36), w / 2, h - 38);
    ctx.textAlign = "left";
  }
}

function wrapText(ctx, text, cx, y, maxW, lineH) {
  const words = String(text).split(/\s+/);
  let line = "";
  let yy = y;
  ctx.textAlign = "center";
  for (const word of words) {
    const test = line ? `${line} ${word}` : word;
    if (ctx.measureText(test).width > maxW && line) {
      ctx.fillText(line, cx, yy);
      line = word;
      yy += lineH;
    } else line = test;
  }
  if (line) ctx.fillText(line, cx, yy);
  ctx.textAlign = "left";
}

function wrapLines(ctx, text, maxW, font) {
  ctx.font = font;
  const words = String(text).split(/\s+/);
  const lines = [];
  let line = "";
  for (const word of words) {
    const test = line ? `${line} ${word}` : word;
    if (ctx.measureText(test).width > maxW && line) {
      lines.push(line);
      line = word;
    } else line = test;
  }
  if (line) lines.push(line);
  return lines.slice(0, 4);
}
