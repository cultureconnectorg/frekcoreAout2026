/**
 * PulseBanner — Indicateur "plateforme vivante" embeddable.
 * Affiche le pulse temps-réel des présences CVLN sans révéler de PII.
 * Fond clair, compatible page Certify et page Accueil.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

export default function PulseBanner({ compact = false }) {
  const [pulse, setPulse] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const r = await fetch(`${API_URL}/api/core/ecosystem/pulse`);
        if (r.ok && !cancelled) setPulse(await r.json());
      } catch { /* offline ok */ }
    };
    load();
    const id = setInterval(load, 30_000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const isAlive = (pulse?.ecosystem_status || 'DORMANT') === 'ALIVE';
  const total = pulse?.total_events ?? 0;
  const subjects = pulse?.total_frek_ids ?? 0;

  return (
    <Link
      to="/accueil"
      data-testid="pulse-banner"
      className={`group inline-flex items-center gap-3 ${compact ? 'px-3 py-1.5' : 'px-4 py-2'} bg-white/70 backdrop-blur-md border border-white/60 rounded-full shadow-sm hover:shadow-md hover:border-[#2cc4f5]/50 transition-all`}
    >
      <span className="relative inline-flex h-2 w-2">
        <span className={`absolute inline-flex h-full w-full rounded-full ${isAlive ? 'bg-emerald-400' : 'bg-slate-300'} opacity-60 animate-ping`} />
        <span className={`relative inline-flex rounded-full h-2 w-2 ${isAlive ? 'bg-emerald-500' : 'bg-slate-400'}`} />
      </span>
      <span data-testid="pulse-banner-label" className="font-mono text-[10px] sm:text-[11px] uppercase tracking-widest text-slate-600">
        {isAlive ? 'Plateforme vivante' : 'Plateforme en sommeil'}
      </span>
      {pulse && (
        <span data-testid="pulse-banner-total" className="font-mono text-[10px] sm:text-[11px] text-[#0ea5e9] tabular-nums">
          {total.toLocaleString('fr-FR')} présences · {subjects.toLocaleString('fr-FR')} FREK-IDs
        </span>
      )}
      <span className="font-mono text-[10px] text-slate-400 group-hover:text-[#0ea5e9] transition-colors">→</span>
    </Link>
  );
}
