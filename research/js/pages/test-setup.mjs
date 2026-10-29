/* Shared harness for Node render tests (no browser available).
 * Serves repo files for data.js fetch calls and provides fake elements.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export function installFetch(root) {
  globalThis.fetch = async (url) => {
    const rel = String(url).replace(/^\/+/, '');
    try {
      const body = readFileSync(join(root, rel), 'utf8');
      return { ok: true, json: async () => JSON.parse(body), text: async () => body };
    } catch {
      return { ok: false, status: 404 };
    }
  };
}

export function fakeHost() {
  return { innerHTML: '', querySelectorAll: () => [] };
}

export function fakeEl(handlers = {}) {
  return {
    innerHTML: '',
    querySelector: (sel) => handlers[sel] || { addEventListener() {} },
    querySelectorAll: () => [],
  };
}

export const countClass = (html, cls) => html.split(`class="${cls}"`).length - 1;
