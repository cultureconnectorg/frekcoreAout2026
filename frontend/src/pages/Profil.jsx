/**
 * FREK — Profil personnel /profil/:frek_id
 *
 * Compte neutre à la création — se remplit uniquement du vécu personnel.
 * Aucun chiffre de la plateforme (CC2026, 40k, masse) n'est affiché ici.
 *
 * Endpoints consommés (lecture seule, publics) :
 *   - GET /api/core/frek/{frek_id}              (subject + 100 derniers events)
 *   - GET /api/v1/identity/{frek_id}/status     (statut public, optionnel)
 *   - GET /api/v1/passport/{frek_id}            (passeport souverain Ed25519)
 *   - GET /api/core/fingerprint/consent/{frek_id} (badge "certifié" si consent accordé)
 */
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

// Actions classifiables FREK-P (présence), FREK-O (œuvre), FREK-X (croisement)
const PRESENCE_ACTIONS = new Set(['ACTIVATION', 'SCAN', 'CHECKIN', 'PRESENCE', 'ACCESS']);
const WORK_ACTIONS = new Set(['EMISSION', 'CERTIFY', 'CERTIFICATION', 'CREATION', 'NOTARIZE']);
// Tout autre action = croisement / interaction

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

function EmptySection({ label, message, testid }) {
  return (
    <div data-testid={testid} className="bg-[#0a1520]/30 border border-dashed border-[#2cc4f5]/15 rounded-xl p-6 sm:p-8 text-center">
      <div className="font-mono text-[10px] text-[#2cc4f5]/40 uppercase tracking-widest mb-2">{label}</div>
      <div className="font-mono text-sm text-white/40 italic">{message}</div>
    </div>
  );
}

function Timeline({ items, kind, testid }) {
  if (!items?.length) return null;
  const colorMap = {
    presence: { dot: 'bg-[#2cc4f5]', text: 'text-[#2cc4f5]', label: 'FREK-P · Présence' },
    work:     { dot: 'bg-[#f7931a]', text: 'text-[#f7931a]', label: 'FREK-O · Œuvre' },
    cross:    { dot: 'bg-emerald-400', text: 'text-emerald-400', label: 'FREK-X · Croisement' },
  };
  const c = colorMap[kind];
  return (
    <div data-testid={testid} className="space-y-3">
      {items.map((ev, i) => (
        <div key={`${ev.timestamp}-${i}`} className="bg-[#0a1520]/50 border border-[#2cc4f5]/10 rounded-lg p-4 flex items-start gap-4">
          <span className={`mt-1.5 inline-block h-2 w-2 rounded-full ${c.dot} shrink-0`} />
          <div className="flex-1 min-w-0">
            <div className={`font-mono text-[10px] ${c.text} uppercase tracking-widest`}>{c.label}</div>
            <div className="font-mono text-sm text-white mt-1 break-words">
              {ev.action}{ev.badge_type ? ` · ${ev.badge_type}` : ''}
            </div>
            <div className="font-mono text-[11px] text-white/40 mt-1">
              {formatDate(ev.timestamp)}
              {ev.event_id ? ` · contexte ${ev.event_id}` : ''}
            </div>
          </div>
          {typeof ev.score_delta === 'number' && (
            <div className="font-mono text-[10px] text-white/30 shrink-0">+{ev.score_delta}</div>
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
      setLoading(true);
      setError(null);
      setNotFound(false);
      try {
        const [pRes, sRes, cRes] = await Promise.allSettled([
          fetch(`${API_URL}/api/core/frek/${encodeURIComponent(frekId)}`),
          fetch(`${API_URL}/api/v1/identity/${encodeURIComponent(frekId)}/status`),
          fetch(`${API_URL}/api/core/fingerprint/consent/${encodeURIComponent(frekId)}`),
        ]);
        if (cancelled) return;

        const profileOk = pRes.status === 'fulfilled' && pRes.value.ok;
        const statusOk = sRes.status === 'fulfilled' && sRes.value.ok;

        if (!profileOk && !statusOk) {
          setNotFound(true);
        } else {
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

  // Sépare les events en 3 timelines : FREK-P, FREK-O, FREK-X
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

  // Badge "Profil culturel certifié" : si au moins une couche fingerprint est consentie
  const hasFingerprintConsent = useMemo(() => {
    if (!consent?.layers) return false;
    return Object.values(consent.layers).some(Boolean);
  }, [consent]);

  // Téléchargement passeport souverain
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
      <div className="min-h-screen bg-[#050a0d] text-white flex items-center justify-center p-6">
        <div className="text-center font-mono text-sm text-white/60">FREK-ID manquant. <Link to="/accueil" className="text-[#2cc4f5] underline">Retour</Link></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#050a0d] via-[#0a1520] to-[#050a0d] text-white">
      <header className="bg-[#050a0d]/95 backdrop-blur-xl border-b border-[#2cc4f5]/10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/accueil" className="flex items-center gap-2 sm:gap-3" data-testid="profil-back-link">
            <img src="/frek-logo.png" alt="FREK" className="h-6 sm:h-8 w-auto" />
            <span className="font-display text-lg sm:text-xl tracking-wider text-[#2cc4f5]">FREK</span>
          </Link>
          <span className="font-mono text-[10px] sm:text-xs text-white/40 uppercase tracking-widest">Profil personnel</span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {loading && (
          <div className="text-center py-20" data-testid="profil-loading">
            <div className="w-10 h-10 mx-auto border-2 border-[#0a1520] border-t-[#2cc4f5] rounded-full animate-spin mb-4" />
            <p className="font-mono text-xs text-[#2cc4f5]/60">Chargement du profil...</p>
          </div>
        )}

        {!loading && notFound && (
          <div className="text-center py-20" data-testid="profil-not-found">
            <h1 className="font-display text-3xl text-white mb-3">Profil introuvable</h1>
            <p className="font-mono text-sm text-white/40 mb-8">
              Ce FREK-ID n'existe pas encore — il sera créé à votre première trace.
            </p>
            <Link
              to="/accueil"
              className="inline-block px-5 py-3 bg-[#2cc4f5] text-[#050a0d] font-mono text-xs uppercase tracking-wider rounded hover:bg-[#33cfff] transition-all font-bold"
              data-testid="profil-not-found-cta"
            >
              Retour
            </Link>
          </div>
        )}

        {!loading && !notFound && (
          <>
            {/* En-tête personnel */}
            <section data-testid="profil-header" className="mb-8 sm:mb-12">
              <div className="font-mono text-[10px] text-[#2cc4f5]/60 uppercase tracking-widest mb-2">
                Votre compte FREK
              </div>
              <h1 className="font-display text-3xl sm:text-4xl text-white break-all" data-testid="profil-frek-id">
                {frekId}
              </h1>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                {status && !status.revoked && !status.expired && (
                  <span data-testid="profil-status-active" className="px-2.5 py-1 bg-[#2cc4f5]/15 text-[#2cc4f5] font-mono text-[10px] uppercase tracking-wider rounded-full border border-[#2cc4f5]/30">
                    Actif · Stage {status.current_stage}
                  </span>
                )}
                {status?.revoked && (
                  <span data-testid="profil-status-revoked" className="px-2.5 py-1 bg-red-500/15 text-red-300 font-mono text-[10px] uppercase tracking-wider rounded-full border border-red-500/30">
                    Révoqué
                  </span>
                )}
                {status?.expired && !status?.revoked && (
                  <span data-testid="profil-status-expired" className="px-2.5 py-1 bg-amber-500/15 text-amber-300 font-mono text-[10px] uppercase tracking-wider rounded-full border border-amber-500/30">
                    Expiré
                  </span>
                )}
                {hasFingerprintConsent && (
                  <span data-testid="profil-fingerprint-badge" className="px-2.5 py-1 bg-emerald-500/15 text-emerald-300 font-mono text-[10px] uppercase tracking-wider rounded-full border border-emerald-500/30">
                    Profil culturel certifié
                  </span>
                )}
              </div>

              <p className="font-mono text-[11px] text-white/30 mt-4 max-w-xl leading-relaxed">
                Seules vos traces personnelles apparaissent ici. La masse de la plateforme
                reste sur la page <Link to="/accueil" className="text-[#2cc4f5]/70 underline">d'accueil</Link>.
              </p>
            </section>

            {error && (
              <div className="mb-6 rounded-lg p-3 bg-red-500/10 border border-red-500/30 font-mono text-[11px] text-red-300" data-testid="profil-error">
                {error}
              </div>
            )}

            {/* Actions personnelles : passeport + export RGPD */}
            <section data-testid="profil-actions" className="mb-10 grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                onClick={downloadPassport}
                data-testid="profil-download-passport-btn"
                className="text-left bg-[#0a1520]/60 hover:bg-[#0a1520] border border-[#2cc4f5]/20 hover:border-[#2cc4f5]/50 rounded-xl p-4 transition-colors"
              >
                <div className="font-mono text-[10px] text-[#2cc4f5]/60 uppercase tracking-widest mb-1">Passeport souverain</div>
                <div className="font-mono text-sm text-white">Télécharger passport.json</div>
                <div className="font-mono text-[10px] text-white/40 mt-1">Signé Ed25519 · vérifiable offline</div>
              </button>

              <Link
                to={`/verify/${encodeURIComponent(frekId)}`}
                data-testid="profil-verify-link"
                className="block bg-[#0a1520]/60 hover:bg-[#0a1520] border border-[#2cc4f5]/20 hover:border-[#2cc4f5]/50 rounded-xl p-4 transition-colors"
              >
                <div className="font-mono text-[10px] text-[#2cc4f5]/60 uppercase tracking-widest mb-1">Vérification publique</div>
                <div className="font-mono text-sm text-white">Ouvrir page /verify</div>
                <div className="font-mono text-[10px] text-white/40 mt-1">Ancrage Bitcoin · audit lisible</div>
              </Link>
            </section>

            {/* Compteurs personnels — strictement issus du compte */}
            <section data-testid="profil-counters" className="mb-10 grid grid-cols-3 gap-3">
              <div className="bg-[#0a1520]/40 border border-[#2cc4f5]/10 rounded-xl p-4">
                <div className="font-mono text-[9px] text-[#2cc4f5]/50 uppercase tracking-widest">Présences</div>
                <div data-testid="profil-count-presences" className="font-display text-2xl sm:text-3xl text-white tabular-nums mt-1">
                  {buckets.presence.length}
                </div>
              </div>
              <div className="bg-[#0a1520]/40 border border-[#f7931a]/10 rounded-xl p-4">
                <div className="font-mono text-[9px] text-[#f7931a]/60 uppercase tracking-widest">Œuvres</div>
                <div data-testid="profil-count-works" className="font-display text-2xl sm:text-3xl text-white tabular-nums mt-1">
                  {buckets.work.length}
                </div>
              </div>
              <div className="bg-[#0a1520]/40 border border-emerald-400/10 rounded-xl p-4">
                <div className="font-mono text-[9px] text-emerald-400/60 uppercase tracking-widest">Croisements</div>
                <div data-testid="profil-count-cross" className="font-display text-2xl sm:text-3xl text-white tabular-nums mt-1">
                  {buckets.cross.length}
                </div>
              </div>
            </section>

            {/* Timelines */}
            <section className="space-y-10">
              <div>
                <h2 className="font-display text-xl text-white mb-3">Présences</h2>
                {buckets.presence.length === 0 ? (
                  <EmptySection
                    label="FREK-P"
                    testid="profil-empty-presences"
                    message="Aucune présence encore — scannez votre premier badge."
                  />
                ) : (
                  <Timeline items={buckets.presence} kind="presence" testid="profil-timeline-presences" />
                )}
              </div>

              <div>
                <h2 className="font-display text-xl text-white mb-3">Œuvres certifiées</h2>
                {buckets.work.length === 0 ? (
                  <EmptySection
                    label="FREK-O"
                    testid="profil-empty-works"
                    message="Aucune œuvre encore — certifiez votre première création."
                  />
                ) : (
                  <Timeline items={buckets.work} kind="work" testid="profil-timeline-works" />
                )}
              </div>

              <div>
                <h2 className="font-display text-xl text-white mb-3">Croisements</h2>
                {buckets.cross.length === 0 ? (
                  <EmptySection
                    label="FREK-X"
                    testid="profil-empty-cross"
                    message="Aucun événement encore."
                  />
                ) : (
                  <Timeline items={buckets.cross} kind="cross" testid="profil-timeline-cross" />
                )}
              </div>
            </section>
          </>
        )}
      </main>

      <footer className="border-t border-[#2cc4f5]/10 mt-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-white/30 uppercase tracking-widest">
          <span>Compte personnel · données privées</span>
          <Link to="/privacy" className="hover:text-[#2cc4f5]">Confidentialité</Link>
        </div>
      </footer>
    </div>
  );
}
