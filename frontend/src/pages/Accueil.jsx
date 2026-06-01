/**
 * FREK — Page d'accueil utilisateur
 * Partie haute : vitrine plateforme (chiffres CVLN)
 * Partie basse : entrée compte personnel (FREK-ID)
 *
 * Règle absolue : les chiffres plateforme et le profil personnel
 * ne se mélangent jamais.
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const CC2026_EVENT_ID = 'CC2026';

function useCountUp(target, duration = 1400) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!target || target <= 0) {
      setValue(0);
      return;
    }
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
      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
    </span>
  );
}

export default function Accueil() {
  const navigate = useNavigate();
  const [pulse, setPulse] = useState(null);
  const [eventStats, setEventStats] = useState(null);
  const [frekIdInput, setFrekIdInput] = useState('');
  const [loadError, setLoadError] = useState(null);

  // Plateforme : pulse + stats CC2026 (chiffres CVLN — jamais mêlés au profil)
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [pRes, eRes] = await Promise.allSettled([
          fetch(`${API_URL}/api/core/ecosystem/pulse`),
          fetch(`${API_URL}/api/core/event/${CC2026_EVENT_ID}/stats`),
        ]);
        if (cancelled) return;
        if (pRes.status === 'fulfilled' && pRes.value.ok) {
          setPulse(await pRes.value.json());
        }
        if (eRes.status === 'fulfilled' && eRes.value.ok) {
          setEventStats(await eRes.value.json());
        }
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
  const eventCount = pulse?.top_event ? 1 : 0; // au minimum 1 event si pulse a un top_event
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
    <div className="min-h-screen bg-gradient-to-b from-[#050a0d] via-[#0a1520] to-[#050a0d] text-white">
      {/* Header minimal — pas de Nav existante pour éviter toute modification */}
      <header className="bg-[#050a0d]/95 backdrop-blur-xl border-b border-[#2cc4f5]/10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 sm:gap-3" data-testid="accueil-logo-link">
            <img src="/frek-logo.png" alt="FREK" className="h-6 sm:h-8 w-auto" />
            <span className="font-display text-lg sm:text-xl tracking-wider text-[#2cc4f5]">FREK</span>
          </Link>
          <Link
            to="/"
            data-testid="accueil-certifier-cta"
            className="px-3 sm:px-4 py-1.5 sm:py-2 bg-[#2cc4f5] text-[#050a0d] font-mono text-[10px] sm:text-xs uppercase tracking-wider rounded hover:bg-[#33cfff] transition-all font-bold"
          >
            Certifier
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-10 sm:py-16">
        {/* ======================= PARTIE HAUTE — PLATEFORME (CVLN) ======================= */}
        <section data-testid="platform-section" className="mb-16 sm:mb-24">
          <div className="flex items-center gap-3 mb-6">
            <Pulse />
            <span
              data-testid="platform-status-label"
              className={`font-mono text-[10px] sm:text-xs uppercase tracking-widest ${isAlive ? 'text-emerald-400' : 'text-white/40'}`}
            >
              {isAlive ? 'Plateforme active' : 'Plateforme en sommeil'}
            </span>
          </div>

          <h1
            data-testid="platform-title"
            className="font-display text-4xl sm:text-5xl lg:text-6xl tracking-tight leading-[1.05] text-white mb-3"
          >
            FrekCore est vivant.
          </h1>
          <p className="font-mono text-sm sm:text-base text-white/50 max-w-2xl leading-relaxed">
            Infrastructure souveraine de certification culturelle. Les chiffres ci-dessous
            mesurent la masse de la plateforme — pas votre profil personnel.
          </p>

          {/* Compteur principal — présences plateforme */}
          <div className="mt-10 sm:mt-12 bg-gradient-to-br from-[#0a1520]/70 to-[#050a0d]/70 rounded-2xl border border-[#2cc4f5]/15 p-6 sm:p-10">
            <div className="font-mono text-[10px] sm:text-xs text-[#2cc4f5]/60 uppercase tracking-widest mb-2">
              Total présences plateforme
            </div>
            <div
              data-testid="platform-total-presences"
              className="font-display text-6xl sm:text-7xl lg:text-8xl text-[#2cc4f5] tabular-nums tracking-tight"
            >
              {animatedPresences.toLocaleString('fr-FR')}
            </div>
            <div className="mt-2 font-mono text-[10px] sm:text-xs text-white/40">
              {loadError ? loadError : 'Mise à jour automatique toutes les 30 secondes'}
            </div>
          </div>

          {/* 3 chiffres clés — événements / œuvres / participants */}
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div data-testid="platform-stat-events" className="bg-[#0a1520]/50 border border-[#2cc4f5]/10 rounded-xl p-5">
              <div className="font-mono text-[9px] sm:text-[10px] text-[#2cc4f5]/50 uppercase tracking-widest mb-2">
                Événements couverts
              </div>
              <div className="font-display text-3xl sm:text-4xl text-white tabular-nums">
                {eventCount.toLocaleString('fr-FR')}
              </div>
              <div className="font-mono text-[10px] text-white/40 mt-1">
                {pulse?.top_event ? `actif: ${pulse.top_event}` : '—'}
              </div>
            </div>

            <div data-testid="platform-stat-works" className="bg-[#0a1520]/50 border border-[#2cc4f5]/10 rounded-xl p-5">
              <div className="font-mono text-[9px] sm:text-[10px] text-[#2cc4f5]/50 uppercase tracking-widest mb-2">
                Œuvres &amp; identités certifiées
              </div>
              <div className="font-display text-3xl sm:text-4xl text-white tabular-nums">
                {totalFreks.toLocaleString('fr-FR')}
              </div>
              <div className="font-mono text-[10px] text-white/40 mt-1">
                FREK-IDs émis depuis l'origine
              </div>
            </div>

            <div data-testid="platform-stat-active" className="bg-[#0a1520]/50 border border-[#2cc4f5]/10 rounded-xl p-5">
              <div className="font-mono text-[9px] sm:text-[10px] text-[#2cc4f5]/50 uppercase tracking-widest mb-2">
                Participants actifs
              </div>
              <div className="font-display text-3xl sm:text-4xl text-white tabular-nums">
                {activeFreks.toLocaleString('fr-FR')}
              </div>
              <div className="font-mono text-[10px] text-white/40 mt-1">
                {sourcesActive} source{sourcesActive > 1 ? 's' : ''} active{sourcesActive > 1 ? 's' : ''} (24h)
              </div>
            </div>
          </div>

          {/* Indicateur CC2026 (si event_stats disponible) */}
          {eventStats && eventStats.total_frek_ids > 0 && (
            <div data-testid="cc2026-mini" className="mt-6 bg-[#0a1520]/40 border border-[#2cc4f5]/10 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="font-mono text-[9px] text-[#2cc4f5]/60 uppercase tracking-widest">CC2026</div>
                <div className="font-mono text-sm text-white/70">
                  {eventStats.total_frek_ids.toLocaleString('fr-FR')} FREK-IDs · {eventStats.active.toLocaleString('fr-FR')} actifs
                </div>
              </div>
              <div className="font-mono text-[10px] text-white/40">
                {eventStats.first_activation ? `Première activation ${eventStats.first_activation.slice(0,10)}` : 'En attente d\'activation'}
              </div>
            </div>
          )}
        </section>

        {/* ======================= PARTIE BASSE — COMPTE PERSONNEL ======================= */}
        <section data-testid="personal-section" className="border-t border-[#2cc4f5]/10 pt-12 sm:pt-16">
          <div className="max-w-2xl">
            <div className="font-mono text-[10px] sm:text-xs text-[#2cc4f5]/60 uppercase tracking-widest mb-3">
              Votre compte FREK
            </div>
            <h2 className="font-display text-2xl sm:text-3xl text-white mb-4">
              Entrez dans votre profil.
            </h2>
            <p className="font-mono text-sm text-white/50 leading-relaxed mb-8">
              Votre profil est vide et prêt. Il se construit à chaque présence,
              chaque œuvre, chaque moment. Les chiffres de la plateforme n'y entrent pas —
              seules vos traces personnelles.
            </p>

            <form onSubmit={handleEnter} className="space-y-4">
              <div>
                <label htmlFor="frek-id-input" className="block font-mono text-[10px] text-[#2cc4f5]/50 uppercase tracking-widest mb-2">
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
                  className="w-full bg-[#0a1520]/60 border border-[#2cc4f5]/20 focus:border-[#2cc4f5] outline-none rounded-lg px-4 py-3 font-mono text-sm text-[#2cc4f5] placeholder:text-white/20 transition-colors"
                />
              </div>
              <button
                type="submit"
                disabled={!frekIdInput.trim()}
                data-testid="accueil-enter-profile-btn"
                className="w-full sm:w-auto px-6 py-3 bg-[#2cc4f5] disabled:bg-[#2cc4f5]/30 disabled:cursor-not-allowed text-[#050a0d] font-mono text-xs uppercase tracking-wider rounded hover:bg-[#33cfff] transition-all font-bold"
              >
                Entrer dans mon profil
              </button>
            </form>

            <div className="mt-10 pt-8 border-t border-white/5">
              <div className="font-mono text-[10px] text-white/40 uppercase tracking-widest mb-3">
                Pas encore de FREK-ID&nbsp;?
              </div>
              <Link
                to="/"
                data-testid="accueil-create-profile-link"
                className="inline-block font-mono text-sm text-[#2cc4f5] hover:text-[#33cfff] underline decoration-[#2cc4f5]/30 underline-offset-4 transition-colors"
              >
                Créer mon profil FREK →
              </Link>
              <p className="font-mono text-[11px] text-white/30 mt-2 max-w-md">
                La création passe par la certification d'une première trace
                (audio, œuvre, présence). Aucune donnée plateforme n'est attachée
                à votre profil à l'arrivée.
              </p>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-[#2cc4f5]/10 mt-16">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-white/30 uppercase tracking-widest">
          <span>FrekCore — Notaire culturel tech</span>
          <div className="flex gap-4">
            <Link to="/scanner" data-testid="accueil-link-scanner" className="hover:text-[#2cc4f5] transition-colors">Pointeuse</Link>
            <Link to="/spec" className="hover:text-[#2cc4f5] transition-colors">Spec</Link>
            <Link to="/privacy" className="hover:text-[#2cc4f5] transition-colors">Confidentialité</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
