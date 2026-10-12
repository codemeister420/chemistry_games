
// Carbohydrate Snake (RNG chemistry version)
// - Head PNG animation (normal + eating face)
// - C= only affects the neck bond (head->next segment) when eaten
// - Added: F (fluorine) makes you membrane-permeable -> wall wrap for a few seconds

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const GRID = 20;
const TILE = canvas.width / GRID;

function randInt(n) { return Math.floor(Math.random() * n); }
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

const HUD = {
  score: document.getElementById("score"),
  speed: document.getElementById("speed"),
  turnPenalty: document.getElementById("turnPenalty"),
  perm: document.getElementById("perm"),
  lastToken: document.getElementById("lastToken"),
};

// RNG chemistry tokens
const TOKENS = [
  { kind: "C",  label: "C",  weight: 44 },
  { kind: "DB", label: "C=", weight: 16 },
  { kind: "O",  label: "O",  weight: 14 },
  { kind: "N",  label: "N",  weight: 10 },
  { kind: "X",  label: "X",  weight: 12 },
  { kind: "F",  label: "F",  weight: 4  }, // membrane-permeable power
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

// ---------- Head images (normal/eat) ----------
function scriptDir() {
  // Find directory of this game.js file from the currently loaded script tag
  const scripts = document.getElementsByTagName("script");
  let src = "";
  for (let i = 0; i < scripts.length; i++) {
    const s = scripts[i].getAttribute("src") || "";
    if (s.indexOf("carb_snake/js/game.js") !== -1 || s.endsWith("/game.js")) {
      src = s;
    }
  }
  const lastSlash = src.lastIndexOf("/");
  if (lastSlash === -1) return "";
  return src.substring(0, lastSlash + 1);
}

const headNormalImg = new Image();
const headEatImg = new Image();

// game.js is in: static/carb_snake/js/game.js
// images in: static/carb_snake/img/
headNormalImg.src = scriptDir() + "../img/head_normal.png";
headEatImg.src = scriptDir() + "../img/head_eat.png";

let imagesReady = false;
let imagesToLoad = 2;

function onImgLoaded() {
  imagesToLoad -= 1;
  if (imagesToLoad <= 0) imagesReady = true;
}
function onImgError() {
  imagesToLoad -= 1;
  if (imagesToLoad <= 0) imagesReady = false;
}

headNormalImg.onload = onImgLoaded;
headEatImg.onload = onImgLoaded;
headNormalImg.onerror = onImgError;
headEatImg.onerror = onImgError;

// Eating animation timing
let eatFaceUntil = 0;
const EAT_FACE_MS = 180;

// ---------- Membrane permeability ----------
let membraneUntil = 0;
const MEMBRANE_MS = 4500;

function nowMs() { return (window.performance && performance.now) ? performance.now() : Date.now(); }
function membraneActive() { return nowMs() < membraneUntil; }

// ---------- Game state ----------
let snake = [
  { x: 10, y: 10, sidechains: [], bondToPrev: "single" },
  { x: 9,  y: 10, sidechains: [], bondToPrev: "single" },
  { x: 8,  y: 10, sidechains: [], bondToPrev: "single" },
];

let dir = { x: 1, y: 0 };
let pendingDir = { x: 1, y: 0 };

let score = 0;
let tickMs = 120;

let turnCooldown = 0;
let rigidityStacks = 0;
let heavyPenalty = 0;

let food = spawnFood();

// ---------- Controls ----------
window.addEventListener("keydown", (e) => {
  const key = (e.key || "").toLowerCase();
  let nd = null;

  if (key === "arrowup" || key === "w") nd = { x: 0, y: -1 };
  if (key === "arrowdown" || key === "s") nd = { x: 0, y: 1 };
  if (key === "arrowleft" || key === "a") nd = { x: -1, y: 0 };
  if (key === "arrowright" || key === "d") nd = { x: 1, y: 0 };

  if (!nd) return;
  if (nd.x === -dir.x && nd.y === -dir.y) return;
  if (turnCooldown > 0) return;

  pendingDir = nd;
});

// ---------- Spawning / collision ----------
function tileOccupied(x, y) {
  for (let i = 0; i < snake.length; i++) {
    const seg = snake[i];
    if (seg.x === x && seg.y === y) return true;
    for (let j = 0; j < seg.sidechains.length; j++) {
      const sc = seg.sidechains[j];
      if (sc.x === x && sc.y === y) return true;
    }
  }
  return false;
}

function spawnFood() {
  const token = weightedPick(TOKENS);
  while (true) {
    const x = randInt(GRID);
    const y = randInt(GRID);
    if (tileOccupied(x, y)) continue;
    return { x, y, token };
  }
}

function gameOver(reason) {
  alert("Game over: " + reason + "\nScore: " + score);
  window.location.reload();
}

// ---------- Chemistry effects ----------
function addSidechainToNewestSegment(force) {
  const head = snake[0];

  const perps = [];
  if (dir.x !== 0) perps.push({ x: 0, y: 1 }, { x: 0, y: -1 });
  else perps.push({ x: 1, y: 0 }, { x: -1, y: 0 });

  const candidates = [];
  for (let i = 0; i < perps.length; i++) {
    const p = perps[i];
    const sx = head.x + p.x;
    const sy = head.y + p.y;
    if (sx < 0 || sx >= GRID || sy < 0 || sy >= GRID) continue;
    if (tileOccupied(sx, sy)) continue;
    candidates.push({ x: sx, y: sy });
  }

  if (candidates.length === 0) {
    if (force) head.sidechains.push({ x: head.x, y: head.y });
    return;
  }

  head.sidechains.push(candidates[randInt(candidates.length)]);
}

function applyToken(token) {
  HUD.lastToken.textContent = token.label + " (" + token.kind + ")";

  if (token.kind === "C") {
    score += 2;
    if (Math.random() < 0.08) addSidechainToNewestSegment(false);
  }

  if (token.kind === "DB") {
    // Neck-only double bond
    if (snake.length > 0) snake[0].bondToPrev = "double";

    rigidityStacks += 1;
    score += 3;
    tickMs = clamp(tickMs + 12, 80, 220);
  }

  if (token.kind === "O") {
    score += 3;
    addSidechainToNewestSegment(true);
    tickMs = clamp(tickMs + 6, 80, 240);
  }

  if (token.kind === "N") {
    score += 3;
    tickMs = clamp(tickMs + 4, 80, 240);
    if (Math.random() < 0.12) addSidechainToNewestSegment(false);
  }

  if (token.kind === "X") {
    heavyPenalty += 1;
    score += 2;
    tickMs = clamp(tickMs + 10, 80, 240);
  }

  if (token.kind === "F") {
    // Membrane-permeable (wrap walls)
    score += 5;
    membraneUntil = nowMs() + MEMBRANE_MS;
    tickMs = clamp(tickMs - 6, 70, 240); // tiny “boost”
  }

  updateHud();
}

function updateHud() {
  HUD.score.textContent = String(score);
  HUD.speed.textContent = (120 / tickMs).toFixed(2) + "x";
  HUD.turnPenalty.textContent = String(rigidityStacks);

  if (HUD.perm) {
    if (membraneActive()) {
      const left = Math.ceil((membraneUntil - nowMs()) / 1000);
      HUD.perm.textContent = "ON (" + left + "s)";
    } else {
      HUD.perm.textContent = "OFF";
    }
  }
}

// ---------- Rendering helpers ----------
function drawBond(x1, y1, x2, y2, type) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;

  const ox = (-dy / len) * 3;
  const oy = ( dx / len) * 3;

  ctx.lineWidth = 3;

  if (type === "double") {
    ctx.beginPath();
    ctx.moveTo(x1 + ox, y1 + oy);
    ctx.lineTo(x2 + ox, y2 + oy);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(x1 - ox, y1 - oy);
    ctx.lineTo(x2 - ox, y2 - oy);
    ctx.stroke();
  } else {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }
}

function drawCircle(cx, cy, r) {
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();
}

function drawHeadImage(x, y) {
  const t = nowMs();
  const img = (t < eatFaceUntil) ? headEatImg : headNormalImg;

  const pad = 2;
  const px = x * TILE + pad;
  const py = y * TILE + pad;
  const size = TILE - pad * 2;

  if (!imagesReady || !img.complete) {
    ctx.fillStyle = "#111";
    drawCircle((x + 0.5) * TILE, (y + 0.5) * TILE, TILE * 0.33);
    return;
  }

  ctx.drawImage(img, px, py, size, size);
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Grid
  ctx.save();
  ctx.globalAlpha = 0.15;
  ctx.strokeStyle = "#000";
  for (let i = 0; i <= GRID; i++) {
    ctx.beginPath();
    ctx.moveTo(i * TILE, 0);
    ctx.lineTo(i * TILE, canvas.height);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(0, i * TILE);
    ctx.lineTo(canvas.width, i * TILE);
    ctx.stroke();
  }
  ctx.restore();

  // Food label
  ctx.fillStyle = "#111";
  ctx.font = Math.floor(TILE * 0.55) + "px Arial";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(food.token.label, (food.x + 0.5) * TILE, (food.y + 0.5) * TILE);

  // Bonds
  ctx.strokeStyle = "#111";
  for (let i = 1; i < snake.length; i++) {
    const a = snake[i - 1];
    const b = snake[i];
    drawBond(
      (a.x + 0.5) * TILE, (a.y + 0.5) * TILE,
      (b.x + 0.5) * TILE, (b.y + 0.5) * TILE,
      a.bondToPrev || "single"
    );
  }

  // Sidechain bonds (single)
  for (let i = 0; i < snake.length; i++) {
    const seg = snake[i];
    const sx = (seg.x + 0.5) * TILE;
    const sy = (seg.y + 0.5) * TILE;
    for (let j = 0; j < seg.sidechains.length; j++) {
      const sc = seg.sidechains[j];
      drawBond(sx, sy, (sc.x + 0.5) * TILE, (sc.y + 0.5) * TILE, "single");
    }
  }

  // Snake (head + body circles)
  const rMain = TILE * 0.33;
  const rSide = TILE * 0.18;

  drawHeadImage(snake[0].x, snake[0].y);

  ctx.fillStyle = "#111";
  for (let i = 1; i < snake.length; i++) {
    const seg = snake[i];
    drawCircle((seg.x + 0.5) * TILE, (seg.y + 0.5) * TILE, rMain);
    for (let j = 0; j < seg.sidechains.length; j++) {
      const sc = seg.sidechains[j];
      drawCircle((sc.x + 0.5) * TILE, (sc.y + 0.5) * TILE, rSide);
    }
  }
  // Head sidechains
  for (let j = 0; j < snake[0].sidechains.length; j++) {
    const sc = snake[0].sidechains[j];
    drawCircle((sc.x + 0.5) * TILE, (sc.y + 0.5) * TILE, rSide);
  }
}

// ---------- Game loop ----------
function step() {
  dir = pendingDir;

  // Next position
  let nx = snake[0].x + dir.x;
  let ny = snake[0].y + dir.y;

  // Wall logic: if permeable -> wrap, else die
  const hitWall = (nx < 0 || nx >= GRID || ny < 0 || ny >= GRID);
  if (hitWall) {
    if (membraneActive()) {
      if (nx < 0) nx = GRID - 1;
      if (nx >= GRID) nx = 0;
      if (ny < 0) ny = GRID - 1;
      if (ny >= GRID) ny = 0;
    } else {
      return gameOver("Hit bilayer membrane");
    }
  }

  const newHead = { x: nx, y: ny, sidechains: [], bondToPrev: "single" };

  if (tileOccupied(newHead.x, newHead.y)) {
    return gameOver("Collided with yourself");
  }

  snake.unshift(newHead);

  const ate = (newHead.x === food.x && newHead.y === food.y);
  if (ate) {
    eatFaceUntil = nowMs() + EAT_FACE_MS;
    applyToken(food.token);
    food = spawnFood();
  } else {
    snake.pop();
  }

  // Rotation restriction
  turnCooldown = clamp(rigidityStacks, 0, 6);
  if (turnCooldown > 0) turnCooldown -= 1;

  updateHud();
  draw();
  setTimeout(step, tickMs);
}

// Start
updateHud();
draw();
setTimeout(step, tickMs);
