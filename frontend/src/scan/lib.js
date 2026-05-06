/**
 * FREK Scan — IndexedDB queue + auth + API client.
 * Mode offline-first : si offline, queue → sync au retour réseau.
 */
import { openDB } from 'idb';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const DB_NAME = 'frek-scan';
const STORE_QUEUE = 'queue';
const STORE_LOG = 'log';
const TOKEN_KEY = 'frek-staff-token';
const STAFF_KEY = 'frek-staff-info';

export async function getDB() {
  return openDB(DB_NAME, 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_QUEUE)) {
        db.createObjectStore(STORE_QUEUE, { keyPath: 'client_uuid' });
      }
      if (!db.objectStoreNames.contains(STORE_LOG)) {
        const s = db.createObjectStore(STORE_LOG, { keyPath: 'id', autoIncrement: true });
        s.createIndex('ts', 'ts');
      }
    },
  });
}

// --- Auth ---
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function getStaff() {
  const raw = localStorage.getItem(STAFF_KEY);
  return raw ? JSON.parse(raw) : null;
}
export function setSession(token, staff) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(STAFF_KEY, JSON.stringify(staff));
}
export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(STAFF_KEY);
}

// --- API ---
async function apiFetch(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  const tok = getToken();
  if (tok) headers.Authorization = `Bearer ${tok}`;
  const res = await fetch(`${API_URL}${path}`, { ...opts, headers });
  const ct = res.headers.get('content-type') || '';
  const body = ct.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) {
    const err = new Error(body?.detail || body || `HTTP ${res.status}`);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

export const api = {
  login: (agent_id, pin) =>
    apiFetch('/api/v1/staff/login', { method: 'POST', body: JSON.stringify({ agent_id, pin }) }),
  me: () => apiFetch('/api/v1/staff/me'),
  zones: () => apiFetch('/api/v1/staff/scan/zones'),
  marchands: () => apiFetch('/api/v1/staff/scan/marchands'),
  badge: (code) => apiFetch(`/api/v1/staff/scan/badge/${encodeURIComponent(code)}`),
  access: (payload) =>
    apiFetch('/api/v1/staff/scan/access', { method: 'POST', body: JSON.stringify(payload) }),
  cashless: (payload) =>
    apiFetch('/api/v1/staff/scan/cashless', { method: 'POST', body: JSON.stringify(payload) }),
  emit: (payload) =>
    apiFetch('/api/v1/staff/scan/emit', { method: 'POST', body: JSON.stringify(payload) }),
  sync: (actions) =>
    apiFetch('/api/v1/staff/scan/sync', { method: 'POST', body: JSON.stringify({ actions }) }),
};

// --- Offline queue ---
function uuid() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export async function queueAll() {
  const db = await getDB();
  return db.getAll(STORE_QUEUE);
}

export async function queueCount() {
  const db = await getDB();
  return db.count(STORE_QUEUE);
}

export async function queueRemove(client_uuid) {
  const db = await getDB();
  await db.delete(STORE_QUEUE, client_uuid);
}

export async function queueClear() {
  const db = await getDB();
  const tx = db.transaction(STORE_QUEUE, 'readwrite');
  await tx.objectStore(STORE_QUEUE).clear();
  await tx.done;
}

export async function logAdd(entry) {
  const db = await getDB();
  await db.add(STORE_LOG, { ...entry, ts: new Date().toISOString() });
}

export async function logRecent(limit = 50) {
  const db = await getDB();
  const tx = db.transaction(STORE_LOG, 'readonly');
  const store = tx.objectStore(STORE_LOG);
  const idx = store.index('ts');
  const all = [];
  let cursor = await idx.openCursor(null, 'prev');
  while (cursor && all.length < limit) {
    all.push(cursor.value);
    cursor = await cursor.continue();
  }
  return all;
}

/**
 * Try online action. If offline / network fails, queue it.
 * Returns { ok, queued, result, error }.
 * client_uuid est injecte dans le payload pour idempotence backend (replay-safe).
 */
export async function tryOrQueue(kind, payload, onlineFn) {
  const client_uuid = uuid();
  const stamped = { ...payload, client_uuid };
  if (!navigator.onLine) {
    await queuePushItem({ client_uuid, kind, payload: stamped });
    await logAdd({ kind, status: 'queued_offline', payload: stamped });
    return { ok: false, queued: true };
  }
  try {
    const result = await onlineFn(stamped);
    await logAdd({ kind, status: 'success', payload: stamped, summary: summarize(kind, result) });
    return { ok: true, result };
  } catch (e) {
    if (e.status) {
      await logAdd({ kind, status: 'error', payload: stamped, error: String(e.body?.detail || e.message) });
      return { ok: false, error: e.body?.detail || e.message, status: e.status };
    }
    await queuePushItem({ client_uuid, kind, payload: stamped });
    await logAdd({ kind, status: 'queued_network', payload: stamped });
    return { ok: false, queued: true, error: 'Réseau indisponible — mis en file' };
  }
}

async function queuePushItem(item) {
  const db = await getDB();
  await db.add(STORE_QUEUE, {
    ...item,
    queued_at: new Date().toISOString(),
    attempts: 0,
  });
}

function summarize(kind, r) {
  if (kind === 'access') return `${r.access} ${r.badge?.prenom || ''}`;
  if (kind === 'cashless') return `${r.transaction?.montant_jetons}J → ${r.marchand}`;
  if (kind === 'emit') return `${r.badge?.badge_id}`;
  return '';
}

export async function flushQueue() {
  const all = await queueAll();
  if (!all.length) return { total: 0, success: 0, failed: 0 };
  const actions = all.map((a) => ({ kind: a.kind, payload: a.payload, client_uuid: a.client_uuid }));
  const res = await api.sync(actions);
  const ok = new Set(res.results.filter((r) => r.ok).map((r) => r.client_uuid));
  for (const u of ok) await queueRemove(u);
  await logAdd({ kind: 'sync', status: 'flushed', summary: `${res.success}/${res.total}` });
  return res;
}
