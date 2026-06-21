/**
 * FREK — Page Admin PDF Batch /admin/pdf
 *
 * Self-service : staff connecte (PIN existant) peut lister les evenements et
 * declencher la generation d'un ZIP de PDFs pour batch impression.
 *
 * Operationnel pour annees futures sans intervention developpeur.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const SESSION_KEY = 'frek_poste_session';

function loadSession() {
  try { const r = sessionStorage.getItem(SESSION_KEY); return r ? JSON.parse(r) : null; } catch { return null; }
}
function saveSession(s) { try { sessionStorage.setItem(SESSION_KEY, JSON.stringify(s)); } catch { /* noop */ } }

function BackgroundDecor() {
  return (
    <>
      <div aria-hidden className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl opacity-30" />
      <div aria-hidden className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl opacity-25" />
    </>
  );
}

export default function AdminPdf() {
  const [session, setSession] = useState(() => loadSession());
  const [agentId, setAgentId] = useState('');
  const [pin, setPin] = useState('');
  const [loginError, setLoginError] = useState(null);

  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [limit, setLimit] = useState(100);
  const [template, setTemplate] = useState({
    title: 'FrekCore',
    subtitle: "Carte d'accès certifiée",
    footer: 'Notaire culturel tech · cvln.com',
    accent_hex: '#0EA5E9',
  });
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState(null);

  const isAdmin = session?.permissions?.includes('view_stats');

  // Charge la liste des evenements quand on est admin loggué
  useEffect(() => {
    if (!isAdmin) return;
    let cancelled = false;
    const load = async () => {
      try {
        const r = await fetch(`${API_URL}/api/v1/pdf-batch/events-with-counts`, {
          headers: { 'Authorization': `Bearer ${session.token}` },
        });
        if (!r.ok) return;
        const data = await r.json();
        if (!cancelled) setEvents(data.events || []);
      } catch { /* noop */ }
    };
    load();
    return () => { cancelled = true; };
  }, [isAdmin, session]);

  const handleLogin = async (e) => {
    e?.preventDefault();
    setLoginError(null);
    try {
      const r = await fetch(`${API_URL}/api/v1/staff/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId.trim(), pin: pin.trim() }),
      });
      if (!r.ok) { setLoginError('Agent ou PIN invalide'); return; }
      const data = await r.json();
      const s = { token: data.access_token, agent_id: data.agent_id, nom: data.nom, role: data.role, permissions: data.permissions || [] };
      saveSession(s); setSession(s); setAgentId(''); setPin('');
      if (!s.permissions.includes('admin')) setLoginError('Permission admin requise pour ce poste.');
    } catch { setLoginError('Connexion impossible'); }
  };

  const handleGenerate = async () => {
    if (!selectedEvent || busy) return;
    setBusy(true); setError(null); setFeedback(null);
    try {
      const r = await fetch(`${API_URL}/api/v1/pdf-batch/by-event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${session.token}` },
        body: JSON.stringify({
          event: selectedEvent,
          type_badge: typeFilter || undefined,
          limit,
          template,
        }),
      });
      if (!r.ok) {
        const txt = await r.text().catch(() => '');
        throw new Error(`HTTP ${r.status} ${txt.slice(0,120)}`);
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `frek-badges-${selectedEvent}.zip`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
      setFeedback(`ZIP téléchargé · ${selectedEvent} · ${typeFilter || 'tous types'}`);
    } catch (e) {
      setError(String(e.message || e));
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 relative overflow-hidden">
      <BackgroundDecor />

      <header className="relative z-10 max-w-3xl mx-auto px-4 sm:px-6 pt-6">
        <div className="bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/60 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/accueil" data-testid="adminpdf-home-link" className="flex items-center gap-2">
            <span className="font-display text-xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">FREK</span>
          </Link>
          <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">Admin · PDF batch</span>
        </div>
      </header>

      <main className="relative z-10 max-w-3xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
        {!session && (
          <section data-testid="adminpdf-login-section" className="max-w-md mx-auto">
            <h1 className="font-display text-3xl text-slate-800 mb-2">Admin · PDF batch</h1>
            <p className="font-mono text-sm text-slate-500 mb-6">Authentification admin requise.</p>
            <form onSubmit={handleLogin} className="space-y-4 bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-6 shadow-lg">
              <input data-testid="adminpdf-agent-input" type="text" value={agentId} onChange={(e) => setAgentId(e.target.value)} placeholder="Agent ID" className="w-full bg-white border border-slate-200 focus:border-[#2cc4f5] outline-none rounded-xl px-4 py-3 font-mono text-sm" />
              <input data-testid="adminpdf-pin-input" type="password" value={pin} onChange={(e) => setPin(e.target.value)} placeholder="PIN" className="w-full bg-white border border-slate-200 focus:border-[#2cc4f5] outline-none rounded-xl px-4 py-3 font-mono text-sm" />
              {loginError && <div data-testid="adminpdf-login-error" className="rounded-lg p-3 bg-red-50 border border-red-200 font-mono text-[11px] text-red-600">{loginError}</div>}
              <button type="submit" data-testid="adminpdf-login-btn" className="w-full px-6 py-3 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white font-mono text-xs uppercase tracking-wider rounded-xl shadow-lg font-semibold">Connexion</button>
            </form>
          </section>
        )}

        {session && !isAdmin && (
          <section data-testid="adminpdf-not-admin" className="text-center py-20">
            <h1 className="font-display text-2xl text-slate-800 mb-2">Permission admin requise</h1>
            <p className="font-mono text-sm text-slate-500">Votre compte staff n'a pas la permission "admin".</p>
          </section>
        )}

        {session && isAdmin && (
          <section data-testid="adminpdf-section">
            <h1 className="font-display text-3xl text-slate-800 mb-2">Génération PDF</h1>
            <p className="font-mono text-sm text-slate-500 mb-8">Self-service. Réutilisable chaque année.</p>

            {/* Evenements disponibles */}
            <div className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-5 shadow-lg mb-6">
              <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-3">Événements disponibles</div>
              {events.length === 0 ? (
                <p className="font-mono text-sm text-slate-400 italic">Chargement ou aucun événement.</p>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {events.map((e) => (
                    <button
                      key={e.event}
                      onClick={() => setSelectedEvent(e.event)}
                      data-testid={`adminpdf-event-${e.event}`}
                      className={`text-left px-3 py-2 rounded-lg border transition ${selectedEvent === e.event ? 'bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white border-transparent' : 'bg-white border-slate-200 hover:border-[#2cc4f5]'}`}
                    >
                      <div className="font-mono text-sm">{e.event}</div>
                      <div className={`font-mono text-[10px] ${selectedEvent === e.event ? 'text-white/70' : 'text-slate-400'}`}>{e.count} badges</div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Filtres */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-5 shadow-md mb-6">
              <div>
                <label className="block font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Type badge (optionnel)</label>
                <input
                  type="text"
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value.toUpperCase())}
                  placeholder="ex: BNV, ART, VIP"
                  data-testid="adminpdf-type-filter"
                  className="w-full bg-white border border-slate-200 focus:border-[#2cc4f5] outline-none rounded-xl px-3 py-2 font-mono text-sm uppercase"
                />
              </div>
              <div>
                <label className="block font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Limite (max 1000)</label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={limit}
                  onChange={(e) => setLimit(Math.min(1000, Math.max(1, parseInt(e.target.value, 10) || 1)))}
                  data-testid="adminpdf-limit"
                  className="w-full bg-white border border-slate-200 focus:border-[#2cc4f5] outline-none rounded-xl px-3 py-2 font-mono text-sm"
                />
              </div>
            </div>

            {/* Template */}
            <details className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-5 shadow-md mb-6">
              <summary className="cursor-pointer font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Personnaliser le template</summary>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                {['title', 'subtitle', 'footer'].map((k) => (
                  <input key={k} type="text" value={template[k] || ''} onChange={(e) => setTemplate({ ...template, [k]: e.target.value })} placeholder={k} data-testid={`adminpdf-tpl-${k}`} className="w-full bg-white border border-slate-200 focus:border-[#2cc4f5] outline-none rounded-xl px-3 py-2 font-mono text-sm" />
                ))}
                <input type="text" value={template.accent_hex} onChange={(e) => setTemplate({ ...template, accent_hex: e.target.value })} placeholder="#0EA5E9" data-testid="adminpdf-tpl-accent" className="w-full bg-white border border-slate-200 focus:border-[#2cc4f5] outline-none rounded-xl px-3 py-2 font-mono text-sm" />
              </div>
            </details>

            {error && <div data-testid="adminpdf-error" className="rounded-lg p-3 bg-red-50 border border-red-200 font-mono text-[11px] text-red-600 mb-4">{error}</div>}
            {feedback && <div data-testid="adminpdf-feedback" className="rounded-lg p-3 bg-emerald-50 border border-emerald-200 font-mono text-[11px] text-emerald-700 mb-4">{feedback}</div>}

            <button
              onClick={handleGenerate}
              disabled={!selectedEvent || busy}
              data-testid="adminpdf-generate-btn"
              className="w-full px-6 py-3 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] disabled:from-slate-300 disabled:to-slate-300 disabled:cursor-not-allowed text-white font-mono text-xs uppercase tracking-wider rounded-xl shadow-lg font-semibold transition-all"
            >
              {busy ? 'Génération en cours…' : `Générer ZIP · ${selectedEvent || '(choisir un event)'}`}
            </button>

            <p className="font-mono text-[11px] text-slate-400 mt-4 max-w-xl">
              Format A6 portrait (105×148mm). 1 PDF par badge dans le ZIP.
              QR code intégré pointe vers <code className="text-[#0ea5e9]">/verify/{`{frek_id}`}</code>.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
