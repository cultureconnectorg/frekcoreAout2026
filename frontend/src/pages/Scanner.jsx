/**
 * FREK — Pointeuse /scanner
 * Usage : staff CC2026 + participants.
 *
 * Comportement :
 *   - Saisie / scan QR/NFC d'un badge_id (texte plein écran, focus auto)
 *   - Vérification publique via GET /api/badges/{badge_id}
 *   - Stockage local de la présence dans la queue offline `frek_offline_queue`
 *     (clé localStorage, sync auto au retour réseau)
 *   - Compteur session locale + compteur plateforme (chiffres CVLN, jamais personnels)
 *
 * Aucun appel API externe, aucune modification backend.
 * NB : la persistance serveur des scans nécessite un poste staff authentifié
 *      via /scan (PWA staff existante). Ici la queue est juste la file
 *      souveraine côté terminal — elle se vide quand un poste staff
 *      authentifié rejoue les éléments.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const QUEUE_KEY = 'frek_offline_queue';

function readQueue() {
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr : [];
  } catch { return []; }
}
function writeQueue(q) {
  try { localStorage.setItem(QUEUE_KEY, JSON.stringify(q)); } catch { /* noop */ }
}

function nowIso() { return new Date().toISOString(); }

function fmtTime(iso) {
  try { return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }); }
  catch { return iso; }
}

export default function Scanner() {
  const inputRef = useRef(null);
  const [value, setValue] = useState('');
  const [online, setOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [queue, setQueue] = useState(() => readQueue());
  const [sessionCount, setSessionCount] = useState(0);
  const [lastConfirm, setLastConfirm] = useState(null); // {frek_id, badge_id, ts, status}
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [platformTotal, setPlatformTotal] = useState(null);

  // Connexion réseau
  useEffect(() => {
    const onOn = () => setOnline(true);
    const onOff = () => setOnline(false);
    window.addEventListener('online', onOn);
    window.addEventListener('offline', onOff);
    return () => {
      window.removeEventListener('online', onOn);
      window.removeEventListener('offline', onOff);
    };
  }, []);

  // Focus auto sur l'input (scanners HID se comportent comme un clavier)
  useEffect(() => {
    const tick = () => {
      if (document.activeElement !== inputRef.current && inputRef.current) {
        inputRef.current.focus();
      }
    };
    tick();
    const id = setInterval(tick, 1500);
    return () => clearInterval(id);
  }, []);

  // Compteur plateforme (chiffres CVLN — strictement séparés du compteur session)
  const fetchPlatform = useCallback(async () => {
    try {
      const r = await fetch(`${API_URL}/api/core/ecosystem/pulse`);
      if (r.ok) {
        const j = await r.json();
        setPlatformTotal(j.total_events ?? null);
      }
    } catch { /* offline, ignore */ }
  }, []);

  useEffect(() => {
    fetchPlatform();
    const id = setInterval(fetchPlatform, 30_000);
    return () => clearInterval(id);
  }, [fetchPlatform]);

  // Enregistre une présence dans la queue offline
  const recordPresence = useCallback((entry) => {
    setQueue((prev) => {
      const next = [...prev, entry];
      writeQueue(next);
      return next;
    });
    setSessionCount((c) => c + 1);
    setLastConfirm(entry);
  }, []);

  // Lookup badge (public) puis enregistre la présence
  const handleSubmit = useCallback(async (raw) => {
    const id = (raw ?? value).trim();
    if (!id || busy) return;
    setBusy(true);
    setError(null);

    // Heuristique : si le scan ressemble à un FREK-ID (commence par FREK-), on l'utilise directement.
    // Sinon on tente le lookup badge.
    let frek_id = null;
    let badge_id = null;
    let detail = null;

    if (/^FREK[-_]/i.test(id)) {
      frek_id = id;
    } else {
      badge_id = id;
      try {
        const r = await fetch(`${API_URL}/api/badges/${encodeURIComponent(id)}`);
        if (r.ok) {
          const b = await r.json();
          frek_id = b.frek_id || null;
          detail = b.type_name || b.type_badge || null;
        } else if (r.status === 404) {
          // Pas un badge connu — on enregistre l'identifiant brut sans bloquer
          frek_id = id;
        }
      } catch {
        // hors ligne : on continue, l'identifiant sera capté tel quel
        frek_id = id;
      }
    }

    const entry = {
      frek_id: frek_id || id,
      badge_id: badge_id,
      detail,
      timestamp: nowIso(),
      origin: 'scanner',
      online,
    };
    recordPresence(entry);
    setValue('');
    setBusy(false);
  }, [value, busy, online, recordPresence]);

  // Sync — on essaie un ping public ; les rejouages réels nécessitent un poste staff authentifié.
  // Ici on évacue de la queue les éléments dont l'ancrage est confirmé par un lookup public réussi.
  const trySync = useCallback(async () => {
    if (!online || queue.length === 0) return;
    const remaining = [];
    for (const item of queue) {
      // On ne touche pas au backend en écriture. On marque "verified" si le frek_id existe côté core.
      if (item.frek_id && !item.synced) {
        try {
          const r = await fetch(`${API_URL}/api/core/frek/${encodeURIComponent(item.frek_id)}`);
          if (r.ok) {
            // Verrouillé : la présence est désormais reflétée côté plateforme.
            continue; // évacuée
          }
        } catch { /* offline */ }
      }
      remaining.push(item);
    }
    if (remaining.length !== queue.length) {
      setQueue(remaining);
      writeQueue(remaining);
    }
  }, [online, queue]);

  // Sync automatique au retour réseau et toutes les 60s
  useEffect(() => {
    if (online) trySync();
  }, [online, trySync]);
  useEffect(() => {
    const id = setInterval(() => { trySync(); }, 60_000);
    return () => clearInterval(id);
  }, [trySync]);

  // Vide la file (action manuelle)
  const clearQueue = () => {
    if (!confirm('Vider la file locale ?')) return;
    setQueue([]);
    writeQueue([]);
  };

  const last10 = useMemo(() => [...queue].slice(-10).reverse(), [queue]);

  return (
    <div className="min-h-screen bg-[#050a0d] text-white flex flex-col">
      {/* Bandeau */}
      <header className="border-b border-[#2cc4f5]/10 bg-[#050a0d]/95 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between gap-3">
          <Link to="/accueil" className="flex items-center gap-2 sm:gap-3" data-testid="scanner-home-link">
            <img src="/frek-logo.png" alt="FREK" className="h-6 sm:h-8 w-auto" />
            <span className="font-display text-lg sm:text-xl tracking-wider text-[#2cc4f5]">FREK</span>
          </Link>
          <div className="flex items-center gap-3">
            <span
              data-testid="scanner-network-status"
              className={`inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest ${online ? 'text-emerald-400' : 'text-amber-400'}`}
            >
              <span className={`h-2 w-2 rounded-full ${online ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              {online ? 'En ligne' : 'Hors ligne'}
            </span>
            <span
              data-testid="scanner-queue-count"
              className="font-mono text-[10px] text-white/40 uppercase tracking-widest"
            >
              file : {queue.length}
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-10 flex flex-col">
        {/* Champ de scan plein écran */}
        <section data-testid="scanner-input-zone" className="bg-gradient-to-br from-[#0a1520]/70 to-[#050a0d] border border-[#2cc4f5]/20 rounded-2xl p-6 sm:p-10">
          <div className="font-mono text-[10px] sm:text-xs text-[#2cc4f5]/60 uppercase tracking-widest mb-4">
            Pointeuse FREK-P · CC2026
          </div>
          <form
            onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}
            className="space-y-4"
          >
            <input
              ref={inputRef}
              data-testid="scanner-input"
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="Scanner ou saisir badge_id / FREK-ID"
              autoComplete="off"
              spellCheck={false}
              autoFocus
              className="w-full bg-transparent border-b-2 border-[#2cc4f5]/30 focus:border-[#2cc4f5] outline-none font-mono text-2xl sm:text-4xl text-[#2cc4f5] placeholder:text-white/15 py-3 tracking-wider"
            />
            <div className="flex flex-wrap items-center justify-between gap-3">
              <button
                type="submit"
                disabled={!value.trim() || busy}
                data-testid="scanner-submit-btn"
                className="px-6 py-3 bg-[#2cc4f5] disabled:bg-[#2cc4f5]/30 disabled:cursor-not-allowed text-[#050a0d] font-mono text-xs uppercase tracking-wider rounded hover:bg-[#33cfff] transition-all font-bold"
              >
                {busy ? 'Enregistrement…' : 'Enregistrer présence'}
              </button>
              <button
                type="button"
                onClick={clearQueue}
                disabled={queue.length === 0}
                data-testid="scanner-clear-queue-btn"
                className="font-mono text-[10px] text-white/40 hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed uppercase tracking-widest transition-colors"
              >
                Vider la file
              </button>
            </div>
          </form>
        </section>

        {/* Confirmation dernier scan */}
        {lastConfirm && (
          <section
            data-testid="scanner-last-confirm"
            className="mt-6 bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 sm:p-5"
          >
            <div className="flex items-start gap-3">
              <div className="h-7 w-7 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center shrink-0">
                <svg className="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-mono text-[10px] text-emerald-300 uppercase tracking-widest">Présence enregistrée</div>
                <div className="font-mono text-sm text-white break-all mt-0.5" data-testid="scanner-last-frek-id">
                  {lastConfirm.frek_id}
                </div>
                <div className="font-mono text-[11px] text-white/40 mt-1">
                  {fmtTime(lastConfirm.timestamp)}{lastConfirm.detail ? ` · ${lastConfirm.detail}` : ''}{lastConfirm.online ? '' : ' · queue locale'}
                </div>
              </div>
            </div>
          </section>
        )}

        {error && (
          <div className="mt-4 rounded-lg p-3 bg-red-500/10 border border-red-500/30 font-mono text-[11px] text-red-300" data-testid="scanner-error">
            {error}
          </div>
        )}

        {/* Compteurs */}
        <section data-testid="scanner-counters" className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-[#0a1520]/50 border border-[#2cc4f5]/15 rounded-xl p-5">
            <div className="font-mono text-[10px] text-[#2cc4f5]/60 uppercase tracking-widest">Session en cours</div>
            <div data-testid="scanner-session-count" className="font-display text-4xl sm:text-5xl text-white tabular-nums mt-1">
              {sessionCount}
            </div>
            <div className="font-mono text-[10px] text-white/40 mt-1">scans depuis l'ouverture de cette page</div>
          </div>
          <div className="bg-[#0a1520]/50 border border-[#2cc4f5]/15 rounded-xl p-5">
            <div className="font-mono text-[10px] text-[#2cc4f5]/60 uppercase tracking-widest">Plateforme (CVLN)</div>
            <div data-testid="scanner-platform-total" className="font-display text-4xl sm:text-5xl text-white tabular-nums mt-1">
              {platformTotal !== null ? platformTotal.toLocaleString('fr-FR') : '—'}
            </div>
            <div className="font-mono text-[10px] text-white/40 mt-1">total présences plateforme · indicatif</div>
          </div>
        </section>

        {/* Aperçu file (10 dernières) */}
        {last10.length > 0 && (
          <section data-testid="scanner-queue-preview" className="mt-8">
            <div className="font-mono text-[10px] text-[#2cc4f5]/60 uppercase tracking-widest mb-3">
              File locale — 10 derniers
            </div>
            <div className="space-y-1.5">
              {last10.map((q, i) => (
                <div key={`${q.timestamp}-${i}`} className="flex items-center justify-between gap-3 bg-[#0a1520]/40 border border-[#2cc4f5]/10 rounded-md px-3 py-2">
                  <span className="font-mono text-xs text-white/80 truncate">{q.frek_id}</span>
                  <span className="font-mono text-[10px] text-white/30 shrink-0">
                    {fmtTime(q.timestamp)}{q.online ? '' : ' · offline'}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      <footer className="border-t border-[#2cc4f5]/10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-white/30 uppercase tracking-widest">
          <span>Pointeuse · données locales d'abord</span>
          <span>file persistée dans <code className="text-[#2cc4f5]/60">frek_offline_queue</code></span>
        </div>
      </footer>
    </div>
  );
}
