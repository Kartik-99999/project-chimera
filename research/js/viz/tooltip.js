/* Shared accessible tooltip. Content is always caller-supplied —
 * exact values and denominators, never computed decoration.
 * SVG marks additionally carry <title> as a baseline.
 */
let tip = null;

function ensure() {
  if (tip) return tip;
  tip = document.createElement('div');
  tip.className = 'viz-tip';
  tip.setAttribute('role', 'tooltip');
  tip.hidden = true;
  document.body.appendChild(tip);
  return tip;
}

function place(x, y) {
  const el = ensure();
  const pad = 12;
  const r = el.getBoundingClientRect();
  let left = x + 14;
  let top = y + 16;
  if (left + r.width > window.innerWidth - pad) left = x - r.width - 14;
  if (top + r.height > window.innerHeight - pad) top = y - r.height - 14;
  el.style.left = `${Math.max(pad, left)}px`;
  el.style.top = `${Math.max(pad, top)}px`;
}

export function hideTip() {
  if (tip) tip.hidden = true;
}

/** Attach an HTML tooltip to focusable/hoverable SVG/HTML marks. */
export function attachTip(node, html) {
  const show = (x, y) => {
    const el = ensure();
    el.innerHTML = html;
    el.hidden = false;
    place(x == null ? window.innerWidth / 2 : x, y == null ? 120 : y);
  };
  node.addEventListener('mouseenter', (e) => show(e.clientX, e.clientY));
  node.addEventListener('mousemove', (e) => { if (tip && !tip.hidden) place(e.clientX, e.clientY); });
  node.addEventListener('mouseleave', hideTip);
  node.addEventListener('focus', () => {
    const r = node.getBoundingClientRect ? node.getBoundingClientRect() : null;
    show(r ? r.left + r.width / 2 : null, r ? r.top : null);
  });
  node.addEventListener('blur', hideTip);
  node.addEventListener('keydown', (e) => { if (e.key === 'Escape') hideTip(); });
}
