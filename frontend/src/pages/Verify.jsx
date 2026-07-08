/**
 * FREK v2 — Page de Vérification
 * Route les FREK-ID publics (prefix "m-") vers MomentVerify (theme clair v1.0).
 * Les FREK-ID stage-based restent sur l'ancienne UI.
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import PassportPanel from '../components/PassportPanel';
import MomentVerify from './MomentVerify';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

export function Verify() {
  const { frekId } = useParams();

  // Route les moments publics vers l'UI dediee (theme clair v1.0)
  if (frekId && frekId.startsWith('m-')) {
    return <MomentVerify frekId={frekId} />;
  }

  return <LegacyVerify frekId={frekId} />;
}

function LegacyVerify({ frekId }) {
  const [attestation, setAttestation] = useState(null);
  const [notary, setNotary] = useState(null);
  const [status, setStatus] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAttestation = async () => {
      if (!frekId) {
        setError('FREK-ID manquant');
        setLoading(false);
        return;
      }

      try {
        const [attRes, notaryRes, statusRes, auditRes] = await Promise.allSettled([
          fetch(`${API_URL}/api/frek/verify/${frekId}`),
          fetch(`${API_URL}/api/v1/notary/proof/${frekId}`),
          fetch(`${API_URL}/api/v1/identity/${frekId}/status`),
          fetch(`${API_URL}/api/v1/audit/${frekId}`),
        ]);

        if (attRes.status === 'fulfilled' && attRes.value.ok) {
          setAttestation(await attRes.value.json());
        } else if (attRes.status === 'fulfilled') {
          const r = attRes.value;
          if (r.status !== 404) setError(`Erreur ${r.status}`);
        }

        if (notaryRes.status === 'fulfilled' && notaryRes.value.ok) {
          setNotary(await notaryRes.value.json());
        }
        if (statusRes.status === 'fulfilled' && statusRes.value.ok) {
          setStatus(await statusRes.value.json());
        }
        if (auditRes.status === 'fulfilled' && auditRes.value.ok) {
          setTimeline(await auditRes.value.json());
        }

        if (
          (attRes.status !== 'fulfilled' || !attRes.value.ok) &&
          (notaryRes.status !== 'fulfilled' || !notaryRes.value.ok) &&
          (statusRes.status !== 'fulfilled' || !statusRes.value.ok)
        ) {
          setError('FREK-ID introuvable');
        }
      } catch (err) {
        setError('Erreur de connexion');
      } finally {
        setLoading(false);
      }
    };

    fetchAttestation();
  }, [frekId]);

  const formatTimestamp = (ms) => {
    return new Date(ms).toLocaleDateString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#050a0d] via-[#0a1520] to-[#050a0d] text-white">
      {/* Header */}
      <header className="bg-[#050a0d]/95 backdrop-blur-xl border-b border-[#2cc4f5]/10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 sm:gap-3">
            <img src="/frek-logo.png" alt="FREK" className="h-6 sm:h-8 w-auto" />
            <span className="font-display text-lg sm:text-xl tracking-wider text-[#2cc4f5]">FREK</span>
          </Link>
          <Link
            to="/"
            className="px-3 sm:px-4 py-1.5 sm:py-2 bg-[#2cc4f5] text-[#050a0d] font-mono text-[10px] sm:text-xs uppercase tracking-wider rounded hover:bg-[#33cfff] transition-all font-bold"
          >
            Certifier
          </Link>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {loading && (
          <div className="text-center py-16 sm:py-20">
            <div className="w-10 h-10 sm:w-12 sm:h-12 mx-auto border-2 border-[#0a1520] border-t-[#2cc4f5] rounded-full animate-spin mb-4" />
            <p className="font-mono text-xs sm:text-sm text-[#2cc4f5]/60">Vérification...</p>
          </div>
        )}

        {error && (
          <div className="text-center py-16 sm:py-20">
            <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-4 sm:mb-6 rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center">
              <svg className="w-8 h-8 sm:w-10 sm:h-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <p className="font-mono text-xs sm:text-sm text-red-400/80 mb-6 sm:mb-8">{error}</p>
            <Link
              to="/"
              className="inline-block px-5 sm:px-6 py-2.5 sm:py-3 bg-[#2cc4f5] text-[#050a0d] font-mono text-[10px] sm:text-xs uppercase tracking-wider rounded hover:bg-[#33cfff] transition-all font-bold"
            >
              Certifier
            </Link>
          </div>
        )}

        {!attestation && !loading && !error && (status || notary) && (
          <div className="space-y-6 sm:space-y-8" data-testid="frekv1-details">
            {/* Banner revoque / expire */}
            {status && (status.revoked || status.expired) && (
              <div
                data-testid="status-banner"
                className={`rounded-xl p-4 sm:p-5 border-2 text-center ${
                  status.revoked ? 'border-red-500/60 bg-red-500/10' : 'border-amber-500/60 bg-amber-500/10'
                }`}
              >
                <div className={`font-mono text-sm sm:text-base uppercase tracking-widest mb-1 ${status.revoked ? 'text-red-300' : 'text-amber-300'}`}>
                  {status.revoked ? '✕ Identite revoquee' : '⏰ Identite expiree'}
                </div>
                {status.revoked && status.revoke_reason && (
                  <div className="font-mono text-[11px] text-red-300/80">Motif : {status.revoke_reason}</div>
                )}
                {status.revoked && status.revoked_at && (
                  <div className="font-mono text-[10px] text-red-300/60 mt-1">Le {new Date(status.revoked_at).toLocaleString('fr-FR')}</div>
                )}
                <div className="font-mono text-[10px] text-white/40 mt-2">
                  La preuve historique reste lisible sur la FREK-Chain.
                </div>
              </div>
            )}

            {/* Identite valide */}
            {status && !status.revoked && !status.expired && (
              <div className="text-center">
                <div className="w-14 h-14 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 rounded-full bg-[#2cc4f5]/20 border-2 border-[#2cc4f5] flex items-center justify-center">
                  <svg className="w-7 h-7 sm:w-8 sm:h-8 text-[#2cc4f5]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="inline-block px-2.5 sm:px-3 py-1 bg-[#2cc4f5]/20 text-[#2cc4f5] font-mono text-[9px] sm:text-[10px] uppercase tracking-wider rounded-full">
                  Verifie · Stage {status.current_stage}
                </span>
              </div>
            )}

            {/* FREK-ID */}
            <div className="bg-[#0a1520]/50 rounded-xl p-4 sm:p-6 border border-[#2cc4f5]/10">
              <div className="font-mono text-[9px] sm:text-[10px] text-[#2cc4f5]/50 uppercase tracking-wider mb-1 sm:mb-2">FREK-ID</div>
              <div className="font-mono text-sm sm:text-base text-[#2cc4f5] break-all" data-testid="verified-frek-id">
                {frekId}
              </div>
              {status && (
                <div className="mt-3 grid grid-cols-2 gap-3 text-left">
                  <div>
                    <div className="font-mono text-[9px] text-[#2cc4f5]/40 uppercase tracking-wider">Cree</div>
                    <div className="font-mono text-[11px] text-white/60">{status.created_at?.slice(0,10)}</div>
                  </div>
                  <div>
                    <div className="font-mono text-[9px] text-[#2cc4f5]/40 uppercase tracking-wider">Progression</div>
                    <div className="font-mono text-[11px] text-white/60">{status.progression}%</div>
                  </div>
                  {status.expires_at && (
                    <div className="col-span-2">
                      <div className="font-mono text-[9px] text-[#2cc4f5]/40 uppercase tracking-wider">Expire</div>
                      <div className="font-mono text-[11px] text-white/60">{new Date(status.expires_at).toLocaleString('fr-FR')}</div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Passeport souverain Ed25519 — verification offline live */}
            <PassportPanel frekId={frekId} />

            {/* Notary panel */}
            {notary && (
              <div
                data-testid="notary-panel"
                className="bg-gradient-to-br from-[#f7931a]/10 to-[#0a1520]/80 rounded-xl p-4 sm:p-5 border border-[#f7931a]/30"
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 rounded-full bg-[#f7931a]/20 border border-[#f7931a]/40 flex items-center justify-center">
                    <span className="text-[#f7931a] font-bold">₿</span>
                  </div>
                  <div>
                    <div className="font-mono text-[10px] text-[#f7931a] uppercase tracking-wider">Notaire Culturel Tech</div>
                    <div className="font-mono text-[9px] text-[#f7931a]/60">FREK-Chain · OpenTimestamps · Bitcoin</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div>
                    <div className="font-mono text-[9px] text-[#f7931a]/50 uppercase tracking-wider mb-1">Block</div>
                    <div data-testid="notary-block-height" className="font-mono text-xs sm:text-sm text-[#f7931a]">#{notary.block.height}</div>
                  </div>
                  <div>
                    <div className="font-mono text-[9px] text-[#f7931a]/50 uppercase tracking-wider mb-1">Statut</div>
                    <div data-testid="notary-status" className="font-mono text-xs sm:text-sm text-[#f7931a]">
                      {notary.btc_anchored ? 'Confirme Bitcoin' : 'Ancre (en attente BTC)'}
                    </div>
                  </div>
                </div>
                <div className="mb-2">
                  <div className="font-mono text-[9px] text-[#f7931a]/50 uppercase tracking-wider mb-1">Block-hash</div>
                  <div className="font-mono text-[10px] sm:text-[11px] text-[#f7931a]/80 break-all">{notary.block.block_hash}</div>
                </div>
                {notary.btc_anchored && notary.btc_attestation?.btc_block_height && (
                  <div className="mb-2">
                    <div className="font-mono text-[9px] text-[#f7931a]/50 uppercase tracking-wider mb-1">Bitcoin block height</div>
                    <a
                      href={`https://mempool.space/block-height/${notary.btc_attestation.btc_block_height}`}
                      target="_blank" rel="noopener noreferrer"
                      data-testid="notary-btc-link"
                      className="font-mono text-[11px] sm:text-xs text-[#f7931a] hover:text-[#ffa83d] underline"
                    >
                      #{notary.btc_attestation.btc_block_height} ↗ mempool.space
                    </a>
                  </div>
                )}
                <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-[#f7931a]/20">
                  <a
                    href={`${API_URL}/api/v1/notary/proof/${frekId}/ots`}
                    download={`frek-${frekId}.ots`}
                    data-testid="notary-download-ots"
                    className="px-3 py-1.5 bg-[#f7931a]/10 border border-[#f7931a]/40 text-[#f7931a] font-mono text-[10px] uppercase tracking-wider rounded hover:bg-[#f7931a]/20 transition-all"
                  >
                    Telecharger preuve .ots
                  </a>
                </div>
              </div>
            )}

            {/* Timeline */}
            {timeline && timeline.length > 0 && (
              <div data-testid="timeline-panel" className="rounded-xl border border-white/10 bg-[#0a1520]/40 p-4 sm:p-5">
                <div className="font-mono text-[10px] sm:text-xs text-[#2cc4f5]/70 uppercase tracking-wider mb-3">
                  Parcours culturel (audit trail)
                </div>
                <ol className="space-y-2 max-h-72 overflow-auto">
                  {timeline.map((e, i) => (
                    <li key={i} data-testid={`timeline-event-${e.kind}`} className="flex items-start gap-3 text-left">
                      <span className="font-mono text-[10px] text-white/30 w-32 shrink-0 pt-0.5">
                        {e.timestamp ? new Date(e.timestamp).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'}
                      </span>
                      <span className={`inline-block w-1.5 h-1.5 rounded-full mt-2 shrink-0 ${
                        e.kind === 'revocation' ? 'bg-red-400'
                        : e.kind === 'renewal' ? 'bg-amber-400'
                        : e.kind === 'scan' ? 'bg-[#2cc4f5]'
                        : e.kind === 'transaction' ? 'bg-[#f7931a]'
                        : 'bg-white/40'
                      }`} />
                      <span className="font-mono text-[11px] text-white/80 flex-1">{e.label}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}

        {attestation && (
          <div className="space-y-6 sm:space-y-8" data-testid="attestation-details">
            {/* Badge revoque/expire avant tout le reste */}
            {status && (status.revoked || status.expired) && (
              <div
                data-testid="status-banner"
                className={`rounded-xl p-4 sm:p-5 border-2 text-center ${
                  status.revoked
                    ? 'border-red-500/60 bg-red-500/10'
                    : 'border-amber-500/60 bg-amber-500/10'
                }`}
              >
                <div className={`font-mono text-sm sm:text-base uppercase tracking-widest mb-1 ${status.revoked ? 'text-red-300' : 'text-amber-300'}`}>
                  {status.revoked ? '✕ Identite revoquee' : '⏰ Identite expiree'}
                </div>
                {status.revoked && status.revoke_reason && (
                  <div className="font-mono text-[11px] text-red-300/80">
                    Motif : {status.revoke_reason}
                  </div>
                )}
                {status.revoked && status.revoked_at && (
                  <div className="font-mono text-[10px] text-red-300/60 mt-1">
                    Le {new Date(status.revoked_at).toLocaleString('fr-FR')}
                  </div>
                )}
                <div className="font-mono text-[10px] text-white/40 mt-2">
                  La preuve historique reste lisible sur la FREK-Chain.
                </div>
              </div>
            )}

            {/* Badge vérifié */}
            <div className="text-center">
              <div className="w-14 h-14 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 rounded-full bg-[#2cc4f5]/20 border-2 border-[#2cc4f5] flex items-center justify-center">
                <svg className="w-7 h-7 sm:w-8 sm:h-8 text-[#2cc4f5]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span className="inline-block px-2.5 sm:px-3 py-1 bg-[#2cc4f5]/20 text-[#2cc4f5] font-mono text-[9px] sm:text-[10px] uppercase tracking-wider rounded-full">
                Vérifié
              </span>
            </div>

            {/* FREK-ID */}
            <div className="bg-[#0a1520]/50 rounded-xl p-4 sm:p-6 border border-[#2cc4f5]/10">
              <div className="font-mono text-[9px] sm:text-[10px] text-[#2cc4f5]/50 uppercase tracking-wider mb-1 sm:mb-2">
                FREK-ID
              </div>
              <div className="font-mono text-sm sm:text-base text-[#2cc4f5] break-all" data-testid="verified-frek-id">
                {attestation.frek_id}
              </div>
            </div>

            {/* QR Code */}
            <div className="text-center">
              <div className="inline-block p-3 sm:p-4 bg-white rounded-xl shadow-lg shadow-[#2cc4f5]/10">
                <QRCodeSVG
                  value={`${window.location.origin}/verify/${attestation.frek_id}`}
                  size={140}
                  level="M"
                  fgColor="#0a1520"
                />
              </div>
            </div>

            {/* Infos */}
            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              <div className="bg-[#0a1520]/50 rounded-lg p-3 sm:p-4 border border-[#2cc4f5]/10">
                <div className="font-mono text-[9px] sm:text-[10px] text-[#2cc4f5]/50 uppercase tracking-wider mb-1">
                  Date
                </div>
                <div className="font-mono text-xs sm:text-sm text-[#8ab4c8]">
                  {formatTimestamp(attestation.timestamp_ms)}
                </div>
              </div>

              <div className="bg-[#0a1520]/50 rounded-lg p-3 sm:p-4 border border-[#2cc4f5]/10">
                <div className="font-mono text-[9px] sm:text-[10px] text-[#2cc4f5]/50 uppercase tracking-wider mb-1">
                  Stade
                </div>
                <div className="font-mono text-xs sm:text-sm text-[#8ab4c8]">
                  {attestation.stade === 4 ? 'EMISSION' : attestation.stade}
                </div>
              </div>
            </div>

            {/* SHA-256 */}
            <div className="bg-[#0a1520]/50 rounded-lg p-3 sm:p-4 border border-[#2cc4f5]/10">
              <div className="font-mono text-[9px] sm:text-[10px] text-[#2cc4f5]/50 uppercase tracking-wider mb-1 sm:mb-2">
                SHA-256
              </div>
              <div className="font-mono text-[10px] sm:text-xs text-[#2cc4f5]/70 break-all">
                {attestation.sha256_signal}
              </div>
            </div>

            {/* Passeport souverain Ed25519 — verification offline live */}
            <PassportPanel frekId={attestation.frek_id} />

            {/* FREK Notary — Notarisation Bitcoin */}
            {notary && (
              <div
                data-testid="notary-panel"
                className="bg-gradient-to-br from-[#f7931a]/10 to-[#0a1520]/80 rounded-xl p-4 sm:p-5 border border-[#f7931a]/30"
              >
                <div className="flex items-center gap-2 mb-3 sm:mb-4">
                  <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[#f7931a]/20 border border-[#f7931a]/40 flex items-center justify-center">
                    <span className="text-[#f7931a] text-sm sm:text-base font-bold">₿</span>
                  </div>
                  <div>
                    <div className="font-mono text-[10px] sm:text-xs text-[#f7931a] uppercase tracking-wider">
                      Notaire Culturel Tech
                    </div>
                    <div className="font-mono text-[9px] sm:text-[10px] text-[#f7931a]/60">
                      FREK-Chain · OpenTimestamps · Bitcoin
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 sm:gap-3 mb-3">
                  <div>
                    <div className="font-mono text-[9px] text-[#f7931a]/50 uppercase tracking-wider mb-1">
                      Block
                    </div>
                    <div
                      data-testid="notary-block-height"
                      className="font-mono text-xs sm:text-sm text-[#f7931a]"
                    >
                      #{notary.block.height}
                    </div>
                  </div>
                  <div>
                    <div className="font-mono text-[9px] text-[#f7931a]/50 uppercase tracking-wider mb-1">
                      Statut
                    </div>
                    <div
                      data-testid="notary-status"
                      className="font-mono text-xs sm:text-sm text-[#f7931a]"
                    >
                      {notary.btc_anchored ? 'Confirmé Bitcoin' : 'Ancré (en attente BTC)'}
                    </div>
                  </div>
                </div>

                <div className="mb-2">
                  <div className="font-mono text-[9px] text-[#f7931a]/50 uppercase tracking-wider mb-1">
                    Block-hash
                  </div>
                  <div className="font-mono text-[10px] sm:text-[11px] text-[#f7931a]/80 break-all">
                    {notary.block.block_hash}
                  </div>
                </div>

                {notary.btc_anchored && notary.btc_attestation?.btc_block_height && (
                  <div className="mb-2">
                    <div className="font-mono text-[9px] text-[#f7931a]/50 uppercase tracking-wider mb-1">
                      Bitcoin block height
                    </div>
                    <a
                      href={`https://mempool.space/block-height/${notary.btc_attestation.btc_block_height}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      data-testid="notary-btc-link"
                      className="font-mono text-[11px] sm:text-xs text-[#f7931a] hover:text-[#ffa83d] underline"
                    >
                      #{notary.btc_attestation.btc_block_height} ↗ mempool.space
                    </a>
                  </div>
                )}

                <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-[#f7931a]/20">
                  <a
                    href={`${API_URL}/api/v1/notary/proof/${frekId}/ots`}
                    download={`frek-${frekId}.ots`}
                    data-testid="notary-download-ots"
                    className="px-3 py-1.5 bg-[#f7931a]/10 border border-[#f7931a]/40 text-[#f7931a] font-mono text-[10px] uppercase tracking-wider rounded hover:bg-[#f7931a]/20 transition-all"
                  >
                    Télécharger preuve .ots
                  </a>
                  <a
                    href={`${API_URL}/api/v1/notary/block/${notary.block.height}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    data-testid="notary-view-block"
                    className="px-3 py-1.5 border border-[#f7931a]/30 text-[#f7931a]/80 font-mono text-[10px] uppercase tracking-wider rounded hover:border-[#f7931a]/60 hover:text-[#f7931a] transition-all"
                  >
                    Voir block JSON
                  </a>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 justify-center pt-4">
              <a
                href={`${API_URL}/api/frek/verify/${attestation.frek_id}/certificat.pdf`}
                className="px-4 sm:px-5 py-2 sm:py-2.5 border border-[#2cc4f5]/30 text-[#2cc4f5]/70 font-mono text-[10px] sm:text-xs uppercase tracking-wider hover:border-[#2cc4f5]/50 hover:text-[#2cc4f5] rounded transition-all"
              >
                PDF
              </a>
              <button
                onClick={() => navigator.clipboard.writeText(attestation.frek_id)}
                className="px-4 sm:px-5 py-2 sm:py-2.5 bg-[#2cc4f5] text-[#050a0d] font-mono text-[10px] sm:text-xs uppercase tracking-wider hover:bg-[#33cfff] rounded transition-all font-bold"
              >
                Copier
              </button>
            </div>

            {/* Timeline humaine — Audit trail */}
            {timeline && timeline.length > 0 && (
              <div data-testid="timeline-panel" className="rounded-xl border border-white/10 bg-[#0a1520]/40 p-4 sm:p-5">
                <div className="font-mono text-[10px] sm:text-xs text-[#2cc4f5]/70 uppercase tracking-wider mb-3">
                  Parcours culturel (audit trail)
                </div>
                <ol className="space-y-2 max-h-72 overflow-auto">
                  {timeline.map((e, i) => (
                    <li key={i} data-testid={`timeline-event-${e.kind}`} className="flex items-start gap-3 text-left">
                      <span className="font-mono text-[10px] text-white/30 w-32 shrink-0 pt-0.5">
                        {e.timestamp ? new Date(e.timestamp).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'}
                      </span>
                      <span className={`inline-block w-1.5 h-1.5 rounded-full mt-2 shrink-0 ${
                        e.kind === 'revocation' ? 'bg-red-400'
                        : e.kind === 'renewal' ? 'bg-amber-400'
                        : e.kind === 'scan' ? 'bg-[#2cc4f5]'
                        : e.kind === 'transaction' ? 'bg-[#f7931a]'
                        : 'bg-white/40'
                      }`} />
                      <span className="font-mono text-[11px] text-white/80 flex-1">{e.label}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#2cc4f5]/10 mt-auto">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 sm:py-6 text-center">
          <p className="font-mono text-[9px] sm:text-[10px] text-[#8ab4c8]/20 uppercase tracking-wider">
            © 2026 CVLN Group · frekcore.com
          </p>
        </div>
      </footer>
    </div>
  );
}

export default Verify;
