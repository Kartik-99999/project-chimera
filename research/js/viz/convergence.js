/* Convergence canvas: five tributary streams drift rightward and
 * merge into a verification seal. Stage-driven (1–5): streams past
 * the current stage run faint and dormant; at stage 5 the seal
 * closes and particles are absorbed. Ambient mode loops slowly.
 * Dependency-free, DPR-aware, pauses offscreen, static frame
 * under prefers-reduced-motion. */
const STREAMS = [
  { c: '14,116,144', y: 0.14 },
  { c: '109,40,217', y: 0.32 },
  { c: '180,83,9', y: 0.50 },
  { c: '21,128,61', y: 0.68 },
  { c: '29,78,216', y: 0.86 },
];
const SEAL_X = 0.74;

// Minimal seeded PRNG (mulberry32). Used only when callers pass
// `opts.seed`; default particle layout still uses Math.random so
// existing consumers are unaffected.
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function streamY(s, t, h) {
  const base = s.y * h;
  const target = h * 0.5;
  const ease = t * t * (3 - 2 * t);
  const wobble = Math.sin(t * 5.1 + s.y * 12.0) * (1 - ease) * h * 0.028;
  return base + (target - base) * ease + wobble;
}

export function mountConvergence(canvas, opts = {}) {
  const ctx = canvas.getContext('2d');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let stage = opts.stage ?? 5;
  let ambient = opts.ambient ?? false;
  const outcome = opts.outcome ?? null; // 'success' | 'failure' | null
  const random = opts.seed == null ? Math.random : mulberry32(opts.seed);
  let raf = 0;
  let visible = true;
  let W = 0, H = 0;
  const P = [];

  function resize() {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const r = canvas.getBoundingClientRect();
    W = Math.max(80, r.width); H = Math.max(60, r.height || W * 0.32);
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function seed() {
    P.length = 0;
    const n = Math.round(Math.min(150, Math.max(48, W / 7)));
    for (let i = 0; i < n; i++) {
      const s = i % STREAMS.length;
      P.push({ s, t: random() * 0.9, v: 0.05 + random() * 0.075, r: 1 + random() * 1.7 });
    }
  }

  function sealGlow(t) {
    if (stage < 5) return 0;
    return reduced ? 0.5 : 0.35 + 0.3 * Math.sin(t / 640);
  }

  function draw(t) {
    ctx.clearRect(0, 0, W, H);
    const sealX = W * SEAL_X, sealY = H * 0.5;
    const sealR = Math.min(W, H) * (H < 120 ? 0.30 : 0.24);
    // stream threads
    for (let si = 0; si < STREAMS.length; si++) {
      const s = STREAMS[si];
      const live = si < stage;
      ctx.beginPath();
      for (let i = 0; i <= 60; i++) {
        const tt = (i / 60) * 0.94;
        const x = 8 + tt * (sealX - 8);
        const y = streamY(s, tt, H);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = live ? `rgba(${s.c},0.34)` : `rgba(${s.c},0.13)`;
      ctx.lineWidth = live ? 1.4 : 1;
      ctx.stroke();
    }
    // particles
    for (const p of P) {
      const s = STREAMS[p.s];
      const live = p.s < stage;
      const x = 8 + p.t * (sealX - 8);
      const y = streamY(s, p.t, H);
      const near = Math.max(0, 1 - Math.hypot(x - sealX, y - sealY) / (W * 0.3));
      const a = (live ? 0.28 + 0.5 * near : 0.10);
      ctx.beginPath();
      ctx.arc(x, y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${s.c},${a.toFixed(3)})`;
      ctx.fill();
    }
    // seal: closed only at stage 5; a judged failure closes in
    // red with a cross — never a check.
    const closed = stage >= 5;
    const bad = closed && outcome === 'failure';
    const SC = bad ? [185, 28, 28] : [194, 65, 12];
    const sc = (a) => `rgba(${SC[0]},${SC[1]},${SC[2]},${a})`;
    ctx.beginPath();
    ctx.arc(sealX, sealY, sealR, 0, Math.PI * 2);
    ctx.fillStyle = closed ? sc(0.12) : sc(0.05);
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.setLineDash(closed ? [] : [5, 5]);
    ctx.strokeStyle = closed ? sc(1) : sc(0.55);
    ctx.stroke();
    ctx.setLineDash([]);
    if (closed) {
      const g = sealGlow(t);
      ctx.beginPath();
      ctx.arc(sealX, sealY, sealR + 5 + g * 4, 0, Math.PI * 2);
      ctx.strokeStyle = sc((0.25 + g * 0.3).toFixed(3));
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.beginPath();
      if (bad) {
        ctx.moveTo(sealX - sealR * 0.28, sealY - sealR * 0.28);
        ctx.lineTo(sealX + sealR * 0.28, sealY + sealR * 0.28);
        ctx.moveTo(sealX + sealR * 0.28, sealY - sealR * 0.28);
        ctx.lineTo(sealX - sealR * 0.28, sealY + sealR * 0.28);
      } else {
        ctx.moveTo(sealX - sealR * 0.36, sealY + sealR * 0.02);
        ctx.lineTo(sealX - sealR * 0.08, sealY + sealR * 0.30);
        ctx.lineTo(sealX + sealR * 0.40, sealY - sealR * 0.26);
      }
      ctx.strokeStyle = sc(1);
      ctx.lineWidth = 2.4;
      ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      ctx.stroke();
    } else {
      ctx.beginPath();
      ctx.arc(sealX, sealY, 3, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(194,65,12,0.6)';
      ctx.fill();
    }
  }

  function frame(t) {
    if (!visible) { raf = requestAnimationFrame(frame); return; }
    if (ambient && !reduced) {
      stage = 1 + Math.floor(t / 2600) % 5;
    }
    if (!reduced) {
      for (const p of P) {
        const live = p.s < stage;
        p.t += p.v * (live ? 0.016 : 0.004);
        if (p.t > 0.94) { p.t = 0; }
      }
    }
    draw(t || 0);
    if (!reduced) raf = requestAnimationFrame(frame);
  }

  const ro = new ResizeObserver(() => { resize(); seed(); if (reduced) draw(0); });
  ro.observe(canvas);
  const io = new IntersectionObserver((es) => { visible = es[0].isIntersecting; }, { threshold: 0 });
  io.observe(canvas);
  resize(); seed();
  if (reduced) draw(0); else raf = requestAnimationFrame(frame);

  return {
    setStage(n) { stage = Math.max(1, Math.min(5, n)); ambient = false; if (reduced) draw(0); },
    destroy() { cancelAnimationFrame(raf); ro.disconnect(); io.disconnect(); },
  };
}
