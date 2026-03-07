/**
 * FREK v2 — Page de Vérification Publique
 * ========================================
 * Affiche les détails d'un FREK-ID sans compte requis
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
          if (response.status === 404) {
            setError('FREK-ID introuvable');
          } else {
            setError(`Erreur ${response.status}`);
          }
          setLoading(false);
          return;
        }

        const data = await response.json();
        setAttestation(data);
      } catch (err) {
        setError('Erreur de connexion');
      } finally {
        setLoading(false);
      }
    };

    fetchAttestation();
  }, [frekId]);

  const formatTimestamp = (ms) => {
    const date = new Date(ms);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-dark via-navy to-dark text-white">
      {/* Header */}
      <header className="bg-dark/90 backdrop-blur-xl border-b border-frek-500/20">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img src="/frek-logo.png" alt="FREK" className="h-8 w-auto" />
            <span className="font-display text-xl tracking-wider text-frek-500">FREK</span>
          </Link>
          <Link
            to="/certify"
            className="px-4 py-2 bg-frek-500 text-dark font-mono text-xs uppercase tracking-wider rounded hover:bg-frek-400 transition-all font-bold"
          >
            Certifier
          </Link>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-2xl mx-auto px-6 py-12">
        {loading && (
          <div className="text-center py-20">
            <div className="w-12 h-12 mx-auto border-2 border-frek-800 border-t-frek-500 rounded-full animate-spin mb-4" />
            <p className="font-mono text-sm text-frek-600">Vérification...</p>
          </div>
        )}

        {error && (
          <div className="text-center py-20">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center">
              <svg className="w-10 h-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="font-display text-2xl text-red-500 mb-2">Non trouvé</h2>
            <p className="font-mono text-sm text-red-400 mb-8">{error}</p>
            <Link
              to="/certify"
              className="inline-block px-6 py-3 bg-frek-500 text-dark font-mono text-xs uppercase tracking-wider rounded hover:bg-frek-400 transition-all font-bold"
            >
              Créer une certification
            </Link>
          </div>
        )}

        {attestation && (
          <div className="space-y-8" data-testid="attestation-details">
            {/* Titre */}
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-frek-500/20 border-2 border-frek-500 flex items-center justify-center">
                <svg className="w-8 h-8 text-frek-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span className="inline-block px-3 py-1 bg-frek-500/20 text-frek-500 font-mono text-xs uppercase tracking-wider rounded-full mb-2">
                Vérifié
              </span>
              <h1 className="font-display text-3xl text-frek-500">
                ATTESTATION FREK
              </h1>
            </div>

            {/* FREK-ID */}
            <div className="bg-frek-900/30 rounded-xl p-6 border border-frek-500/20">
              <div className="font-mono text-[10px] text-frek-600 uppercase tracking-wider mb-2">
                FREK-ID
              </div>
              <div className="font-mono text-lg text-frek-400 break-all" data-testid="verified-frek-id">
                {attestation.frek_id}
              </div>
            </div>

            {/* QR Code */}
            <div className="text-center">
              <div className="inline-block p-4 bg-white rounded-xl shadow-lg shadow-frek-500/20">
                <QRCodeSVG
                  value={`${window.location.origin}/verify/${attestation.frek_id}`}
                  size={160}
                  level="M"
                  fgColor="#0a1520"
                />
              </div>
            </div>

            {/* Détails */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-frek-900/30 rounded-lg p-4 border border-frek-500/10">
                <div className="font-mono text-[10px] text-frek-600 uppercase tracking-wider mb-1">
                  Horodatage
                </div>
                <div className="font-mono text-sm text-frek-400">
                  {formatTimestamp(attestation.timestamp_ms)}
                </div>
              </div>

              <div className="bg-frek-900/30 rounded-lg p-4 border border-frek-500/10">
                <div className="font-mono text-[10px] text-frek-600 uppercase tracking-wider mb-1">
                  Stade
                </div>
                <div className="font-mono text-sm text-frek-400">
                  {attestation.stade === 4 ? 'EMISSION' : attestation.stade}
                </div>
              </div>

              <div className="bg-frek-900/30 rounded-lg p-4 border border-frek-500/10">
                <div className="font-mono text-[10px] text-frek-600 uppercase tracking-wider mb-1">
                  Artiste ID
                </div>
                <div className="font-mono text-sm text-frek-400 truncate">
                  {attestation.artiste_id}
                </div>
              </div>

              <div className="bg-frek-900/30 rounded-lg p-4 border border-frek-500/10">
                <div className="font-mono text-[10px] text-frek-600 uppercase tracking-wider mb-1">
                  Vecteur
                </div>
                <div className="font-mono text-sm text-frek-400">
                  {attestation.vector_528d?.length || 528}D
                </div>
              </div>
            </div>

            {/* SHA-256 */}
            <div className="bg-frek-900/30 rounded-lg p-4 border border-frek-500/10">
              <div className="font-mono text-[10px] text-frek-600 uppercase tracking-wider mb-2">
                SHA-256 Signal
              </div>
              <div className="font-mono text-xs text-frek-500 break-all">
                {attestation.sha256_signal}
              </div>
            </div>

            <div className="bg-frek-900/30 rounded-lg p-4 border border-frek-500/10">
              <div className="font-mono text-[10px] text-frek-600 uppercase tracking-wider mb-2">
                Hash Chaîné
              </div>
              <div className="font-mono text-xs text-frek-500 break-all">
                {attestation.hash_chaine}
              </div>
            </div>

            {/* Chaînage */}
            {attestation.prev_frek_id && (
              <div className="bg-frek-900/30 rounded-lg p-4 border border-frek-500/10">
                <div className="font-mono text-[10px] text-frek-600 uppercase tracking-wider mb-2">
                  FREK-ID Précédent (Chaînage)
                </div>
                <Link
                  to={`/verify/${attestation.prev_frek_id}`}
                  className="font-mono text-xs text-frek-400 hover:text-frek-300 underline"
                >
                  {attestation.prev_frek_id}
                </Link>
              </div>
            )}

            {/* Résonance */}
            {attestation.resonance && attestation.resonance.match_count > 0 && (
              <div className="bg-frek-900/30 rounded-lg p-4 border border-frek-500/10">
                <div className="font-mono text-[10px] text-frek-600 uppercase tracking-wider mb-2">
                  Résonances détectées
                </div>
                <div className="space-y-2">
                  {attestation.resonance.matches?.slice(0, 3).map((match, i) => (
                    <div key={i} className="flex justify-between items-center">
                      <Link
                        to={`/verify/${match.frek_id}`}
                        className="font-mono text-xs text-frek-400 hover:text-frek-300"
                      >
                        {match.frek_id}
                      </Link>
                      <span className="font-mono text-xs text-frek-600">
                        {match.similarity?.toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Note juridique */}
            <div className="text-center pt-8 border-t border-frek-500/10">
              <p className="font-mono text-[10px] text-frek-700 uppercase tracking-wider">
                Cette attestation certifie un fait technique.
              </p>
              <p className="font-mono text-[10px] text-frek-800">
                Elle ne constitue pas une déclaration de droits.
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default Verify;
