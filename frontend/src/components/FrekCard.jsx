/**
 * FrekCard — Carte virtuelle nominative et individuelle.
 *
 * Conçue pour vivre à vie avec le porteur :
 *  - Nominative (nom + prénom depuis badges/ publics, si CC2026)
 *  - Horodatée en continu (mise à jour temps réel)
 *  - Liée immuablement au FREK-ID
 *  - L'agent IA classe les traces : présences, œuvres, croisements (FREK-P/O/X)
 *  - Score d'impact culturel & stage Luciole affichés
 *
 * Design : verre teinté cyan-blanc, lisible sur fond clair Certify-style.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const ORIGIN = typeof window !== 'undefined' ? window.location.origin : '';

// Tiers visuels FREK Card — derives du Cultural Impact Score.
// Aucun score n'est code en dur cote backend (autoritaire dans frek_scoring_rules).
const TIERS = [
  { id: 'platinum', min: 500, label: 'Platine', accent: '#e2e8f0',
    gradient: 'linear-gradient(135deg, #475569 0%, #64748b 30%, #94a3b8 60%, #cbd5e1 100%)' },
  { id: 'gold',     min: 200, label: 'Or',     accent: '#fef3c7',
    gradient: 'linear-gradient(135deg, #b45309 0%, #d97706 30%, #f59e0b 60%, #fbbf24 100%)' },
  { id: 'silver',   min: 50,  label: 'Argent', accent: '#f1f5f9',
    gradient: 'linear-gradient(135deg, #475569 0%, #64748b 40%, #94a3b8 100%)' },
  { id: 'bronze',   min: 0,   label: 'Bronze', accent: '#fed7aa',
    gradient: 'linear-gradient(135deg, #7c2d12 0%, #9a3412 30%, #c2410c 60%, #ea580c 100%)' },
  { id: 'neuf',     min: -1,  label: 'Neuve',  accent: '#dbeafe',
    gradient: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 30%, #2cc4f5 60%, #4dd9ff 100%)' },
];

function tierFromScore(score) {
  if (score == null || score === undefined) return TIERS.find((t) => t.id === 'neuf');
  for (const t of TIERS) {
    if (t.id !== 'neuf' && score >= t.min) return t;
  }
  return TIERS.find((t) => t.id === 'bronze');
}

function relativeTime(iso) {
  if (!iso) return 'inactive';
  const then = new Date(iso).getTime();
  const diff = Date.now() - then;
  if (Number.isNaN(then)) return 'inactive';
  const m = Math.floor(diff / 60000);
  if (m < 1) return "à l'instant";
  if (m < 60) return `il y a ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `il y a ${h} h`;
  const d = Math.floor(h / 24);
  if (d < 30) return `il y a ${d} j`;
  return new Date(iso).toLocaleDateString('fr-FR');
}

function useLiveClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

function fmtClock(d) {
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
function fmtDate(d) {
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' });
}

export default function FrekCard({
  frekId,
  fullscreen = false,
  showQrAlways = false,
  data: dataOverride,
}) {
  // data: { prenom, nom, type_badge, type_name, status, current_stage,
  //         cultural_impact_score, event_count, traces: { presences, works, cross },
  //         last_event_at }
  const [data, setData] = useState(dataOverride || null);
  const [loading, setLoading] = useState(!dataOverride);
  const now = useLiveClock();
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (dataOverride) { return; }
    if (!frekId || fetchedRef.current) return;
    fetchedRef.current = true;

    const load = async () => {
      setLoading(true);
      const result = {
        prenom: null, nom: null, type_badge: null, type_name: null,
        status: null, current_stage: null,
        cultural_impact_score: null, event_count: null,
        traces: { presences: 0, works: 0, cross: 0 },
        last_event_at: null,
      };
      try {
        const [bRes, sRes, pRes] = await Promise.allSettled([
          fetch(`${API_URL}/api/badges/?event=CC2026&size=200`),
          fetch(`${API_URL}/api/v1/identity/${encodeURIComponent(frekId)}/status`),
          fetch(`${API_URL}/api/core/frek/${encodeURIComponent(frekId)}`),
        ]);
        if (bRes.status === 'fulfilled' && bRes.value.ok) {
          const j = await bRes.value.json();
          const match = (j.badges || []).find((b) => b.frek_id === frekId);
          if (match) {
            result.prenom = match.prenom || null;
            result.nom = match.nom || null;
            result.type_badge = match.type_badge || null;
            result.type_name = match.type_name || null;
          }
        }
        if (sRes.status === 'fulfilled' && sRes.value.ok) {
          const j = await sRes.value.json();
          result.current_stage = j.current_stage || null;
          result.status = j.revoked ? 'REVOQUE' : j.expired ? 'EXPIRE' : (j.active ? 'ACTIF' : 'PENDING');
        }
        if (pRes.status === 'fulfilled' && pRes.value.ok) {
          const j = await pRes.value.json();
          result.cultural_impact_score = j.cultural_impact_score ?? null;
          result.event_count = j.event_count ?? (j.events?.length ?? 0);
          // Derniere activite — max timestamp des events
          const events = j.events || [];
          if (events.length > 0) {
            let maxTs = null;
            for (const ev of events) {
              if (!maxTs || (ev.timestamp && ev.timestamp > maxTs)) maxTs = ev.timestamp;
            }
            result.last_event_at = maxTs;
          }
          // Classification IA-style FREK-P/O/W (cohérent avec Profil.jsx)
          const PRES = new Set(['ACTIVATION','SCAN','CHECKIN','PRESENCE','ACCESS']);
          const WORK = new Set(['EMISSION','CERTIFY','CERTIFICATION','CREATION','NOTARIZE']);
          for (const ev of (j.events || [])) {
            const a = (ev.action || '').toUpperCase();
            if (PRES.has(a)) result.traces.presences++;
            else if (WORK.has(a)) result.traces.works++;
            else result.traces.cross++;
          }
        }
      } catch { /* offline-friendly */ }
      setData(result);
      setLoading(false);
    };
    load();
  }, [frekId, dataOverride]);

  const displayName = useMemo(() => {
    if (data?.prenom || data?.nom) return `${data.prenom || ''} ${data.nom || ''}`.trim();
    return 'Porteur anonyme';
  }, [data]);

  const tier = tierFromScore(data?.cultural_impact_score);
  const isAlive = data?.last_event_at
    ? (now.getTime() - new Date(data.last_event_at).getTime()) < 24 * 3600 * 1000
    : false;

  const statusColor = data?.status === 'ACTIF' ? 'bg-emerald-400' : data?.status === 'REVOQUE' ? 'bg-red-400' : data?.status === 'EXPIRE' ? 'bg-amber-400' : 'bg-slate-300';

  return (
    <div
      data-testid={fullscreen ? 'frek-card-fullscreen' : 'frek-card'}
      data-tier={tier.id}
      className={`relative ${fullscreen ? 'w-full max-w-md mx-auto aspect-[1.586/1]' : 'w-full aspect-[1.586/1] max-w-lg'} rounded-3xl overflow-hidden shadow-2xl shadow-cyan-500/20`}
      style={{ background: tier.gradient }}
    >
      {/* Texture surcouches */}
      <div className="absolute inset-0 opacity-30" style={{
        backgroundImage:
          'radial-gradient(circle at 20% 20%, rgba(255,255,255,0.45) 0px, transparent 35%), radial-gradient(circle at 80% 80%, rgba(13,158,212,0.4) 0px, transparent 40%)',
      }} />
      <div className="absolute inset-0 opacity-40 mix-blend-overlay" style={{
        backgroundImage: 'linear-gradient(to bottom, rgba(255,255,255,0.3) 0%, transparent 50%)'
      }} />
      <div className="absolute inset-0 opacity-[0.07]" style={{
        backgroundImage:
          'linear-gradient(to right, white 1px, transparent 1px), linear-gradient(to bottom, white 1px, transparent 1px)',
        backgroundSize: '24px 24px',
      }} />

      {/* Contenu */}
      <div className="relative h-full p-5 sm:p-6 flex flex-col justify-between text-white">
        {/* Ligne haute */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            {/* Puce NFC virtuelle */}
            <div aria-hidden className="w-9 h-7 sm:w-10 sm:h-8 rounded-md border border-white/30 bg-gradient-to-br from-amber-100/80 via-amber-200/60 to-amber-100/40 backdrop-blur-sm shrink-0">
              <div className="h-full w-full grid grid-cols-3 grid-rows-2 gap-px p-1">
                {Array.from({ length: 6 }).map((_, i) => (
                  <span key={i} className="bg-amber-900/30 rounded-sm" />
                ))}
              </div>
            </div>
            <div>
              <div data-testid="frek-card-tier" className="font-mono text-[9px] sm:text-[10px] tracking-[0.3em] uppercase text-white/80">
                FREK · Card · <span className="font-semibold">{tier.label}</span>
              </div>
              <div className="font-display text-base sm:text-lg tracking-wider mt-0.5">FrekCore</div>
            </div>
          </div>
          <div className="text-right shrink-0">
            <div className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/15 backdrop-blur-sm border border-white/20">
              <span className={`h-1.5 w-1.5 rounded-full ${statusColor}`} />
              <span className="font-mono text-[9px] tracking-widest uppercase">
                {loading ? '...' : (data?.status || 'NEUF')}
              </span>
            </div>
            <div className="font-mono text-[9px] text-white/60 mt-1.5 tabular-nums">
              {fmtClock(now)}
            </div>
          </div>
        </div>

        {/* Centre — Nominatif */}
        <div className="flex-1 flex flex-col justify-center mt-3 sm:mt-4">
          <div data-testid="frek-card-name" className="font-display text-xl sm:text-2xl leading-tight break-words">
            {displayName}
          </div>
          {data?.type_name && (
            <div className="font-mono text-[10px] sm:text-[11px] text-white/70 mt-1 tracking-wider uppercase">
              {data.type_name}{data.type_badge ? ` · ${data.type_badge}` : ''}
            </div>
          )}
          {/* Card v2 — Impact score + derniere activite */}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span data-testid="frek-card-impact-score" className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-white/15 backdrop-blur-sm border border-white/20 font-mono text-[10px]">
              <span className="opacity-70">Impact</span>
              <span className="font-semibold tabular-nums">{data?.cultural_impact_score ?? 0}</span>
            </span>
            <span data-testid="frek-card-last-activity" className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full backdrop-blur-sm border font-mono text-[10px] ${isAlive ? 'bg-emerald-500/25 border-emerald-300/40' : 'bg-white/10 border-white/20'}`}>
              <span className={`h-1 w-1 rounded-full ${isAlive ? 'bg-emerald-300 animate-pulse' : 'bg-white/40'}`} />
              {relativeTime(data?.last_event_at)}
            </span>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center">
            <div className="rounded-lg bg-white/10 backdrop-blur-sm border border-white/15 p-1.5">
              <div className="font-display text-base sm:text-lg tabular-nums">{data?.traces.presences ?? 0}</div>
              <div className="font-mono text-[7.5px] uppercase tracking-widest text-white/60">FREK-P</div>
            </div>
            <div className="rounded-lg bg-white/10 backdrop-blur-sm border border-white/15 p-1.5">
              <div className="font-display text-base sm:text-lg tabular-nums">{data?.traces.works ?? 0}</div>
              <div className="font-mono text-[7.5px] uppercase tracking-widest text-white/60">FREK-O</div>
            </div>
            <div className="rounded-lg bg-white/10 backdrop-blur-sm border border-white/15 p-1.5">
              <div className="font-display text-base sm:text-lg tabular-nums">{data?.traces.cross ?? 0}</div>
              <div className="font-mono text-[7.5px] uppercase tracking-widest text-white/60">FREK-X</div>
            </div>
          </div>
        </div>

        {/* Ligne basse */}
        <div className="flex items-end justify-between gap-3 mt-2">
          <div className="min-w-0">
            <div className="font-mono text-[9px] text-white/60 uppercase tracking-widest">FREK-ID</div>
            <div data-testid="frek-card-frek-id" className="font-mono text-[10px] sm:text-xs tracking-wider break-all text-white/95">
              {frekId}
            </div>
            <div className="font-mono text-[9px] text-white/50 mt-1">
              {fmtDate(now)} · à vie · stage {data?.current_stage || '—'}
            </div>
          </div>
          {(fullscreen || showQrAlways) && (
            <div className="shrink-0 rounded-lg bg-white p-1.5">
              <QRCodeSVG
                value={`${ORIGIN}/verify/${frekId}`}
                size={fullscreen ? 80 : 60}
                level="M"
                bgColor="#ffffff"
                fgColor="#0ea5e9"
              />
            </div>
          )}
        </div>

        {/* Puce NFC virtuelle deja integree dans la ligne haute */}
      </div>
    </div>
  );
}
