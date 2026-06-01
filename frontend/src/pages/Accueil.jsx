/**
 * FREK — Page d'accueil utilisateur (theme clair Certify)
 * Partie haute : vitrine plateforme (chiffres CVLN)
 * Partie basse : entrée compte personnel (FREK-ID)
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const CC2026_EVENT_ID = 'CC2026';

function useCountUp(target, duration = 1400) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!target || target <= 0) { setValue(0); return; }
    const start = performance.now();
    let raf;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(Math.floor(eased * target));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => raf && cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

function Pulse() {
  return (
    <span className="relative inline-flex h-2.5 w-2.5">
      <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60 animate-ping" />
      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
    </span>
  );
}

function BackgroundDecor() {
  return (
    <>
      <div aria-hidden className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl opacity-40" />
      <div aria-hidden className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl opacity-30" />
      <div aria-hidden className="absolute top-1/3 right-1/4 w-72 h-72 bg-[#2cc4f5]/10 rounded-full blur-2xl" />
      <div aria-hidden className="absolute inset-0 opacity-[0.04]" style={{
        backgroundImage: 'linear-gradient(to right, #2cc4f5 1px, transparent 1px), linear-gradient(to bottom, #2cc4f5 1px, transparent 1px)',
        backgroundSize: '40px 40px',
      }} />
    </>
  );
}

export default function Accueil() {
  const navigate = useNavigate();
  const [pulse, setPulse] = useState(null);
  const [eventStats, setEventStats] = useState(null);
  const [frekIdInput, setFrekIdInput] = useState('');
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [pRes, eRes] = await Promise.allSettled([
          fetch(`${API_URL}/api/core/ecosystem/pulse`),
          fetch(`${API_URL}/api/core/event/${CC2026_EVENT_ID}/stats`),
        ]);
        if (cancelled) return;
        if (pRes.status === 'fulfilled' && pRes.value.ok) setPulse(await pRes.value.json());
        if (eRes.status === 'fulfilled' && eRes.value.ok) setEventStats(await eRes.value.json());
      } catch {
        if (!cancelled) setLoadError('Plateforme injoignable');
      }
    };
    load();
    const id = setInterval(load, 30_000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const totalPresences = pulse?.total_events ?? 0;
  const totalFreks = pulse?.total_frek_ids ?? 0;
  const activeFreks = pulse?.active_frek_ids ?? 0;
  const eventCount = pulse?.top_event ? 1 : 0;
  const sourcesActive = pulse?.sources_active?.length ?? 0;

  const animatedPresences = useCountUp(totalPresences);
  const isAlive = (pulse?.ecosystem_status || 'DORMANT') === 'ALIVE';

  const handleEnter = (e) => {
    e?.preventDefault();
    const cleaned = frekIdInput.trim();
    if (!cleaned) return;
    navigate(`/profil/${encodeURIComponent(cleaned)}`);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 relative overflow-hidden">
      <BackgroundDecor />

      <header className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 pt-6">
        <div className="bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/60 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/" data-testid="accueil-logo-link" className="flex items-center gap-2 sm:gap-3">
            <span className="font-display text-xl sm:text-2xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">FREK</span>
          </Link>
          <Link
            to="/"
            data-testid="accueil-certifier-cta"
            className="px-3 sm:px-4 py-2 font-mono text-[10px] sm:text-xs uppercase tracking-wider text-[#0ea5e9] hover:text-white bg-[#2cc4f5]/5 hover:bg-gradient-to-r hover:from-[#2cc4f5] hover:to-[#0ea5e9] border border-[#2cc4f5]/20 hover:border-transparent rounded-xl transition-all"
          >
            Certifier
          </Link>
        </div>
      </header>

      <main className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 py-10 sm:py-16">
        {/* PLATEFORME */}
        <section data-testid="platform-section" className="mb-16 sm:mb-24">
          <div className="flex items-center gap-3 mb-6">
            <Pulse />
            <span
              data-testid="platform-status-label"
              className={`font-mono text-[10px] sm:text-xs uppercase tracking-widest ${isAlive ? 'text-emerald-600' : 'text-slate-400'}`}
            >
              {isAlive ? 'Plateforme active' : 'Plateforme en sommeil'}
            </span>
          </div>

          <h1 data-testid="platform-title" className="font-display text-4xl sm:text-5xl lg:text-6xl tracking-tight leading-[1.05] text-slate-900 mb-3">
            <span className="bg-gradient-to-r from-[#2cc4f5] via-[#06b6d4] to-[#0ea5e9] bg-clip-text text-transparent">FrekCore</span> est vivant.
          </h1>
          <p className="font-mono text-sm sm:text-base text-slate-500 max-w-2xl leading-relaxed">
            Infrastructure souveraine de certification culturelle. Les chiffres ci-dessous
            mesurent la masse de la plateforme — pas votre profil personnel.
          </p>

          <div className="mt-10 sm:mt-12 bg-white/80 backdrop-blur-xl rounded-2xl border border-white/70 shadow-xl shadow-slate-200/40 p-6 sm:p-10">
            <div className="font-mono text-[10px] sm:text-xs text-[#0ea5e9] uppercase tracking-widest mb-2">
              Total présences plateforme
            </div>
            <div
              data-testid="platform-total-presences"
              className="font-display text-6xl sm:text-7xl lg:text-8xl tabular-nums tracking-tight bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent"
            >
              {animatedPresences.toLocaleString('fr-FR')}
            </div>
            <div className="mt-2 font-mono text-[10px] sm:text-xs text-slate-400">
              {loadError ? loadError : 'Mise à jour automatique toutes les 30 secondes'}
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div data-testid="platform-stat-events" className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-5 shadow-md shadow-slate-200/30">
              <div className="font-mono text-[9px] sm:text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Événements couverts</div>
              <div className="font-display text-3xl sm:text-4xl text-slate-800 tabular-nums">{eventCount.toLocaleString('fr-FR')}</div>
              <div className="font-mono text-[10px] text-slate-400 mt-1">{pulse?.top_event ? `actif: ${pulse.top_event}` : '—'}</div>
            </div>
            <div data-testid="platform-stat-works" className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-5 shadow-md shadow-slate-200/30">
              <div className="font-mono text-[9px] sm:text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Œuvres &amp; identités certifiées</div>
              <div className="font-display text-3xl sm:text-4xl text-slate-800 tabular-nums">{totalFreks.toLocaleString('fr-FR')}</div>
              <div className="font-mono text-[10px] text-slate-400 mt-1">FREK-IDs émis depuis l'origine</div>
            </div>
            <div data-testid="platform-stat-active" className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-5 shadow-md shadow-slate-200/30">
              <div className="font-mono text-[9px] sm:text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Participants actifs</div>
              <div className="font-display text-3xl sm:text-4xl text-slate-800 tabular-nums">{activeFreks.toLocaleString('fr-FR')}</div>
              <div className="font-mono text-[10px] text-slate-400 mt-1">{sourcesActive} source{sourcesActive > 1 ? 's' : ''} active{sourcesActive > 1 ? 's' : ''} (24h)</div>
            </div>
          </div>

          {eventStats && eventStats.total_frek_ids > 0 && (
            <div data-testid="cc2026-mini" className="mt-6 bg-white/60 backdrop-blur-xl border border-white/60 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3 shadow-sm">
              <div>
                <div className="font-mono text-[9px] text-[#0ea5e9] uppercase tracking-widest">CC2026</div>
                <div className="font-mono text-sm text-slate-600">
                  {eventStats.total_frek_ids.toLocaleString('fr-FR')} FREK-IDs · {eventStats.active.toLocaleString('fr-FR')} actifs
                </div>
              </div>
              <div className="font-mono text-[10px] text-slate-400">
                {eventStats.first_activation ? `Première activation ${eventStats.first_activation.slice(0,10)}` : 'En attente d\'activation'}
              </div>
            </div>
          )}
        </section>

        {/* COMPTE PERSONNEL */}
        <section data-testid="personal-section" className="border-t border-slate-200/70 pt-12 sm:pt-16">
          <div className="max-w-2xl">
            <div className="font-mono text-[10px] sm:text-xs text-[#0ea5e9] uppercase tracking-widest mb-3">Votre compte FREK</div>
            <h2 className="font-display text-2xl sm:text-3xl text-slate-800 mb-4">Entrez dans votre profil.</h2>
            <p className="font-mono text-sm text-slate-500 leading-relaxed mb-8">
              Votre profil est vide et prêt. Il se construit à chaque présence,
              chaque œuvre, chaque moment. Les chiffres de la plateforme n'y entrent pas —
              seules vos traces personnelles.
            </p>

            <form onSubmit={handleEnter} className="space-y-4">
              <div>
                <label htmlFor="frek-id-input" className="block font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">
                  FREK-ID
                </label>
                <input
                  id="frek-id-input"
                  data-testid="accueil-frek-id-input"
                  type="text"
                  value={frekIdInput}
                  onChange={(e) => setFrekIdInput(e.target.value)}
                  placeholder="FREK-XXXXXXXX"
                  autoComplete="off"
                  spellCheck={false}
                  className="w-full bg-white/80 backdrop-blur-sm border border-slate-200 focus:border-[#2cc4f5] focus:ring-2 focus:ring-[#2cc4f5]/20 outline-none rounded-xl px-4 py-3 font-mono text-sm text-slate-700 placeholder:text-slate-300 transition-all shadow-sm"
                />
              </div>
              <button
                type="submit"
                disabled={!frekIdInput.trim()}
                data-testid="accueil-enter-profile-btn"
                className="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] disabled:from-slate-300 disabled:to-slate-300 disabled:cursor-not-allowed text-white font-mono text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-[#2cc4f5]/30 hover:shadow-xl hover:shadow-[#2cc4f5]/40 transition-all font-semibold"
              >
                Entrer dans mon profil
              </button>
            </form>

            <div className="mt-10 pt-8 border-t border-slate-200/70">
              <div className="font-mono text-[10px] text-slate-400 uppercase tracking-widest mb-3">Pas encore de FREK-ID&nbsp;?</div>
              <Link
                to="/"
                data-testid="accueil-create-profile-link"
                className="inline-block font-mono text-sm text-[#0ea5e9] hover:text-[#06b6d4] underline decoration-[#2cc4f5]/40 underline-offset-4 transition-colors"
              >
                Créer mon profil FREK →
              </Link>
              <p className="font-mono text-[11px] text-slate-400 mt-2 max-w-md">
                La création passe par la certification d'une première trace
                (audio, œuvre, présence). Aucune donnée plateforme n'est attachée
                à votre profil à l'arrivée.
              </p>
            </div>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t border-slate-200/70 mt-16">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-slate-400 uppercase tracking-widest">
          <span>FrekCore — Notaire culturel tech</span>
          <div className="flex gap-4">
            <Link to="/scanner" data-testid="accueil-link-scanner" className="hover:text-[#0ea5e9] transition-colors">Pointeuse</Link>
            <Link to="/poste" data-testid="accueil-link-poste" className="hover:text-[#0ea5e9] transition-colors">Poste staff</Link>
            <Link to="/spec" className="hover:text-[#0ea5e9] transition-colors">Spec</Link>
            <Link to="/privacy" className="hover:text-[#0ea5e9] transition-colors">Confidentialité</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
