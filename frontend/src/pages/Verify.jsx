/**
 * FREK v2 — Page de Vérification
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

export function Verify() {
  const { frekId } = useParams();
  const [attestation, setAttestation] = useState(null);
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
        const response = await fetch(`${API_URL}/api/frek/verify/${frekId}`);
        if (!response.ok) {
          setError(response.status === 404 ? 'FREK-ID introuvable' : `Erreur ${response.status}`);
          setLoading(false);
          return;
        }
        setAttestation(await response.json());
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

        {attestation && (
          <div className="space-y-6 sm:space-y-8" data-testid="attestation-details">
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
