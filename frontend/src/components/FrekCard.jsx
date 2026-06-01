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
  //         cultural_impact_score, event_count, traces: { presences, works, cross } }
  const [data, setData] = useState(dataOverride || null);
  const [loading, setLoading] = useState(!dataOverride);
  const now = useLiveClock();
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (dataOverride) { setData(dataOverride); setLoading(false); return; }
    if (!frekId || fetchedRef.current) return;
    fetchedRef.current = true;

    const load = async () => {
      setLoading(true);
      const result = {
        prenom: null, nom: null, type_badge: null, type_name: null,
        status: null, current_stage: null,
        cultural_impact_score: null, event_count: null,
        traces: { presences: 0, works: 0, cross: 0 },
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

  const verifyUrl = `${typeof window !== 'undefined' ? window.location.origin : ''}/verify/${frekId}`;
  const statusColor = data?.status === 'ACTIF' ? 'bg-emerald-400' : data?.status === 'REVOQUE' ? 'bg-red-400' : data?.status === 'EXPIRE' ? 'bg-amber-400' : 'bg-slate-300';

  return (
    <div
      data-testid={fullscreen ? 'frek-card-fullscreen' : 'frek-card'}
      className={`relative ${fullscreen ? 'w-full max-w-md mx-auto aspect-[1.586/1]' : 'w-full aspect-[1.586/1] max-w-lg'} rounded-3xl overflow-hidden shadow-2xl shadow-cyan-500/20`}
      style={{
        background:
          'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 30%, #2cc4f5 60%, #4dd9ff 100%)',
      }}
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
        <div className="flex items-start justify-between">
          <div>
            <div className="font-mono text-[9px] sm:text-[10px] tracking-[0.3em] uppercase text-white/70">FREK · Card</div>
            <div className="font-display text-base sm:text-lg tracking-wider mt-0.5">FrekCore</div>
          </div>
          <div className="text-right">
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
        <div className="flex-1 flex flex-col justify-center mt-2 sm:mt-3">
          <div data-testid="frek-card-name" className="font-display text-xl sm:text-2xl leading-tight break-words">
            {displayName}
          </div>
          {data?.type_name && (
            <div className="font-mono text-[10px] sm:text-[11px] text-white/70 mt-1 tracking-wider uppercase">
              {data.type_name}{data.type_badge ? ` · ${data.type_badge}` : ''}
            </div>
          )}
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
                value={verifyUrl}
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
