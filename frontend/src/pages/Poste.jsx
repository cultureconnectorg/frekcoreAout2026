/**
 * FREK — Poste Staff /poste
 *
 * Station authentifiée qui réinjecte la queue offline `frek_offline_queue`
 * (alimentée par /scanner sur tous les terminaux du terrain) vers le serveur,
 * via l'endpoint authentifié /api/v1/scan/access (Bearer staff PIN).
 *
 * Auth : PIN staff existant (/api/v1/staff/login) — aucune nouveauté backend.
 * Zone : sélectionnée pour toute la session (ENTREE par défaut).
 *
 * Idempotent par client_uuid (le scan_routes gère déjà la déduplication).
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const QUEUE_KEY = 'frek_offline_queue';
const SESSION_KEY = 'frek_poste_session';
const ZONES = ['ENTREE', 'SCENE', 'VIP_LOUNGE', 'BACKSTAGE', 'EXPOSANTS', 'PRESSE', 'ATELIERS'];

function readQueue() {
  try { const r = localStorage.getItem(QUEUE_KEY); const a = r ? JSON.parse(r) : []; return Array.isArray(a) ? a : []; }
  catch { return []; }
}
function writeQueue(q) { try { localStorage.setItem(QUEUE_KEY, JSON.stringify(q)); } catch { /* noop */ } }

function loadSession() {
  try { const r = sessionStorage.getItem(SESSION_KEY); return r ? JSON.parse(r) : null; } catch { return null; }
}
function saveSession(s) { try { sessionStorage.setItem(SESSION_KEY, JSON.stringify(s)); } catch { /* noop */ } }
function clearSession() { try { sessionStorage.removeItem(SESSION_KEY); } catch { /* noop */ } }

function BackgroundDecor() {
  return (
    <>
      <div aria-hidden className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl opacity-30" />
      <div aria-hidden className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl opacity-25" />
    </>
  );
}

export default function Poste() {
  const [session, setSession] = useState(() => loadSession());
  const [agentId, setAgentId] = useState('');
  const [pin, setPin] = useState('');
  const [zone, setZone] = useState('ENTREE');
  const [queue, setQueue] = useState(() => readQueue());
  const [results, setResults] = useState([]); // {entry, status:'ok'|'skip'|'error', detail}
  const [replaying, setReplaying] = useState(false);
  const [loginError, setLoginError] = useState(null);
  const abortRef = useRef(false);

  // Refresh queue every 5s (autres scanners peuvent alimenter en parallele via meme localStorage)
  useEffect(() => {
    const id = setInterval(() => setQueue(readQueue()), 5000);
    return () => clearInterval(id);
  }, []);

  const counts = useMemo(() => {
    const ok = results.filter((r) => r.status === 'ok').length;
    const skip = results.filter((r) => r.status === 'skip').length;
    const err = results.filter((r) => r.status === 'error').length;
    return { ok, skip, err, total: results.length };
  }, [results]);

  const handleLogin = async (e) => {
    e?.preventDefault();
    setLoginError(null);
    try {
      const r = await fetch(`${API_URL}/api/v1/staff/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId.trim(), pin: pin.trim() }),
      });
      if (!r.ok) {
        setLoginError('Agent ou PIN invalide');
        return;
      }
      const data = await r.json();
      const s = {
        token: data.access_token,
        agent_id: data.agent_id,
        nom: data.nom,
        role: data.role,
        permissions: data.permissions || [],
        loggedAt: new Date().toISOString(),
      };
      saveSession(s);
      setSession(s);
      setAgentId(''); setPin('');
    } catch {
      setLoginError('Connexion impossible');
    }
  };

  const handleLogout = () => {
    clearSession();
    setSession(null);
    setResults([]);
  };

  const replayQueue = async () => {
    if (!session?.token || replaying) return;
    abortRef.current = false;
    setReplaying(true);
    setResults([]);
    const current = readQueue();
    const remaining = [];

    for (const entry of current) {
      if (abortRef.current) { remaining.push(entry); continue; }
      // Si pas de badge_id : on ne peut pas appeler /scan/access (necessite un code resolvable badge).
      // On marque skip et on garde l'entrée dans la queue pour traitement manuel ulterieur.
      if (!entry.code && !entry.badge_id) {
        setResults((r) => [...r, { entry, status: 'skip', detail: 'pas de code badge — entree conservee' }]);
        remaining.push(entry);
        continue;
      }
      const code = entry.code || entry.badge_id || entry.frek_id;
      try {
        const r = await fetch(`${API_URL}/api/v1/staff/scan/access`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.token}`,
          },
          body: JSON.stringify({ code, zone, client_uuid: entry.client_uuid }),
        });
        if (r.ok) {
          const data = await r.json();
          setResults((rs) => [...rs, { entry, status: 'ok', detail: data?.idempotent ? 'deja enregistre' : 'OK' }]);
          // Succes : ne pas remettre dans la queue
        } else if (r.status === 401) {
          setResults((rs) => [...rs, { entry, status: 'error', detail: 'session expiree' }]);
          remaining.push(entry);
          abortRef.current = true; // stop le batch
        } else {
          const txt = await r.text().catch(() => '');
          setResults((rs) => [...rs, { entry, status: 'error', detail: `HTTP ${r.status} ${txt.slice(0,80)}` }]);
          remaining.push(entry);
        }
      } catch (err) {
        setResults((rs) => [...rs, { entry, status: 'error', detail: 'reseau' }]);
        remaining.push(entry);
      }
    }

    writeQueue(remaining);
    setQueue(remaining);
    setReplaying(false);
    if (abortRef.current) {
      handleLogout();
    }
  };

  const stopReplay = () => { abortRef.current = true; };

  // ===== UI =====
  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 relative overflow-hidden">
      <BackgroundDecor />

      <header className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 pt-6">
        <div className="bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/60 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/accueil" data-testid="poste-home-link" className="flex items-center gap-2">
            <span className="font-display text-xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">FREK</span>
          </Link>
          <div className="flex items-center gap-3">
            <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">Poste Staff</span>
            {session && (
              <button
                onClick={handleLogout}
                data-testid="poste-logout-btn"
                className="font-mono text-[10px] text-slate-500 hover:text-red-500 uppercase tracking-widest transition-colors"
              >
                Déconnexion
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {!session && (
          <section data-testid="poste-login-section" className="max-w-md mx-auto">
            <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Authentification staff</div>
            <h1 className="font-display text-3xl text-slate-800 mb-2">Poste staff</h1>
            <p className="font-mono text-sm text-slate-500 mb-8">
              Connectez-vous pour rejouer la file accumulée par les pointeuses sur le terrain.
            </p>

            <form onSubmit={handleLogin} className="space-y-4 bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-6 shadow-lg shadow-slate-200/40">
              <div>
                <label htmlFor="poste-agent" className="block font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Agent ID</label>
                <input
                  id="poste-agent"
                  data-testid="poste-agent-input"
                  type="text"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  placeholder="SUPERVISEUR-01"
                  autoComplete="username"
                  className="w-full bg-white border border-slate-200 focus:border-[#2cc4f5] focus:ring-2 focus:ring-[#2cc4f5]/20 outline-none rounded-xl px-4 py-3 font-mono text-sm text-slate-700 placeholder:text-slate-300 transition-all"
                />
              </div>
              <div>
                <label htmlFor="poste-pin" className="block font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">PIN</label>
                <input
                  id="poste-pin"
                  data-testid="poste-pin-input"
                  type="password"
                  value={pin}
                  onChange={(e) => setPin(e.target.value)}
                  inputMode="numeric"
                  placeholder="••••"
                  autoComplete="current-password"
                  className="w-full bg-white border border-slate-200 focus:border-[#2cc4f5] focus:ring-2 focus:ring-[#2cc4f5]/20 outline-none rounded-xl px-4 py-3 font-mono text-lg tracking-widest text-slate-700 placeholder:text-slate-300 transition-all"
                />
              </div>
              {loginError && (
                <div data-testid="poste-login-error" className="rounded-lg p-3 bg-red-50 border border-red-200 font-mono text-[11px] text-red-600">{loginError}</div>
              )}
              <button
                type="submit"
                disabled={!agentId.trim() || !pin.trim()}
                data-testid="poste-login-btn"
                className="w-full px-6 py-3 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] disabled:from-slate-300 disabled:to-slate-300 disabled:cursor-not-allowed text-white font-mono text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-[#2cc4f5]/30 hover:shadow-xl transition-all font-semibold"
              >
                Connexion
              </button>
            </form>
          </section>
        )}

        {session && (
          <section data-testid="poste-session-section">
            <div className="mb-8">
              <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Session active</div>
              <h1 className="font-display text-3xl text-slate-800" data-testid="poste-agent-name">{session.nom || session.agent_id}</h1>
              <div className="font-mono text-[11px] text-slate-500 mt-1">
                {session.role} · permissions : {session.permissions.join(', ') || '—'}
              </div>
            </div>

            {/* Sélecteur de zone */}
            <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-5 shadow-lg shadow-slate-200/40 mb-6">
              <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-3">Zone d'enregistrement (session entière)</div>
              <div className="flex flex-wrap gap-2">
                {ZONES.map((z) => (
                  <button
                    key={z}
                    onClick={() => setZone(z)}
                    data-testid={`poste-zone-${z}`}
                    className={`px-3 py-1.5 rounded-lg font-mono text-[10px] uppercase tracking-wider transition-all ${
                      zone === z
                        ? 'bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white shadow'
                        : 'bg-white border border-slate-200 text-slate-600 hover:border-[#2cc4f5]'
                    }`}
                  >
                    {z}
                  </button>
                ))}
              </div>
            </div>

            {/* File + actions */}
            <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-5 shadow-lg shadow-slate-200/40 mb-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">File locale</div>
                  <div data-testid="poste-queue-size" className="font-display text-3xl text-slate-800 tabular-nums">{queue.length}</div>
                </div>
                <div className="flex gap-2">
                  {!replaying && (
                    <button
                      onClick={replayQueue}
                      disabled={queue.length === 0}
                      data-testid="poste-replay-btn"
                      className="px-5 py-2.5 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] disabled:from-slate-300 disabled:to-slate-300 disabled:cursor-not-allowed text-white font-mono text-xs uppercase tracking-wider rounded-xl shadow hover:shadow-lg transition-all font-semibold"
                    >
                      Rejouer la file
                    </button>
                  )}
                  {replaying && (
                    <button
                      onClick={stopReplay}
                      data-testid="poste-stop-btn"
                      className="px-5 py-2.5 bg-red-500 hover:bg-red-600 text-white font-mono text-xs uppercase tracking-wider rounded-xl transition-colors font-semibold"
                    >
                      Arrêter
                    </button>
                  )}
                </div>
              </div>

              {/* Résultats */}
              {results.length > 0 && (
                <div data-testid="poste-results" className="space-y-1.5 max-h-80 overflow-y-auto">
                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2 text-center">
                      <div data-testid="poste-results-ok" className="font-display text-xl text-emerald-700 tabular-nums">{counts.ok}</div>
                      <div className="font-mono text-[9px] text-emerald-600 uppercase tracking-widest">OK</div>
                    </div>
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 text-center">
                      <div data-testid="poste-results-skip" className="font-display text-xl text-amber-700 tabular-nums">{counts.skip}</div>
                      <div className="font-mono text-[9px] text-amber-600 uppercase tracking-widest">Skip</div>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-2 text-center">
                      <div data-testid="poste-results-err" className="font-display text-xl text-red-600 tabular-nums">{counts.err}</div>
                      <div className="font-mono text-[9px] text-red-600 uppercase tracking-widest">Erreurs</div>
                    </div>
                  </div>
                  {results.slice(-50).reverse().map((r, i) => (
                    <div key={i} className={`flex items-center justify-between gap-3 rounded-md px-3 py-2 border ${
                      r.status === 'ok' ? 'bg-emerald-50/50 border-emerald-100' :
                      r.status === 'skip' ? 'bg-amber-50/50 border-amber-100' :
                      'bg-red-50/50 border-red-100'
                    }`}>
                      <span className="font-mono text-[11px] text-slate-700 truncate">{r.entry.code || r.entry.frek_id}</span>
                      <span className="font-mono text-[9px] text-slate-500 shrink-0 uppercase tracking-widest">{r.status} · {r.detail}</span>
                    </div>
                  ))}
                </div>
              )}

              {queue.length === 0 && results.length === 0 && (
                <p data-testid="poste-queue-empty" className="font-mono text-sm text-slate-400 italic text-center py-4">
                  La file est vide. Les pointeuses du terrain alimenteront cet écran.
                </p>
              )}
            </div>

            <p className="font-mono text-[11px] text-slate-400 max-w-xl">
              L'enregistrement est idempotent : chaque entrée porte un <code className="text-[#0ea5e9]">client_uuid</code>
              qui empêche tout double comptage côté serveur. Les présences sans badge_id résolvable sont conservées dans la file pour traitement manuel.
            </p>
          </section>
        )}
      </main>

      <footer className="relative z-10 border-t border-slate-200/70 mt-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-slate-400 uppercase tracking-widest">
          <span>Poste staff · session locale</span>
          <Link to="/scanner" className="hover:text-[#0ea5e9]">Pointeuse →</Link>
        </div>
      </footer>
    </div>
  );
}
