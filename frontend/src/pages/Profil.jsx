/**
 * FREK — Profil personnel /profil/:frek_id (theme clair Certify)
 *
 * Compte neutre à la création — se remplit uniquement du vécu personnel.
 * L'agent IA classe en FREK-P (présences) / FREK-O (œuvres) / FREK-X (croisements).
 * La FREK Card virtuelle, nominative et liée à vie, est intégrée.
 *
 * Aucune donnée de la plateforme n'apparaît ici.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import FrekCard from '../components/FrekCard';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

const PRESENCE_ACTIONS = new Set(['ACTIVATION', 'SCAN', 'CHECKIN', 'PRESENCE', 'ACCESS']);
const WORK_ACTIONS = new Set(['EMISSION', 'CERTIFY', 'CERTIFICATION', 'CREATION', 'NOTARIZE']);

function classify(action) {
  const a = (action || '').toUpperCase();
  if (PRESENCE_ACTIONS.has(a)) return 'presence';
  if (WORK_ACTIONS.has(a)) return 'work';
  return 'cross';
}

function formatDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}

function BackgroundDecor() {
  return (
    <>
      <div aria-hidden className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl opacity-30" />
      <div aria-hidden className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl opacity-25" />
    </>
  );
}

function EmptySection({ label, message, testid }) {
  return (
    <div data-testid={testid} className="bg-white/60 backdrop-blur-xl border border-dashed border-[#2cc4f5]/30 rounded-xl p-6 sm:p-8 text-center shadow-sm">
      <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">{label}</div>
      <div className="font-mono text-sm text-slate-400 italic">{message}</div>
    </div>
  );
}

function Timeline({ items, kind, testid }) {
  if (!items?.length) return null;
  const colorMap = {
    presence: { dot: 'bg-[#0ea5e9]', text: 'text-[#0ea5e9]', label: 'FREK-P · Présence' },
    work:     { dot: 'bg-[#f59e0b]', text: 'text-[#d97706]', label: 'FREK-O · Œuvre' },
    cross:    { dot: 'bg-emerald-500', text: 'text-emerald-600', label: 'FREK-X · Croisement' },
  };
  const c = colorMap[kind];
  return (
    <div data-testid={testid} className="space-y-3">
      {items.map((ev, i) => (
        <div key={`${ev.timestamp}-${i}`} className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-lg p-4 flex items-start gap-4 shadow-sm">
          <span className={`mt-1.5 inline-block h-2 w-2 rounded-full ${c.dot} shrink-0`} />
          <div className="flex-1 min-w-0">
            <div className={`font-mono text-[10px] ${c.text} uppercase tracking-widest`}>{c.label}</div>
            <div className="font-mono text-sm text-slate-800 mt-1 break-words">
              {ev.action}{ev.badge_type ? ` · ${ev.badge_type}` : ''}
            </div>
            <div className="font-mono text-[11px] text-slate-400 mt-1">
              {formatDate(ev.timestamp)}{ev.event_id ? ` · contexte ${ev.event_id}` : ''}
            </div>
          </div>
          {typeof ev.score_delta === 'number' && (
            <div className="font-mono text-[10px] text-slate-400 shrink-0">+{ev.score_delta}</div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function Profil() {
  const { frekId } = useParams();
  const [profile, setProfile] = useState(null);
  const [status, setStatus] = useState(null);
  const [consent, setConsent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true); setError(null); setNotFound(false);
      try {
        const [pRes, sRes, cRes] = await Promise.allSettled([
          fetch(`${API_URL}/api/core/frek/${encodeURIComponent(frekId)}`),
          fetch(`${API_URL}/api/v1/identity/${encodeURIComponent(frekId)}/status`),
          fetch(`${API_URL}/api/core/fingerprint/consent/${encodeURIComponent(frekId)}`),
        ]);
        if (cancelled) return;

        const profileOk = pRes.status === 'fulfilled' && pRes.value.ok;
        const statusOk = sRes.status === 'fulfilled' && sRes.value.ok;

        if (!profileOk && !statusOk) setNotFound(true);
        else {
          if (profileOk) setProfile(await pRes.value.json());
          if (statusOk) setStatus(await sRes.value.json());
        }
        if (cRes.status === 'fulfilled' && cRes.value.ok) {
          setConsent(await cRes.value.json());
        }
      } catch {
        if (!cancelled) setError('Connexion impossible');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    if (frekId) load();
    return () => { cancelled = true; };
  }, [frekId]);

  const buckets = useMemo(() => {
    const events = profile?.events || [];
    const presence = [], work = [], cross = [];
    for (const ev of events) {
      const k = classify(ev.action);
      if (k === 'presence') presence.push(ev);
      else if (k === 'work') work.push(ev);
      else cross.push(ev);
    }
    return { presence, work, cross };
  }, [profile]);

  const hasFingerprintConsent = useMemo(() => {
    if (!consent?.layers) return false;
    return Object.values(consent.layers).some(Boolean);
  }, [consent]);

  const downloadPassport = async () => {
    try {
      const r = await fetch(`${API_URL}/api/v1/passport/${encodeURIComponent(frekId)}`);
      if (!r.ok) throw new Error('passport_unavailable');
      const data = await r.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `frek-passport-${frekId}.json`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch {
      setError('Passeport indisponible');
    }
  };

  if (!frekId) {
    return (
      <div className="min-h-screen bg-[#f8fafc] text-slate-700 flex items-center justify-center p-6">
        <div className="text-center font-mono text-sm">FREK-ID manquant. <Link to="/accueil" className="text-[#0ea5e9] underline">Retour</Link></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 relative overflow-hidden">
      <BackgroundDecor />

      <header className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 pt-6">
        <div className="bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/60 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/accueil" className="flex items-center gap-2 sm:gap-3" data-testid="profil-back-link">
            <span className="font-display text-xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">FREK</span>
          </Link>
          <span className="font-mono text-[10px] sm:text-xs text-slate-400 uppercase tracking-widest">Profil personnel</span>
        </div>
      </header>

      <main className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {loading && (
          <div className="text-center py-20" data-testid="profil-loading">
            <div className="w-10 h-10 mx-auto border-2 border-slate-200 border-t-[#2cc4f5] rounded-full animate-spin mb-4" />
            <p className="font-mono text-xs text-[#0ea5e9]">Chargement du profil...</p>
          </div>
        )}

        {!loading && notFound && (
          <div className="text-center py-20" data-testid="profil-not-found">
            <h1 className="font-display text-3xl text-slate-800 mb-3">Profil introuvable</h1>
            <p className="font-mono text-sm text-slate-400 mb-8">
              Ce FREK-ID n'existe pas encore — il sera créé à votre première trace.
            </p>
            <Link
              to="/accueil"
              className="inline-block px-5 py-3 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white font-mono text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-[#2cc4f5]/30 hover:shadow-xl transition-all font-semibold"
              data-testid="profil-not-found-cta"
            >
              Retour
            </Link>
          </div>
        )}

        {!loading && !notFound && (
          <>
            {/* FREK Card virtuelle nominative — lien vers /card en plein écran */}
            <section data-testid="profil-card-section" className="mb-10">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Votre FREK Card</div>
                  <h2 className="font-display text-2xl text-slate-800 mt-1">Nominative · à vie · vivante</h2>
                </div>
                <Link
                  to={`/card/${encodeURIComponent(frekId)}`}
                  data-testid="profil-open-card-fullscreen"
                  className="px-3 py-1.5 bg-white border border-slate-200 hover:border-[#2cc4f5] text-slate-600 font-mono text-[10px] uppercase tracking-wider rounded-lg transition-colors shadow-sm"
                >
                  Plein écran
                </Link>
              </div>
              <Link to={`/card/${encodeURIComponent(frekId)}`} className="block hover:scale-[1.01] transition-transform">
                <FrekCard frekId={frekId} />
              </Link>
            </section>

            <section data-testid="profil-header" className="mb-8 sm:mb-10">
              <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Identifiant souverain</div>
              <h1 className="font-display text-2xl sm:text-3xl text-slate-800 break-all" data-testid="profil-frek-id">{frekId}</h1>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                {status && !status.revoked && !status.expired && (
                  <span data-testid="profil-status-active" className="px-2.5 py-1 bg-[#2cc4f5]/10 text-[#0ea5e9] font-mono text-[10px] uppercase tracking-wider rounded-full border border-[#2cc4f5]/30">
                    Actif · Stage {status.current_stage}
                  </span>
                )}
                {status?.revoked && (
                  <span data-testid="profil-status-revoked" className="px-2.5 py-1 bg-red-50 text-red-600 font-mono text-[10px] uppercase tracking-wider rounded-full border border-red-200">Révoqué</span>
                )}
                {status?.expired && !status?.revoked && (
                  <span data-testid="profil-status-expired" className="px-2.5 py-1 bg-amber-50 text-amber-700 font-mono text-[10px] uppercase tracking-wider rounded-full border border-amber-200">Expiré</span>
                )}
                {hasFingerprintConsent && (
                  <span data-testid="profil-fingerprint-badge" className="px-2.5 py-1 bg-emerald-50 text-emerald-700 font-mono text-[10px] uppercase tracking-wider rounded-full border border-emerald-200">
                    Profil culturel certifié
                  </span>
                )}
              </div>

              <p className="font-mono text-[11px] text-slate-400 mt-4 max-w-xl leading-relaxed">
                Seules vos traces personnelles apparaissent ici. La masse de la plateforme
                reste sur la page <Link to="/accueil" className="text-[#0ea5e9] underline">d'accueil</Link>.
              </p>
            </section>

            {error && (
              <div className="mb-6 rounded-lg p-3 bg-red-50 border border-red-200 font-mono text-[11px] text-red-600" data-testid="profil-error">
                {error}
              </div>
            )}

            <section data-testid="profil-actions" className="mb-10 grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                onClick={downloadPassport}
                data-testid="profil-download-passport-btn"
                className="text-left bg-white/70 hover:bg-white border border-slate-200 hover:border-[#2cc4f5] rounded-xl p-4 transition-colors shadow-sm"
              >
                <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-1">Passeport souverain</div>
                <div className="font-mono text-sm text-slate-800">Télécharger passport.json</div>
                <div className="font-mono text-[10px] text-slate-400 mt-1">Signé Ed25519 · vérifiable offline</div>
              </button>

              <Link
                to={`/verify/${encodeURIComponent(frekId)}`}
                data-testid="profil-verify-link"
                className="block bg-white/70 hover:bg-white border border-slate-200 hover:border-[#2cc4f5] rounded-xl p-4 transition-colors shadow-sm"
              >
                <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-1">Vérification publique</div>
                <div className="font-mono text-sm text-slate-800">Ouvrir page /verify</div>
                <div className="font-mono text-[10px] text-slate-400 mt-1">Ancrage Bitcoin · audit lisible</div>
              </Link>
            </section>

            <section data-testid="profil-counters" className="mb-10 grid grid-cols-3 gap-3">
              <div className="bg-white/70 border border-white/60 rounded-xl p-4 shadow-sm">
                <div className="font-mono text-[9px] text-[#0ea5e9] uppercase tracking-widest">Présences</div>
                <div data-testid="profil-count-presences" className="font-display text-2xl sm:text-3xl text-slate-800 tabular-nums mt-1">{buckets.presence.length}</div>
              </div>
              <div className="bg-white/70 border border-white/60 rounded-xl p-4 shadow-sm">
                <div className="font-mono text-[9px] text-amber-600 uppercase tracking-widest">Œuvres</div>
                <div data-testid="profil-count-works" className="font-display text-2xl sm:text-3xl text-slate-800 tabular-nums mt-1">{buckets.work.length}</div>
              </div>
              <div className="bg-white/70 border border-white/60 rounded-xl p-4 shadow-sm">
                <div className="font-mono text-[9px] text-emerald-600 uppercase tracking-widest">Croisements</div>
                <div data-testid="profil-count-cross" className="font-display text-2xl sm:text-3xl text-slate-800 tabular-nums mt-1">{buckets.cross.length}</div>
              </div>
            </section>

            <section className="space-y-10">
              <div>
                <h2 className="font-display text-xl text-slate-800 mb-3">Présences</h2>
                {buckets.presence.length === 0 ? (
                  <EmptySection label="FREK-P" testid="profil-empty-presences" message="Aucune présence encore — scannez votre premier badge." />
                ) : (
                  <Timeline items={buckets.presence} kind="presence" testid="profil-timeline-presences" />
                )}
              </div>
              <div>
                <h2 className="font-display text-xl text-slate-800 mb-3">Œuvres certifiées</h2>
                {buckets.work.length === 0 ? (
                  <EmptySection label="FREK-O" testid="profil-empty-works" message="Aucune œuvre encore — certifiez votre première création." />
                ) : (
                  <Timeline items={buckets.work} kind="work" testid="profil-timeline-works" />
                )}
              </div>
              <div>
                <h2 className="font-display text-xl text-slate-800 mb-3">Croisements</h2>
                {buckets.cross.length === 0 ? (
                  <EmptySection label="FREK-X" testid="profil-empty-cross" message="Aucun événement encore." />
                ) : (
                  <Timeline items={buckets.cross} kind="cross" testid="profil-timeline-cross" />
                )}
              </div>
            </section>
          </>
        )}
      </main>

      <footer className="relative z-10 border-t border-slate-200/70 mt-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-slate-400 uppercase tracking-widest">
          <span>Compte personnel · données privées</span>
          <Link to="/privacy" className="hover:text-[#0ea5e9]">Confidentialité</Link>
        </div>
      </footer>
    </div>
  );
}
