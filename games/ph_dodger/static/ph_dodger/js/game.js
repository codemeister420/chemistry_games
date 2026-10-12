// pH Dodger (Canvas) — simple balls with colored text
// Tokens:
// - H+ : pH down (acid)  -> red text / light red ball
// - OH-: pH up (base)   -> blue text / light blue ball
// - BUF: buffer pickup  -> green text / light green ball
// - CO2: slow acidify   -> black text / gray ball
// - NaCl: neutral-ish   -> black text / beige ball

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const HUD = {
  score: document.getElementById("score"),
  ph: document.getElementById("ph"),
  buf: document.getElementById("buf"),
  pka: document.getElementById("pka"),
  diff: document.getElementById("diff"),
};

const W = canvas.width;
const H = canvas.height;

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function randInt(n) { return Math.floor(Math.random() * n); }

let keys = {};
window.addEventListener("keydown", (e) => { keys[(e.key || "").toLowerCase()] = true; });
window.addEventListener("keyup", (e) => { keys[(e.key || "").toLowerCase()] = false; });

function keyDown(name) { return !!keys[name]; }
function nowMs() { return (window.performance && performance.now) ? performance.now() : Date.now(); }

// --- Player ---
const player = {
  x: W / 2,
  y: H - 60,
  r: 18,
  speed: 5.2,
};

// --- Chemistry state ---
let score = 0;
let ph = 7.00;

// Buffer model
let bufferUntil = 0;
let bufferPka = null;
let bufferCapacity = 0;

// CO2 model (slow acidification)
let co2Until = 0;

// Difficulty scaling
let startTime = nowMs();
let difficulty = 1.0;

// Falling particles
let particles = [];

const TYPES = [
  { kind: "H",   label: "H⁺",   weight: 28 },
  { kind: "OH",  label: "OH⁻",  weight: 28 },
  { kind: "BUF", label: "BUF",  weight: 16 },
  { kind: "CO2", label: "CO₂",  weight: 12 },
  { kind: "SAL", label: "NaCl", weight: 16 },
];

function weightedPick(items) {
  const total = items.reduce((s, it) => s + it.weight, 0);
  let r = Math.random() * total;
  for (let i = 0; i < items.length; i++) {
    r -= items[i].weight;
    if (r <= 0) return items[i];
  }
  return items[items.length - 1];
}

// pKa choices (common-ish buffers)
const PKA_CHOICES = [4.8, 6.1, 7.2, 8.3, 9.2];

function bufferActive() {
  return nowMs() < bufferUntil && bufferCapacity > 0.001 && bufferPka !== null;
}

function bufferEffectMultiplier(currentPh) {
  // Strongest buffering near pKa; weaker far away.
  // multiplier in [0.25 .. 1.0]
  if (!bufferActive()) return 1.0;
  const d = Math.abs(currentPh - bufferPka);
  const t = clamp(d / 3.0, 0, 1);
  return 0.25 + 0.75 * t;
}

function consumeBuffer(amount) {
  bufferCapacity = clamp(bufferCapacity - amount, 0, 999);
  if (bufferCapacity <= 0.001) {
    bufferUntil = 0;
    bufferPka = null;
  }
}

function spawnParticle() {
  const t = weightedPick(TYPES);

  const p = {
    kind: t.kind,
    label: t.label,
    x: randInt(W - 40) + 20,
    y: -20,
    r: 18,
    vy: (2.2 + Math.random() * 1.2) * difficulty,
    vx: (Math.random() - 0.5) * 1.0 * difficulty,
  };

  if (p.kind === "BUF") p.r = 20;
  if (p.kind === "SAL") p.r = 16;

  particles.push(p);
}

function circleHit(ax, ay, ar, bx, by, br) {
  const dx = ax - bx, dy = ay - by;
  return (dx*dx + dy*dy) <= (ar + br) * (ar + br);
}

function gameOver(reason) {
  alert("Game over: " + reason + "\nScore: " + score + "\nFinal pH: " + ph.toFixed(2));
  window.location.reload();
}

// --- Particle styles (balls + colored text) ---
function particleStyle(kind) {
  if (kind === "H")   return { fill: "#ffd6d6", text: "#b00000" }; // acid
  if (kind === "OH")  return { fill: "#dbe9ff", text: "#003f9e" }; // base
  if (kind === "BUF") return { fill: "#e3f7e3", text: "#1b6b1b" }; // buffer
  if (kind === "CO2") return { fill: "#eeeeee", text: "#000000" }; // CO2
  if (kind === "SAL") return { fill: "#fff3d6", text: "#000000" }; // salt
  return { fill: "#ffffff", text: "#000000" };
}

// --- Apply effects ---
function applyHit(kind) {
  // Base pH change per hit (tune here)
  let dPh = 0;

  if (kind === "H") dPh = -0.70;
  if (kind === "OH") dPh = +0.70;

  if (kind === "H" || kind === "OH") {
    // Buffer reduces impact, strongest near pKa
    const mult = bufferEffectMultiplier(ph);
    const before = dPh;
    dPh = dPh * mult;

    // capacity drain based on how much it absorbed
    if (bufferActive()) {
      const absorbed = Math.abs(before - dPh);
      consumeBuffer(absorbed * 0.9);
    }

    ph = clamp(ph + dPh, 0, 14);
    score += 2;
    return;
  }

  if (kind === "BUF") {
    bufferPka = PKA_CHOICES[randInt(PKA_CHOICES.length)];
    bufferCapacity = 3.2;
    bufferUntil = nowMs() + 9000;
    score += 8;
    return;
  }

  if (kind === "CO2") {
    co2Until = nowMs() + 6000;
    score += 4;
    return;
  }

  if (kind === "SAL") {
    score += 3;
    // tiny drift toward neutral
    ph += (7.0 - ph) * 0.10;
    return;
  }
}

function updateHud() {
  HUD.score.textContent = String(score);
  HUD.ph.textContent = ph.toFixed(2);
  HUD.diff.textContent = difficulty.toFixed(2) + "x";

  if (bufferActive()) {
    const secs = Math.ceil((bufferUntil - nowMs()) / 1000);
    HUD.buf.textContent = "ON (" + secs + "s, cap " + bufferCapacity.toFixed(1) + ")";
    HUD.pka.textContent = bufferPka.toFixed(1);
  } else {
    HUD.buf.textContent = "OFF";
    HUD.pka.textContent = "—";
  }
}

// --- Main loop ---
let lastSpawn = nowMs();

function tick() {
  const t = nowMs();
  const elapsed = (t - startTime) / 1000;

  // Difficulty ramps over time
  difficulty = 1.0 + elapsed * 0.03;

  // Move player
  let dx = 0, dy = 0;
  if (keyDown("arrowleft") || keyDown("a")) dx -= 1;
  if (keyDown("arrowright") || keyDown("d")) dx += 1;
  if (keyDown("arrowup") || keyDown("w")) dy -= 1;
  if (keyDown("arrowdown") || keyDown("s")) dy += 1;

  if (dx !== 0 && dy !== 0) { dx *= 0.707; dy *= 0.707; }

  player.x = clamp(player.x + dx * player.speed, player.r, W - player.r);
  player.y = clamp(player.y + dy * player.speed, player.r, H - player.r);

  // CO2 slow acidification
  if (t < co2Until) {
    ph = clamp(ph - 0.010 * difficulty, 0, 14);
  }

  // Spawn particles (faster over time)
  const spawnInterval = clamp(650 - elapsed * 7, 220, 650);
  if (t - lastSpawn > spawnInterval) {
    spawnParticle();
    if (Math.random() < clamp(0.08 + elapsed * 0.004, 0, 0.35)) spawnParticle();
    lastSpawn = t;
  }

  // Move particles + collisions
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.x += p.vx;
    p.y += p.vy;

    // bounce off side walls
    if (p.x < p.r) { p.x = p.r; p.vx *= -0.6; }
    if (p.x > W - p.r) { p.x = W - p.r; p.vx *= -0.6; }

    // collision with player
    if (circleHit(player.x, player.y, player.r, p.x, p.y, p.r)) {
      applyHit(p.kind);
      particles.splice(i, 1);
      continue;
    }

    // off screen
    if (p.y > H + 40) {
      particles.splice(i, 1);
      // missing H/OH slightly nudges pH (environment instability)
      if (p.kind === "H") ph = clamp(ph - 0.05, 0, 14);
      if (p.kind === "OH") ph = clamp(ph + 0.05, 0, 14);
    }
  }

  // Lose condition
  if (ph <= 0.2) return gameOver("Too acidic");
  if (ph >= 13.8) return gameOver("Too basic");

  // Draw
  draw();
  updateHud();
  requestAnimationFrame(tick);
}

// --- Drawing ---
function draw() {
  ctx.clearRect(0, 0, W, H);

  // background grid
  ctx.save();
  ctx.globalAlpha = 0.10;
  ctx.strokeStyle = "#000";
  for (let x = 0; x <= W; x += 20) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, H);
    ctx.stroke();
  }
  for (let y = 0; y <= H; y += 20) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }
  ctx.restore();

  // pH bar (top)
  const barW = W - 20;
  const barX = 10;
  const barY = 10;
  const barH = 12;

  ctx.save();
  ctx.globalAlpha = 0.9;
  ctx.strokeStyle = "#000";
  ctx.fillStyle = "#000";
  ctx.strokeRect(barX, barY, barW, barH);
  const frac = ph / 14.0;
  ctx.fillRect(barX, barY, barW * frac, barH);
  ctx.restore();

  // particles (balls + colored text)
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    const style = particleStyle(p.kind);

    // ball
    ctx.fillStyle = style.fill;
    ctx.strokeStyle = "#000";
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // label
    ctx.fillStyle = style.text;
    ctx.font = "bold 14px Arial";
    ctx.fillText(p.label, p.x, p.y);
  }

  // player droplet
  ctx.save();
  ctx.fillStyle = "#000";
  ctx.strokeStyle = "#000";
  ctx.beginPath();
  ctx.arc(player.x, player.y, player.r, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.restore();

  // buffer aura
  if (bufferActive()) {
    ctx.save();
    ctx.globalAlpha = 0.18;
    ctx.fillStyle = "#1b6b1b";
    ctx.beginPath();
    ctx.arc(player.x, player.y, player.r + 16, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // CO2 warning
  if (nowMs() < co2Until) {
    ctx.save();
    ctx.globalAlpha = 0.85;
    ctx.fillStyle = "#000";
    ctx.font = "12px Arial";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.fillText("CO₂ dissolving…", W - 12, 40);
    ctx.restore();
  }
}

// Start
updateHud();
requestAnimationFrame(tick);
