/**
 * FREK Scan — IndexedDB queue + auth + API client.
 * Mode offline-first : si offline, queue → sync au retour réseau.
 */
import { openDB } from 'idb';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const DB_NAME = 'frek-scan';
const DB_VERSION = 2;
const STORE_QUEUE = 'queue';
const STORE_LOG = 'log';
const TOKEN_KEY = 'frek-staff-token';
const STAFF_KEY = 'frek-staff-info';
export const MAX_RETRY_ATTEMPTS = 5;
const RETRYABLE_STATUSES = new Set([0, 401, 408, 429, 500, 502, 503, 504]);

export async function getDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_QUEUE)) {
        db.createObjectStore(STORE_QUEUE, { keyPath: 'client_uuid' });
      }
      // v2 adds an explicit durable state machine. Existing v1 records remain
      // readable and are normalized when they are first processed.
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
  if (crypto.randomUUID) return crypto.randomUUID();
  if (crypto.getRandomValues) {
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('');
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }
  throw new Error('Web Crypto est requis pour creer une operation hors ligne idempotente.');
}

export async function queueAll() {
  const db = await getDB();
  return db.getAll(STORE_QUEUE);
}

export async function queueCount() {
  const db = await getDB();
  const all = await db.getAll(STORE_QUEUE);
  return all.filter((item) => !['succeeded', 'dead_letter', 'cancelled'].includes(item.status || 'queued')).length;
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

export function classifyFailure(status) {
  return RETRYABLE_STATUSES.has(status || 0) ? 'temporary' : 'permanent';
}

export function retryDelayMs(attempts) {
  // Bounded deterministic exponential backoff: 5s, 10s, 20s, …, max 5 min.
  return Math.min(5_000 * (2 ** Math.max(0, attempts - 1)), 300_000);
}

export function isEligibleForRetry(item, now = Date.now()) {
  const status = item.status || 'queued';
  return ['queued', 'retrying', 'processing'].includes(status)
    && (!item.next_retry_at || Date.parse(item.next_retry_at) <= now);
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
  const now = new Date().toISOString();
  const existing = await db.get(STORE_QUEUE, item.client_uuid);
  if (existing) return existing;
  const queued = {
    ...item,
    correlation_id: item.correlation_id || item.client_uuid,
    status: 'queued',
    queued_at: now,
    created_at: now,
    updated_at: now,
    attempts: 0,
    next_retry_at: now,
    last_error: null,
    last_error_kind: null,
  };
  await db.add(STORE_QUEUE, queued);
  return queued;
}

function summarize(kind, r) {
  if (kind === 'access') return `${r.access} ${r.badge?.prenom || ''}`;
  if (kind === 'cashless') return `${r.transaction?.montant_jetons}J → ${r.marchand}`;
  if (kind === 'emit') return `${r.badge?.badge_id}`;
  return '';
}

export async function flushQueue() {
  const db = await getDB();
  const all = await db.getAll(STORE_QUEUE);
  const eligible = all.filter((item) => isEligibleForRetry(item));
  if (!eligible.length) return { total: 0, success: 0, failed: 0, deferred: all.length };

  const processingAt = new Date().toISOString();
  const tx = db.transaction(STORE_QUEUE, 'readwrite');
  for (const item of eligible) {
    await tx.store.put({ ...item, status: 'processing', updated_at: processingAt });
  }
  await tx.done;

  let response;
  try {
    response = await api.sync(eligible.map((item) => ({
      kind: item.kind,
      payload: item.payload,
      client_uuid: item.client_uuid,
      correlation_id: item.correlation_id,
    })));
  } catch (error) {
    const status = error.status || 0;
    await Promise.all(eligible.map((item) => updateFailedItem(item, status, error.body?.detail || error.message)));
    await logAdd({ kind: 'sync', status: 'retrying', error: String(error.message || 'network error') });
    return { total: eligible.length, success: 0, failed: eligible.length, deferred: all.length - eligible.length };
  }

  const results = new Map((response.results || []).map((result) => [result.client_uuid, result]));
  let success = 0;
  for (const item of eligible) {
    const result = results.get(item.client_uuid) || { ok: false, status: 0, error: 'Reponse de synchronisation incomplete' };
    if (result.ok) {
      success += 1;
      await db.put(STORE_QUEUE, {
        ...item,
        status: 'succeeded',
        succeeded_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_error: null,
        last_error_kind: null,
      });
    } else {
      await updateFailedItem(item, result.status || 0, result.error || 'Synchronisation refusee');
    }
  }
  const failed = eligible.length - success;
  await logAdd({ kind: 'sync', status: failed ? 'partial' : 'succeeded', summary: `${success}/${eligible.length}` });
  return { total: eligible.length, success, failed, deferred: all.length - eligible.length, results: response.results || [] };
}

async function updateFailedItem(item, status, message) {
  const db = await getDB();
  const attempts = (item.attempts || 0) + 1;
  const failureKind = classifyFailure(status);
  const deadLetter = failureKind === 'permanent' || attempts >= MAX_RETRY_ATTEMPTS;
  const now = new Date();
  await db.put(STORE_QUEUE, {
    ...item,
    attempts,
    status: deadLetter ? 'dead_letter' : 'retrying',
    updated_at: now.toISOString(),
    next_retry_at: deadLetter ? null : new Date(now.getTime() + retryDelayMs(attempts)).toISOString(),
    last_error: String(message),
    last_error_kind: deadLetter && failureKind !== 'permanent' ? 'retry_exhausted' : failureKind,
  });
}
