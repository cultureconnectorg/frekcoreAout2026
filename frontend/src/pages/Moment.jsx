import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import BrandLogo from '../components/BrandLogo';

/**
 * FREKCORE — Fenetre d'acces #1 : Signer le moment present.
 * v1.1 — media reel (photo / audio) optionnel + choix conservation.
 * Doctrine : la preuve reste independante du binaire.
 */

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = 'frek_moment_session';
const MOMENTS_KEY = 'frek_moments_local';
const MAX_MEDIA_BYTES = 15 * 1024 * 1024; // 15 MB (aligne avec backend)

function getSession() {
  let s = localStorage.getItem(SESSION_KEY);
  if (!s) {
    s = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, s);
  }
  return s;
}
function getLocalMoments() {
  try { return JSON.parse(localStorage.getItem(MOMENTS_KEY) || '[]'); } catch { return []; }
}
function saveLocalMoment(m) {
  const list = getLocalMoments();
  list.unshift(m);
  localStorage.setItem(MOMENTS_KEY, JSON.stringify(list.slice(0, 100)));
}

function ParticleField() {
  const orbs = Array.from({ length: 8 }, (_, i) => ({
    id: i,
    size: 200 + Math.random() * 300,
    x: Math.random() * 100,
    y: Math.random() * 100,
    delay: Math.random() * 5,
    duration: 20 + Math.random() * 30,
  }));
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      {orbs.map((o) => (
        <motion.div
          key={o.id}
          className="absolute rounded-full"
          style={{
            width: o.size, height: o.size,
            left: `${o.x}%`, top: `${o.y}%`,
            background: `radial-gradient(circle, rgba(59,130,246,0.12) 0%, rgba(147,197,253,0.04) 40%, transparent 70%)`,
            filter: 'blur(40px)',
          }}
          animate={{ x: [0, 60, -30, 0], y: [0, -40, 30, 0], scale: [1, 1.1, 0.95, 1] }}
          transition={{ duration: o.duration, delay: o.delay, repeat: Infinity, ease: 'easeInOut' }}
        />
      ))}
    </div>
  );
}

export default function Moment() {
  const [phase, setPhase] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [localMoments, setLocalMoments] = useState(getLocalMoments());
  const [showTitleInput, setShowTitleInput] = useState(false);
  const [title, setTitle] = useState('');
  const [geoConsent, setGeoConsent] = useState(false);

  // Media v1.1
  const [mediaFile, setMediaFile] = useState(null);
  const [mediaPreview, setMediaPreview] = useState(null); // objectURL for image
  const photoInputRef = useRef(null);
  const audioInputRef = useRef(null);

  useEffect(() => { getSession(); }, []);
  useEffect(() => {
    // Cleanup blob URL au démontage / changement
    return () => { if (mediaPreview) URL.revokeObjectURL(mediaPreview); };
  }, [mediaPreview]);

  const captureGeo = () => new Promise((resolve) => {
    if (!navigator.geolocation || !geoConsent) return resolve(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({
        lat: Math.round(pos.coords.latitude * 10000) / 10000,
        lon: Math.round(pos.coords.longitude * 10000) / 10000,
        accuracy_m: Math.round(pos.coords.accuracy),
      }),
      () => resolve(null),
      { timeout: 3000, maximumAge: 60000 }
    );
  });

  const onSelectFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > MAX_MEDIA_BYTES) {
      setError(`Fichier trop lourd (max ${Math.floor(MAX_MEDIA_BYTES / (1024 * 1024))} Mo)`);
      e.target.value = '';
      return;
    }
    setError('');
    if (mediaPreview) URL.revokeObjectURL(mediaPreview);
    setMediaFile(f);
    setMediaPreview(f.type.startsWith('image/') ? URL.createObjectURL(f) : null);
  };

  const clearMedia = () => {
    if (mediaPreview) URL.revokeObjectURL(mediaPreview);
    setMediaFile(null);
    setMediaPreview(null);
    if (photoInputRef.current) photoInputRef.current.value = '';
    if (audioInputRef.current) audioInputRef.current.value = '';
  };

  const sign = async ({ store = false } = {}) => {
    setPhase('signing'); setError('');
    const geo = await captureGeo();
    const session_id = getSession();
    try {
      let res;
      const identityToken = localStorage.getItem('frek_identity_token');
      const authHeaders = identityToken ? { 'X-FREK-Session': identityToken } : {};
      if (mediaFile) {
        const fd = new FormData();
        fd.append('file', mediaFile);
        fd.append('store', store ? 'true' : 'false');
        if (title.trim()) fd.append('title', title.trim());
        if (geo) fd.append('geo', JSON.stringify(geo));
        fd.append('session_id', session_id);
        res = await fetch(`${API}/api/v1/moment/sign-media`, { method: 'POST', body: fd, headers: authHeaders });
      } else {
        res = await fetch(`${API}/api/v1/moment/sign`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...authHeaders },
          body: JSON.stringify({ title: title.trim() || null, geo, session_id }),
        });
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
      saveLocalMoment(data);
      setLocalMoments(getLocalMoments());
      setPhase('done');
    } catch (e) {
      setError(e.message || 'Erreur reseau. Reessaye.');
      setPhase('error');
    }
  };

  const reset = () => {
    setPhase('idle'); setResult(null); setTitle('');
    setShowTitleInput(false); setError('');
    clearMedia();
  };

  const container = { hidden: {}, show: { transition: { staggerChildren: 0.12, delayChildren: 0.1 } } };
  const item = {
    hidden: { opacity: 0, y: 24, filter: 'blur(8px)' },
    show: {
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      transition: {
        type: 'spring',
        stiffness: 90,
        damping: 18,
        mass: 0.9,
      },
    },
  };
  const heroReveal = {
    hidden: { opacity: 0, y: 40, filter: 'blur(14px)', letterSpacing: '0.05em' },
    show: {
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      letterSpacing: '-0.04em',
      transition: { duration: 1.05, ease: [0.16, 1, 0.3, 1] },
    },
  };

  const hasMedia = !!mediaFile;
  const mediaKind = mediaFile?.type.startsWith('image/') ? 'image' : mediaFile?.type.startsWith('audio/') ? 'audio' : null;

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 flex flex-col overflow-hidden">
      <ParticleField />

      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 p-6 flex justify-between items-center"
      >
        <BrandLogo to="/universe" testId="moment-brand" />
        <nav className="flex gap-6 text-sm text-slate-600">
          {[
            { to: '/universe', label: 'Univers', tid: 'link-universe' },
            { to: '/manifeste', label: 'Manifeste', tid: 'link-manifesto' },
            { to: '/spec', label: 'Spec', tid: 'link-spec' },
            { to: '/explorer', label: 'Explorer', tid: 'link-explorer' },
          ].map((l) => (
            <Link
              key={l.to} to={l.to}
              className="relative group transition-colors hover:text-blue-600"
              data-testid={l.tid}
            >
              {l.label}
              <span className="absolute -bottom-1 left-0 w-0 h-px bg-blue-600 transition-all duration-300 group-hover:w-full" />
            </Link>
          ))}
        </nav>
      </motion.header>

      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 py-12">
        <AnimatePresence mode="wait">
          {phase === 'idle' && (
            <motion.div
              key="idle"
              variants={container}
              initial="hidden" animate="show"
              exit={{ opacity: 0, y: -30, filter: 'blur(12px)', scale: 0.96, transition: { duration: 0.5, ease: [0.65, 0, 0.35, 1] } }}
              className="text-center max-w-2xl w-full"
            >
              <motion.h1
                variants={heroReveal}
                className="text-6xl md:text-8xl font-black tracking-tighter text-slate-900 mb-6"
                data-testid="moment-headline"
              >
                Signe ce moment.
              </motion.h1>
              <motion.p variants={item} className="text-base md:text-lg text-slate-600 mb-12 font-light tracking-wide">
                Un geste. Une preuve. Notariée sur Bitcoin. Vérifiable à vie.
              </motion.p>

              {/* Sélecteurs media */}
              <motion.div variants={item} className="mb-10">
                <AnimatePresence mode="wait">
                  {!hasMedia ? (
                    <motion.div
                      key="pickers"
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      className="flex flex-wrap justify-center gap-3"
                    >
                      <button
                        onClick={() => photoInputRef.current?.click()}
                        className="px-5 py-2.5 bg-white/60 backdrop-blur border border-slate-300 text-slate-700 rounded-full text-sm hover:bg-white hover:border-blue-400 transition-all"
                        data-testid="moment-pick-photo"
                      >
                        + Photo
                      </button>
                      <button
                        onClick={() => audioInputRef.current?.click()}
                        className="px-5 py-2.5 bg-white/60 backdrop-blur border border-slate-300 text-slate-700 rounded-full text-sm hover:bg-white hover:border-blue-400 transition-all"
                        data-testid="moment-pick-audio"
                      >
                        + Son
                      </button>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="preview"
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      className="inline-flex items-center gap-4 bg-white/70 backdrop-blur-xl border border-white/50 rounded-2xl p-3 pr-5 shadow-lg"
                      data-testid="moment-media-preview"
                    >
                      {mediaKind === 'image' && mediaPreview ? (
                        <img
                          src={mediaPreview}
                          alt="Aperçu"
                          className="w-16 h-16 object-cover rounded-xl"
                          data-testid="moment-media-thumb-image"
                        />
                      ) : (
                        <div
                          className="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center"
                          data-testid="moment-media-thumb-audio"
                        >
                          <svg className="w-7 h-7 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                              d="M9 19V6l12-3v13M9 19a3 3 0 11-6 0 3 3 0 016 0zm12-3a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                        </div>
                      )}
                      <div className="text-left">
                        <div className="text-sm text-slate-900 font-medium truncate max-w-[180px]">
                          {mediaFile.name}
                        </div>
                        <div className="text-xs text-slate-500">
                          {(mediaFile.size / 1024).toFixed(1)} Ko · {mediaKind === 'image' ? 'Photo' : 'Audio'}
                        </div>
                      </div>
                      <button
                        onClick={clearMedia}
                        className="text-slate-400 hover:text-slate-900 transition-colors text-xl leading-none"
                        aria-label="Retirer le fichier"
                        data-testid="moment-clear-media"
                      >
                        ×
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Inputs cachés */}
                <input
                  ref={photoInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={onSelectFile}
                  data-testid="moment-input-photo"
                />
                <input
                  ref={audioInputRef}
                  type="file"
                  accept="audio/*"
                  className="hidden"
                  onChange={onSelectFile}
                  data-testid="moment-input-audio"
                />
              </motion.div>

              {/* Bouton(s) de signature */}
              <motion.div variants={item} className="relative inline-block">
                <motion.div
                  aria-hidden="true"
                  className="absolute inset-0 rounded-full bg-blue-500 blur-3xl opacity-25"
                  animate={{ scale: [1, 1.25, 1], opacity: [0.2, 0.45, 0.2], rotate: [0, 8, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                />
                <motion.div
                  aria-hidden="true"
                  className="absolute inset-0 rounded-full border border-blue-300/40"
                  animate={{ scale: [1, 1.4, 1.4], opacity: [0.6, 0, 0] }}
                  transition={{ duration: 3.2, repeat: Infinity, ease: 'easeOut' }}
                />
                {!hasMedia ? (
                  <motion.button
                    onClick={() => sign({ store: false })}
                    whileHover={{
                      scale: 1.06,
                      boxShadow: '0 40px 80px -20px rgba(15, 23, 42, 0.55), 0 0 0 8px rgba(59,130,246,0.08)',
                      y: -3,
                    }}
                    whileTap={{ scale: 0.94, y: 1 }}
                    transition={{ type: 'spring', stiffness: 320, damping: 18, mass: 0.7 }}
                    className="relative px-20 py-8 bg-slate-900 text-white text-2xl font-black tracking-[0.2em] rounded-full shadow-2xl"
                    data-testid="moment-sign-btn"
                  >
                    SIGNER
                  </motion.button>
                ) : (
                  <div className="relative flex flex-col sm:flex-row gap-3 items-center justify-center">
                    <motion.button
                      onClick={() => sign({ store: false })}
                      whileHover={{ scale: 1.05, y: -2 }}
                      whileTap={{ scale: 0.95 }}
                      transition={{ type: 'spring', stiffness: 380, damping: 22 }}
                      className="px-7 py-4 bg-white/70 backdrop-blur border border-slate-300 text-slate-900 rounded-full font-semibold hover:bg-white transition-all"
                      data-testid="moment-sign-hash-only"
                    >
                      Signer seul<span className="text-slate-500 font-normal"> · hash uniquement</span>
                    </motion.button>
                    <motion.button
                      onClick={() => sign({ store: true })}
                      whileHover={{ scale: 1.05, boxShadow: '0 25px 50px -12px rgba(15, 23, 42, 0.4)' }}
                      whileTap={{ scale: 0.95 }}
                      className="relative px-7 py-4 bg-slate-900 text-white rounded-full font-semibold shadow-xl"
                      data-testid="moment-sign-and-keep"
                    >
                      Signer et conserver
                    </motion.button>
                  </div>
                )}
              </motion.div>

              {hasMedia && (
                <motion.p
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="text-xs text-slate-500 mt-4 max-w-md mx-auto"
                  data-testid="moment-media-explainer"
                >
                  <b className="text-slate-700">Signer seul</b> : seul le hash cryptographique est notarié — ton fichier reste chez toi.<br />
                  <b className="text-slate-700">Signer et conserver</b> : hash + fichier chiffré stocké, récupérable via ta preuve.
                </motion.p>
              )}

              <motion.div variants={item} className="mt-12 flex flex-col items-center gap-3 text-sm text-slate-500">
                <AnimatePresence mode="wait">
                  {!showTitleInput ? (
                    <motion.button
                      key="add"
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      onClick={() => setShowTitleInput(true)}
                      className="text-slate-500 hover:text-slate-900 underline underline-offset-4 transition-colors"
                      data-testid="moment-add-title"
                    >
                      + Ajouter un titre (optionnel)
                    </motion.button>
                  ) : (
                    <motion.input
                      key="input"
                      initial={{ opacity: 0, width: 200 }}
                      animate={{ opacity: 1, width: 320 }}
                      exit={{ opacity: 0 }}
                      type="text" value={title} onChange={(e) => setTitle(e.target.value)}
                      placeholder="Ex : coucher de soleil, concert, réunion..."
                      className="px-4 py-2 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                      maxLength={200} autoFocus
                      data-testid="moment-title-input"
                    />
                  )}
                </AnimatePresence>
                <label className="flex items-center gap-2 cursor-pointer hover:text-slate-900 transition-colors" data-testid="moment-geo-toggle">
                  <input type="checkbox" checked={geoConsent} onChange={(e) => setGeoConsent(e.target.checked)} className="w-4 h-4 accent-blue-600" />
                  <span>Autoriser la localisation (H3, précision 10m)</span>
                </label>
              </motion.div>

              {error && (
                <motion.p
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="text-red-600 text-sm mt-4"
                  data-testid="moment-inline-error"
                >
                  {error}
                </motion.p>
              )}

              {localMoments.length > 0 && (
                <motion.div variants={item} className="mt-16 text-sm text-slate-500" data-testid="moment-history-hint">
                  Tu as déjà signé {localMoments.length} moment{localMoments.length > 1 ? 's' : ''} depuis ce navigateur.{' '}
                  <Link to="/mine" className="text-blue-600 hover:underline font-semibold" data-testid="link-mine">
                    Voir ton univers →
                  </Link>
                </motion.div>
              )}
            </motion.div>
          )}

          {phase === 'signing' && (
            <motion.div
              key="signing"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
              transition={{ duration: 0.4 }}
              className="text-center"
              data-testid="moment-signing"
            >
              <div className="relative w-32 h-32 mx-auto mb-8">
                {[0, 0.3, 0.6].map((delay, i) => (
                  <motion.div
                    key={i}
                    className="absolute inset-0 rounded-full border-2 border-slate-900"
                    animate={{ scale: [1, 1.5, 1.5], opacity: [0.6, 0, 0] }}
                    transition={{ duration: 1.8, delay, repeat: Infinity, ease: 'easeOut' }}
                  />
                ))}
                <motion.div
                  className="absolute inset-4 rounded-full border-4 border-slate-900 border-t-transparent"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
                />
              </div>
              <motion.p
                className="text-xl text-slate-900 font-semibold"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.8, repeat: Infinity }}
              >
                Signature en cours…
              </motion.p>
              <p className="text-sm text-slate-500 mt-3 tracking-wider">
                Notarisation Bitcoin  ·  Signature Ed25519
              </p>
            </motion.div>
          )}

          {phase === 'done' && result && (
            <motion.div
              key="done"
              variants={container}
              initial="hidden" animate="show"
              exit={{ opacity: 0, y: -20 }}
              className="text-center max-w-2xl w-full"
              data-testid="moment-done"
            >
              <motion.div
                variants={item}
                className="text-7xl mb-4 inline-block text-blue-600"
                initial={{ scale: 0, rotate: -180, opacity: 0 }}
                animate={{
                  scale: [0, 1.35, 1],
                  rotate: [-180, 15, 0],
                  opacity: 1,
                }}
                transition={{ duration: 0.9, times: [0, 0.6, 1], ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
              >
                ✓
              </motion.div>
              <motion.h2 variants={item} className="text-4xl md:text-5xl font-black text-slate-900 mb-2 tracking-tighter">
                Ton moment est signé.
              </motion.h2>
              <motion.p variants={item} className="text-xs text-slate-400 font-mono mb-10">#{result.frek_id}</motion.p>

              <motion.div
                variants={item}
                className="bg-white/60 backdrop-blur-xl border border-white/40 rounded-3xl p-8 text-left space-y-5 mb-10 shadow-xl"
              >
                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-1">Signé à</div>
                  <div className="text-slate-900 text-sm font-mono">
                    {new Date(result.created_at).toLocaleString('fr-FR', { dateStyle: 'full', timeStyle: 'medium' })}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-1">Block FREK-Chain</div>
                  <div className="text-slate-900 font-mono text-xs break-all">
                    {result.block_hash || 'En cours de notarisation…'}
                  </div>
                </div>
                {result.media_hash && (
                  <div data-testid="moment-media-hash-block">
                    <div className="text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-1">
                      Empreinte {result.media_kind === 'image' ? 'photo' : 'audio'}
                    </div>
                    <div className="text-slate-900 font-mono text-xs break-all">{result.media_hash}</div>
                    <div className="text-[10px] text-slate-500 mt-1">
                      {result.media_stored
                        ? 'Fichier chiffré conservé · récupérable via ta preuve'
                        : 'Hash uniquement · ton fichier reste chez toi'}
                    </div>
                  </div>
                )}
                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-2">Couches capturées</div>
                  <div className="flex flex-wrap gap-2">
                    {result.layers_captured.map((l, idx) => (
                      <motion.span
                        key={l}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.5 + idx * 0.08 }}
                        className="px-3 py-1 bg-gradient-to-r from-blue-100 to-blue-50 text-blue-700 rounded-full text-xs font-medium border border-blue-200/50"
                      >
                        {l}
                      </motion.span>
                    ))}
                  </div>
                </div>
              </motion.div>

              <motion.div variants={item} className="flex flex-wrap justify-center gap-3">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link
                    to={`/verify/${result.frek_id}`}
                    className="inline-block px-7 py-3 bg-slate-900 text-white rounded-full font-semibold shadow-lg hover:shadow-xl transition-shadow"
                    data-testid="moment-see-proof"
                  >
                    Voir la preuve
                  </Link>
                </motion.div>
                {result.block_hash && (
                  <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Link
                      to={result.proof_url}
                      className="inline-block px-7 py-3 bg-white/70 backdrop-blur border border-slate-300 text-slate-900 rounded-full font-semibold hover:bg-white transition-colors"
                      data-testid="moment-see-block"
                    >
                      Explorer le block
                    </Link>
                  </motion.div>
                )}
                <motion.button
                  whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                  onClick={reset}
                  className="px-7 py-3 bg-blue-600 text-white rounded-full font-semibold shadow-lg hover:bg-blue-700 transition-colors"
                  data-testid="moment-sign-another"
                >
                  Signer un autre moment
                </motion.button>
              </motion.div>

              <motion.p variants={item} className="text-xs text-slate-400 mt-10 leading-relaxed" data-testid="moment-anonymous-notice">
                Ce moment est anonyme. Il vit dans ce navigateur.
                <br />
                Pour le conserver sur tous tes appareils, associe une identité plus tard.
              </motion.p>
            </motion.div>
          )}

          {phase === 'error' && (
            <motion.div
              key="error"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: [0, -8, 8, -8, 8, 0] }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center max-w-md"
              data-testid="moment-error"
            >
              <div className="text-5xl mb-4">⚠</div>
              <p className="text-slate-900 font-semibold mb-2">{error}</p>
              <motion.button
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={reset}
                className="mt-6 px-7 py-3 bg-slate-900 text-white rounded-full font-semibold hover:bg-slate-700"
                data-testid="moment-retry"
              >
                Réessayer
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <motion.footer
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.2, duration: 1 }}
        className="relative z-10 p-6 text-center text-xs text-slate-400"
      >
        FREKCORE — Infrastructure de preuve culturelle • <Link to="/spec" className="hover:text-slate-600 transition-colors">v1.0</Link>
      </motion.footer>
    </div>
  );
}
