import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

/**
 * FREKCORE — Verification d'un moment signe (route publique #1).
 * Reservee aux FREK-ID prefixes "m-" (fenetre publique anonyme).
 * Doctrine : page de PREUVE avant d'etre page media.
 */

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

export default function MomentVerify({ frekId }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await fetch(`${API}/api/v1/moment/detail/${frekId}`);
        if (!res.ok) {
          if (res.status === 404) setError('Moment introuvable');
          else setError(`Erreur ${res.status}`);
          return;
        }
        const data = await res.json();
        if (!cancelled) setDetail(data);
      } catch {
        if (!cancelled) setError('Erreur de connexion');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [frekId]);

  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  const loadPreview = async () => {
    if (previewUrl || !detail?.media?.stored) return;
    setPreviewLoading(true);
    try {
      const res = await fetch(`${API}${detail.media.url}`);
      if (res.ok) {
        const blob = await res.blob();
        setPreviewUrl(URL.createObjectURL(blob));
      }
    } finally {
      setPreviewLoading(false);
    }
  };

  const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 flex flex-col overflow-hidden">
      <motion.header
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative z-10 p-6 flex justify-between items-center max-w-5xl mx-auto w-full"
      >
        <Link to="/" className="text-xl font-bold text-slate-900" data-testid="mv-brand">FREKCORE</Link>
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="mv-link-sign">← Signer</Link>
          <Link to="/manifeste" className="hover:text-blue-600 transition-colors" data-testid="mv-link-manifeste">Manifeste</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 flex-1 max-w-2xl mx-auto w-full px-6 py-10">
        {loading && (
          <div className="text-center py-20" data-testid="mv-loading">
            <div className="w-10 h-10 mx-auto border-2 border-slate-200 border-t-blue-600 rounded-full animate-spin mb-4" />
            <p className="text-sm text-slate-500">Vérification…</p>
          </div>
        )}

        {error && (
          <div className="text-center py-20" data-testid="mv-error">
            <div className="text-5xl mb-4 text-slate-300">?</div>
            <p className="text-slate-900 font-semibold mb-6">{error}</p>
            <Link to="/" className="inline-block px-6 py-3 bg-slate-900 text-white rounded-full font-semibold hover:bg-slate-700 transition-colors" data-testid="mv-back-home">
              Retour à l&apos;accueil
            </Link>
          </div>
        )}

        {detail && !loading && (
          <motion.div variants={container} initial="hidden" animate="show" className="space-y-8" data-testid="mv-detail">
            {/* Badge Moment attesté */}
            <motion.div variants={item} className="text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-full text-blue-700 text-sm font-semibold" data-testid="mv-badge">
                <span className="text-blue-600">✓</span> Moment attesté
              </div>
            </motion.div>

            {/* FREK-ID */}
            <motion.div variants={item} className="text-center">
              <div className="text-[10px] text-slate-400 uppercase tracking-[0.3em] mb-2">FREK-ID</div>
              <div className="text-slate-900 font-mono text-sm md:text-base break-all" data-testid="mv-frek-id">
                {detail.frek_id}
              </div>
            </motion.div>

            {/* Titre (optionnel) */}
            {detail.title && (
              <motion.h1 variants={item} className="text-3xl md:text-5xl font-black tracking-tighter text-slate-900 text-center leading-tight" data-testid="mv-title">
                « {detail.title} »
              </motion.h1>
            )}

            {/* Bloc metadata */}
            <motion.div variants={item} className="bg-white/70 backdrop-blur-xl border border-white/50 rounded-3xl p-6 md:p-8 space-y-5 shadow-xl">
              <div>
                <div className="text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-1">Date de signature</div>
                <div className="text-slate-900 text-sm font-mono" data-testid="mv-date">
                  {new Date(detail.created_at).toLocaleString('fr-FR', { dateStyle: 'full', timeStyle: 'short' })}
                </div>
              </div>

              {detail.geo && (
                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-1">Lieu</div>
                  <div className="text-slate-900 text-sm font-mono" data-testid="mv-geo">
                    {detail.geo.lat?.toFixed(3)}, {detail.geo.lon?.toFixed(3)}
                    {detail.geo.accuracy_m && <span className="text-slate-500"> · ±{detail.geo.accuracy_m}m</span>}
                  </div>
                </div>
              )}

              {detail.block?.block_hash && (
                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-1">
                    Empreinte vérifiable {detail.block.btc_anchored && <span className="text-blue-600">· Bitcoin</span>}
                  </div>
                  <div className="text-slate-900 font-mono text-xs break-all" data-testid="mv-block-hash">
                    {detail.block.block_hash}
                  </div>
                </div>
              )}

              {detail.media?.hash && (
                <div data-testid="mv-media-hash">
                  <div className="text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-1">
                    Empreinte {detail.media.kind === 'image' ? 'photo' : 'audio'}
                  </div>
                  <div className="text-slate-900 font-mono text-xs break-all">{detail.media.hash}</div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    {detail.media.stored ? 'Fichier chiffré conservé' : 'Hash uniquement — fichier non conservé'}
                  </div>
                </div>
              )}

              {detail.layers_captured?.length > 0 && (
                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-2">Couches capturées</div>
                  <div className="flex flex-wrap gap-2">
                    {detail.layers_captured.map((l) => (
                      <span key={l} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs border border-blue-200/50">{l}</span>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>

            {/* Actions media */}
            {detail.media?.stored && (
              <motion.div variants={item} className="space-y-4" data-testid="mv-media-actions">
                <div className="flex flex-wrap justify-center gap-3">
                  <button
                    onClick={loadPreview}
                    disabled={previewLoading || !!previewUrl}
                    className="px-6 py-3 bg-slate-900 text-white rounded-full font-semibold shadow-lg hover:bg-slate-700 transition-colors disabled:opacity-60"
                    data-testid="mv-btn-preview"
                  >
                    {previewLoading ? 'Chargement…' : previewUrl ? 'Aperçu chargé ↓' : 'Voir aperçu'}
                  </button>
                  <a
                    href={`${API}${detail.media.url}`}
                    download={`frek-${detail.frek_id}.${detail.media.content_type?.split('/')?.[1] || 'bin'}`}
                    className="px-6 py-3 bg-white/70 backdrop-blur border border-slate-300 text-slate-900 rounded-full font-semibold hover:bg-white transition-colors"
                    data-testid="mv-btn-download"
                  >
                    Télécharger l&apos;original
                  </a>
                </div>

                {previewUrl && detail.media.kind === 'image' && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    className="flex justify-center pt-2"
                  >
                    <img
                      src={previewUrl}
                      alt="Aperçu"
                      className="max-w-full max-h-96 rounded-2xl shadow-2xl border border-white/50"
                      data-testid="mv-preview-image"
                    />
                  </motion.div>
                )}

                {previewUrl && detail.media.kind === 'audio' && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    className="flex justify-center pt-2"
                  >
                    <audio controls src={previewUrl} className="w-full max-w-md" data-testid="mv-preview-audio" />
                  </motion.div>
                )}
              </motion.div>
            )}

            <motion.div variants={item} className="text-center pt-4">
              <Link to="/" className="text-blue-600 hover:underline text-sm font-semibold" data-testid="mv-cta-sign-another">
                Signer un autre moment →
              </Link>
            </motion.div>
          </motion.div>
        )}
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400">
        FREKCORE — Infrastructure de preuve culturelle • v1.0
      </footer>
    </div>
  );
}
