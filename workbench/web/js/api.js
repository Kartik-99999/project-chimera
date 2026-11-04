/* Workbench API client. */
const BASE = '/api/workbench';

async function request(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* non-JSON */ }
  if (!res.ok) {
    const err = new Error((data && data.error) || `HTTP ${res.status}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  health: () => request('GET', '/health'),
  workflows: () => request('GET', '/workflows'),
  facets: () => request('GET', '/facets'),
  start: (payload) => request('POST', '/executions', payload),
  list: (params) => request('GET', '/executions' + (params || '')),
  get: (id) => request('GET', `/executions/${encodeURIComponent(id)}`),
  cancel: (id) => request('POST', `/executions/${encodeURIComponent(id)}/cancel`),
  remove: (id) => request('DELETE', `/executions/${encodeURIComponent(id)}`),
  analytics: (name, params) => request('GET', `/analytics/${name}${params || ''}`),
  artifact: (id, kind) => `${BASE}/executions/${encodeURIComponent(id)}/artifact?kind=${kind}`,
  exportCsv: (params) => `${BASE}/export.csv${params || ''}`,
  campaigns: () => request('GET', '/campaigns'),
  createCampaign: (payload) => request('POST', '/campaigns', payload),
  campaign: (id) => request('GET', `/campaigns/${encodeURIComponent(id)}`),
  campaignAction: (id, action) => request('POST', `/campaigns/${encodeURIComponent(id)}/${action}`),
  studioMeta: () => request('GET', '/studio/meta'),
  studioList: () => request('GET', '/studio/workflows'),
  studioGet: (id, version) => request('GET', `/studio/workflows/${encodeURIComponent(id)}${version ? `?version=${version}` : ''}`),
  studioCreate: (payload) => request('POST', '/studio/workflows', payload),
  studioSave: (id, definition) => request('POST', `/studio/workflows/${encodeURIComponent(id)}`, { definition }),
  studioClone: (id) => request('POST', `/studio/workflows/${encodeURIComponent(id)}/clone`),
  studioValidate: (definition, environment) => request('POST', '/studio/validate', { definition, environment }),
  stepShot: (id, ref) => `${BASE}/executions/${encodeURIComponent(id)}/artifact?kind=stepshot&ref=${encodeURIComponent(ref)}`,
};

export function queryString(obj) {
  const parts = [];
  for (const [k, v] of Object.entries(obj || {})) {
    if (v === undefined || v === null || v === '') continue;
    for (const item of Array.isArray(v) ? v : [v]) {
      parts.push(`${encodeURIComponent(k)}=${encodeURIComponent(item)}`);
    }
  }
  return parts.length ? `?${parts.join('&')}` : '';
}
