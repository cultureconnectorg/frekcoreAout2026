/**
 * FREKCORE — Engagement session utility.
 *
 * Doctrine : chaque signature engage moralement. Pour éviter la friction d'une
 * coche à chaque moment, on persiste l'engagement 4h après la première signature,
 * mais on garde une trace visible et un journal d'audit accessible dans /mine.
 *
 * L'engagement est un objet local (localStorage) — pas un ancrage backend pour
 * le MVP a). Une version b) notariée pourra remplacer ce fichier sans changer
 * l'interface publique (getActive / start / link / renew / clear).
 */

const KEY = 'frek_engagement_session';
const TTL_HOURS = 4;

async function sha256Hex(input) {
  const enc = new TextEncoder().encode(input);
  const buf = await crypto.subtle.digest('SHA-256', enc);
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

function read() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function write(obj) {
  localStorage.setItem(KEY, JSON.stringify(obj));
}

export function getActiveEngagement() {
  const eng = read();
  if (!eng) return null;
  if (Date.now() > eng.expires_at) return null;
  return eng;
}

export function getAllEngagements() {
  try {
    const raw = localStorage.getItem('frek_engagement_history');
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

export async function startEngagement(sessionId) {
  const created_at = Date.now();
  const expires_at = created_at + TTL_HOURS * 3600 * 1000;
  const hash = await sha256Hex(`${sessionId || 'anon'}|${created_at}|frekcore-engagement-v1`);
  const eng = {
    id: hash.slice(0, 16),
    hash,
    session_id: sessionId || null,
    created_at,
    expires_at,
    moments: [],
  };
  write(eng);
  // Historique complet pour audit
  const history = getAllEngagements();
  history.unshift({ ...eng });
  localStorage.setItem('frek_engagement_history', JSON.stringify(history.slice(0, 50)));
  return eng;
}

export function linkMomentToEngagement(momentSummary) {
  const eng = getActiveEngagement();
  if (!eng) return null;
  eng.moments.push({
    frek_id: momentSummary.frek_id,
    title: momentSummary.title || momentSummary.metadata?.title || 'Moment sans titre',
    signed_at: Date.now(),
  });
  write(eng);
  // Aligne aussi l'entrée dans l'historique
  const history = getAllEngagements();
  const idx = history.findIndex((h) => h.id === eng.id);
  if (idx !== -1) {
    history[idx] = { ...eng };
    localStorage.setItem('frek_engagement_history', JSON.stringify(history));
  }
  return eng;
}

export function clearActiveEngagement() {
  localStorage.removeItem(KEY);
}

export function formatExpiry(expires_at) {
  const d = new Date(expires_at);
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}
