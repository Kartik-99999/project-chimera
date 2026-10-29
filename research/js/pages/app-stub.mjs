/* Test-only stub of app.js link(). Kept identical to the real
 * implementation by link-parity assertions in render tests. */
export function link(id, params = [], query = {}) {
  let h = `#/${id}`;
  for (const p of params) h += `/${encodeURIComponent(p)}`;
  const qs = Object.entries(query).filter(([, v]) => v !== '' && v != null)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');
  return qs ? `${h}?${qs}` : h;
}
