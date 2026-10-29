/* Ambient particle layer (canvas). The restrained-identity prototype,
 * kept: a faint drifting field behind content gaps — never behind
 * data at intensity, never animated when reduced motion is set.
 * Adaptive: sustained slow frames shed particles down to a static
 * frame. Toggle persisted in localStorage ('chimera-motion').
 */
const COLORS = ['57,208,216', '167,139,250', '140,155,175'];
let canvas = null;
let ctx = null;
let dots = [];
let raf = 0;
let ema = 16;
let slowFrames = 0;
let enabled = true;

function targetCount() {
  const w = window.innerWidth;
  if (w < 700) return 36;
  if (w < 1200) return 70;
  return 110;
}

function seed(n) {
  const w = window.innerWidth, h = window.innerHeight;
  dots = Array.from({ length: n }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.22,
    vy: (Math.random() - 0.5) * 0.22,
    r: 0.8 + Math.random() * 1.6,
    c: COLORS[(Math.random() * COLORS.length) | 0],
    a: 0.10 + Math.random() * 0.16,
  }));
}

function draw(static_, dt) {
  if (!ctx) return;
  const dpr = Math.min(1.5, window.devicePixelRatio || 1);
  const w = window.innerWidth, h = window.innerHeight;
  if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
    canvas.width = w * dpr;
    canvas.height = h * dpr;
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  const step = static_ ? 0 : Math.min(0.05, dt || 0.016);
  for (const d of dots) {
    if (step) {
      d.x += d.vx * step * 60; d.y += d.vy * step * 60;
      if (d.x < -8) d.x = w + 8; if (d.x > w + 8) d.x = -8;
      if (d.y < -8) d.y = h + 8; if (d.y > h + 8) d.y = -8;
    }
    ctx.beginPath();
    ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${d.c},${d.a.toFixed(3)})`;
    ctx.fill();
  }
  // Faint neighbor links, capped work: stride sampling keeps it O(n).
  if (!static_) {
    ctx.lineWidth = 1;
    for (let i = 0; i < dots.length; i += 3) {
      const a = dots[i];
      for (let j = i + 3; j < Math.min(dots.length, i + 15); j += 3) {
        const b = dots[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        if (dx * dx + dy * dy < 8100) {
          ctx.strokeStyle = `rgba(120,150,190,${(0.05 * (1 - (dx * dx + dy * dy) / 8100)).toFixed(3)})`;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
    }
  }
}

function loop(t) {
  const dt = t - (loop.last || t);
  loop.last = t;
  ema = ema * 0.92 + Math.min(100, dt) * 0.08;
  if (ema > 34) slowFrames += 1; else slowFrames = 0;
  if (slowFrames > 90 && dots.length > 0) {
    // Sustained jank: shed a quarter of the field, down to static.
    dots = dots.slice(0, Math.floor(dots.length * 0.75));
    slowFrames = 0;
    if (!dots.length) { stop(); return; }
  }
  draw(false, Math.min(0.05, dt / 1000));
  raf = requestAnimationFrame(loop);
}

function reducedMotion() {
  return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function stop() {
  if (raf) cancelAnimationFrame(raf);
  raf = 0;
}

function ensureCanvas() {
  if (canvas) return;
  canvas = document.createElement('canvas');
  canvas.id = 'ambient';
  canvas.setAttribute('aria-hidden', 'true');
  document.body.prepend(canvas);
  ctx = canvas.getContext('2d');
  let timer = 0;
  window.addEventListener('resize', () => {
    clearTimeout(timer);
    timer = setTimeout(() => { if (enabled) { seed(targetCount()); draw(!raf); } }, 200);
  });
  document.addEventListener('visibilitychange', () => {
    if (!enabled || reducedMotion()) return;
    if (document.hidden) stop();
    else if (!raf) { loop.last = 0; raf = requestAnimationFrame(loop); }
  });
}

export function isMotionEnabled() {
  try {
    const v = window.localStorage.getItem('chimera-motion');
    return v == null ? true : v === 'on';
  } catch {
    return true;
  }
}

export function setMotionEnabled(on) {
  enabled = !!on;
  try { window.localStorage.setItem('chimera-motion', enabled ? 'on' : 'off'); } catch { /* private mode */ }
  if (!enabled) { stop(); if (canvas) canvas.remove(); canvas = null; ctx = null; dots = []; return; }
  start();
}

export function start() {
  enabled = isMotionEnabled();
  if (!enabled) return;
  ensureCanvas();
  seed(targetCount());
  if (reducedMotion()) { draw(true); return; }
  stop();
  ema = 16; slowFrames = 0; loop.last = 0;
  raf = requestAnimationFrame(loop);
}
