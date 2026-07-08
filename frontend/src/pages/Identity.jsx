import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import BrandLogo from '../components/BrandLogo';

/**
 * FREKCORE Identity — Passkey attache au FREK-ID.
 *
 * Etats :
 *   1. Anonyme : "Votre univers existe" — bouton "Protéger votre univers"
 *   2. Ceremony en cours
 *   3. Protege : "Votre identité FREK est maintenant protégée."
 *
 * Doctrine : FREKCORE ne cree pas des comptes. FREKCORE protege des identites culturelles.
 */

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = 'frek_moment_session';
const IDENTITY_TOKEN_KEY = 'frek_identity_token';
const IDENTITY_ID_KEY = 'frek_identity_id';

// Base64URL <-> ArrayBuffer helpers pour WebAuthn
function b64urlToBuf(b64) {
  const pad = '='.repeat((4 - (b64.length % 4)) % 4);
  const bin = atob((b64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
}
function bufToB64url(buf) {
  const bytes = new Uint8Array(buf);
  let bin = '';
  for (let i = 0; i < bytes.byteLength; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function toPubKeyOptions(json) {
  return {
    ...json,
    challenge: b64urlToBuf(json.challenge),
    user: json.user ? { ...json.user, id: b64urlToBuf(json.user.id) } : undefined,
    excludeCredentials: (json.excludeCredentials || []).map((c) => ({ ...c, id: b64urlToBuf(c.id) })),
    allowCredentials: (json.allowCredentials || []).map((c) => ({ ...c, id: b64urlToBuf(c.id) })),
  };
}
function serializeCredential(cred) {
  const r = cred.response;
  const base = {
    id: cred.id,
    rawId: bufToB64url(cred.rawId),
    type: cred.type,
    authenticatorAttachment: cred.authenticatorAttachment,
  };
  if (r.attestationObject) {
    return {
      ...base,
      response: {
        clientDataJSON: bufToB64url(r.clientDataJSON),
        attestationObject: bufToB64url(r.attestationObject),
        transports: typeof r.getTransports === 'function' ? r.getTransports() : [],
      },
    };
  }
  return {
    ...base,
    response: {
      clientDataJSON: bufToB64url(r.clientDataJSON),
      authenticatorData: bufToB64url(r.authenticatorData),
      signature: bufToB64url(r.signature),
      userHandle: r.userHandle ? bufToB64url(r.userHandle) : null,
    },
  };
}

export default function Identity() {
  const [identity, setIdentity] = useState(null);
  const [phase, setPhase] = useState('loading'); // loading | anonymous | ceremony | protected | error
  const [error, setError] = useState('');
  const [linkedMoments, setLinkedMoments] = useState(0);
  const webauthnSupported = typeof window !== 'undefined' &&
    window.PublicKeyCredential !== undefined;
  // Detection iframe : WebAuthn est bloque dans les iframes cross-origin
  // (cas de la preview Emergent embarquee dans app.emergent.sh).
  const inIframe = typeof window !== 'undefined' && (() => {
    try { return window.self !== window.top; } catch { return true; }
  })();
  const currentOrigin = typeof window !== 'undefined' ? window.location.origin : '';
  const backendOrigin = (API || '').replace(/\/$/, '');
  const originMismatch = currentOrigin && backendOrigin && currentOrigin !== backendOrigin;

  const openInNewTab = () => {
    const url = backendOrigin
      ? `${backendOrigin}${window.location.pathname}`
      : window.location.href;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const loadCurrent = useCallback(async () => {
    const token = localStorage.getItem(IDENTITY_TOKEN_KEY);
    if (token) {
      try {
        const res = await fetch(`${API}/api/v1/identity/me`, {
          headers: { 'X-FREK-Session': token },
        });
        if (res.ok) {
          const data = await res.json();
          setIdentity(data);
          setPhase('protected');
          return;
        }
      } catch { /* ignore */ }
    }
    // Pas de session -> initialise une identite anonyme liee au session_id local
    const sessionId = localStorage.getItem(SESSION_KEY);
    try {
      const res = await fetch(`${API}/api/v1/identity/init`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          identity_type: 'individual',
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setIdentity(data);
      setLinkedMoments(data.linked_moments_count || 0);
      localStorage.setItem(IDENTITY_ID_KEY, data.frek_id);
      setPhase('anonymous');
    } catch (e) {
      setError(e.message || 'Erreur');
      setPhase('error');
    }
  }, []);

  useEffect(() => { loadCurrent(); }, [loadCurrent]);

  const register = async () => {
    setError('');
    if (!webauthnSupported) {
      setError('Ce navigateur ne supporte pas WebAuthn. Utilisez Safari, Chrome, Firefox ou Edge à jour.');
      return;
    }
    if (inIframe) {
      setError('Passkey bloquée par le cadre de prévisualisation. Ouvrez FREKCORE dans un nouvel onglet pour associer une Passkey.');
      return;
    }
    if (originMismatch) {
      setError(`Domaine incohérent (${currentOrigin} vs ${backendOrigin}). Ouvrez FREKCORE dans un nouvel onglet sur le bon domaine.`);
      return;
    }
    // Verif pre-ceremony : le device a-t-il un authenticator utilisable ?
    try {
      if (typeof PublicKeyCredential !== 'undefined' && typeof PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable === 'function') {
        const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
        if (!available) {
          setError('Aucun authentificateur biométrique détecté sur ce device. Activez Touch ID / Face ID / Windows Hello, ou utilisez une clé de sécurité USB, puis réessayez.');
          return;
        }
      }
    } catch { /* isUVPAA optional */ }
    if (!identity?.frek_id) {
      setError('Aucun FREK-ID chargé. Rechargez la page ou revenez à /universe.');
      return;
    }
    setPhase('ceremony');
    try {
      const optsRes = await fetch(`${API}/api/v1/identity/${identity.frek_id}/register/begin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!optsRes.ok) throw new Error(`Impossible de récupérer les options WebAuthn (begin ${optsRes.status})`);
      const opts = await optsRes.json();
      let cred;
      try {
        cred = await navigator.credentials.create({ publicKey: toPubKeyOptions(opts) });
      } catch (err) {
        // Message dedie selon la cause reelle du NotAllowedError
        const name = err?.name || 'Error';
        if (name === 'NotAllowedError') {
          throw new Error('Passkey refusée par le device — soit annulée, soit le navigateur n\u2019a pas trouvé d\u2019authentificateur utilisable. Vérifiez que Touch ID / Face ID / Windows Hello est actif, puis relancez.');
        }
        if (name === 'InvalidStateError') {
          throw new Error('Une Passkey existe déjà pour ce FREK-ID sur ce device. Utilisez "Retrouver votre univers" à la place.');
        }
        if (name === 'SecurityError') {
          throw new Error(`Erreur de sécurité WebAuthn — domaine ou origine incompatible (rpId doit correspondre à ${backendOrigin}).`);
        }
        throw new Error(`${name}: ${err?.message || 'erreur ceremony inconnue'}`);
      }
      if (!cred) throw new Error('Aucune credential renvoyée par le navigateur.');
      const serialized = serializeCredential(cred);
      const completeRes = await fetch(`${API}/api/v1/identity/${identity.frek_id}/register/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: serialized }),
      });
      if (!completeRes.ok) {
        const err = await completeRes.json().catch(() => ({}));
        throw new Error(err.detail || `Backend a refusé la Passkey (complete ${completeRes.status})`);
      }
      const data = await completeRes.json();
      localStorage.setItem(IDENTITY_TOKEN_KEY, data.session_token);
      setIdentity(data.identity);
      setPhase('protected');
    } catch (e) {
      setError(e.message || 'Erreur inconnue lors de la création de la Passkey.');
      setPhase('anonymous');
    }
  };

  const authenticate = async () => {
    setError('');
    if (!webauthnSupported) {
      setError('Ce navigateur ne supporte pas WebAuthn.');
      return;
    }
    if (inIframe) {
      setError('Passkey bloquée par le cadre de prévisualisation. Ouvrez FREKCORE dans un nouvel onglet.');
      return;
    }
    if (originMismatch) {
      setError(`Domaine incohérent (${currentOrigin} vs ${backendOrigin}). Ouvrez FREKCORE dans un nouvel onglet sur le bon domaine.`);
      return;
    }
    setPhase('ceremony');
    try {
      const optsRes = await fetch(`${API}/api/v1/identity/authenticate/begin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!optsRes.ok) throw new Error(`Impossible de récupérer les options d\u2019authentification (begin ${optsRes.status})`);
      const opts = await optsRes.json();
      let cred;
      try {
        cred = await navigator.credentials.get({ publicKey: toPubKeyOptions(opts) });
      } catch (err) {
        const name = err?.name || 'Error';
        if (name === 'NotAllowedError') {
          throw new Error('Aucune Passkey FREK trouvée sur ce device, ou requête annulée. Créez d\u2019abord votre univers depuis un appareil où la Passkey est enregistrée.');
        }
        throw new Error(`${name}: ${err?.message || 'erreur ceremony inconnue'}`);
      }
      if (!cred) throw new Error('Aucune credential renvoyée par le navigateur.');
      const serialized = serializeCredential(cred);
      const completeRes = await fetch(`${API}/api/v1/identity/authenticate/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: serialized }),
      });
      if (!completeRes.ok) {
        const err = await completeRes.json().catch(() => ({}));
        throw new Error(err.detail || `Backend a refusé l\u2019authentification (complete ${completeRes.status})`);
      }
      const data = await completeRes.json();
      localStorage.setItem(IDENTITY_TOKEN_KEY, data.session_token);
      setIdentity(data.identity);
      setPhase('protected');
    } catch (e) {
      setError(e.message || 'Impossible de retrouver la Passkey.');
      setPhase('anonymous');
    }
  };

  const signOut = () => {
    localStorage.removeItem(IDENTITY_TOKEN_KEY);
    setIdentity(null);
    setPhase('anonymous');
    loadCurrent();
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 flex flex-col overflow-hidden">
      <motion.header
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative z-10 p-6 flex justify-between items-center max-w-5xl mx-auto w-full"
      >
        <BrandLogo to="/universe" testId="identity-brand" />
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/universe" className="hover:text-blue-600 transition-colors" data-testid="identity-link-universe">Univers</Link>
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="identity-link-sign">Signer</Link>
          <Link to="/mine" className="hover:text-blue-600 transition-colors" data-testid="identity-link-mine">Mon univers</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="identity-link-spec">Charte</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 flex-1 max-w-2xl mx-auto w-full px-6 py-12">
        {(inIframe || originMismatch) && phase !== 'protected' && (
          <motion.div
            initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
            className="mb-8 bg-amber-50 border border-amber-300 rounded-2xl p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4"
            data-testid="identity-iframe-warning"
          >
            <div className="flex-1 min-w-0">
              <div className="text-amber-900 font-bold text-sm mb-1">
                {inIframe ? 'Passkey bloquée dans ce cadre' : 'Domaine incohérent'}
              </div>
              <div className="text-amber-800 text-xs leading-relaxed">
                {inIframe
                  ? 'Les navigateurs interdisent WebAuthn dans une prévisualisation intégrée. Ouvrez FREKCORE dans un nouvel onglet pour associer une Passkey en une seconde.'
                  : `Votre onglet est sur ${currentOrigin} mais l'API est sur ${backendOrigin}. Passez sur le bon domaine avant d'associer une Passkey.`}
              </div>
            </div>
            <button
              onClick={openInNewTab}
              className="shrink-0 px-4 py-2 bg-amber-600 text-white rounded-full text-xs font-semibold hover:bg-amber-700 transition-colors"
              data-testid="identity-open-new-tab"
            >
              Ouvrir dans un nouvel onglet →
            </button>
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          {phase === 'loading' && (
            <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="text-center py-20" data-testid="identity-loading">
              <div className="w-10 h-10 mx-auto border-2 border-slate-200 border-t-blue-600 rounded-full animate-spin" />
            </motion.div>
          )}

          {phase === 'anonymous' && identity && (
            <motion.div key="anon"
              initial={{ opacity: 0, y: 24, filter: 'blur(8px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0, y: -12, filter: 'blur(8px)' }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              data-testid="identity-anonymous"
            >
              <div className="text-xs text-slate-500 uppercase tracking-[0.3em] mb-3">FREK Identity</div>
              <h1 className="text-5xl md:text-6xl font-black tracking-tighter text-slate-900 leading-tight mb-4">
                Votre univers existe.
              </h1>
              <p className="text-lg text-slate-600 mb-8 leading-relaxed">
                {linkedMoments > 0
                  ? `${linkedMoments} moment${linkedMoments > 1 ? 's' : ''} déjà signé${linkedMoments > 1 ? 's' : ''} depuis ce navigateur.`
                  : 'Aucun moment signé pour l\'instant, mais votre identité culturelle est prête.'}
                <br />
                <span className="text-slate-500 text-base">
                  Sans protection, il vit uniquement dans ce navigateur. Si vous videz le cache, tout disparaît côté client — les preuves, elles, restent ancrées.
                </span>
              </p>

              <div className="bg-white/70 backdrop-blur-xl border border-white/50 rounded-3xl p-6 mb-6 shadow-xl">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-2">Votre FREK Identity</div>
                <div className="text-slate-900 font-mono text-sm break-all mb-3" data-testid="identity-frek-id">
                  {identity.frek_id}
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  Non protégée
                </div>
              </div>

              <motion.button
                whileHover={{ scale: 1.03, y: -2 }}
                whileTap={{ scale: 0.97 }}
                transition={{ type: 'spring', stiffness: 340, damping: 20 }}
                onClick={register}
                disabled={!webauthnSupported}
                className="w-full px-8 py-5 bg-slate-900 text-white rounded-full font-bold shadow-xl hover:bg-slate-700 disabled:opacity-60 transition-colors"
                data-testid="identity-register-btn"
              >
                Associer une Passkey — protéger cet univers
              </motion.button>
              {!webauthnSupported && (
                <p className="text-xs text-red-600 mt-3 text-center">Ce navigateur ne supporte pas WebAuthn. Utilisez Safari, Chrome, Firefox, Edge à jour.</p>
              )}

              <div className="mt-8 pt-6 border-t border-slate-200 text-center">
                <p className="text-sm text-slate-600 mb-3">Vous avez déjà une Passkey FREK sur un autre appareil ?</p>
                <button
                  onClick={authenticate}
                  disabled={!webauthnSupported}
                  className="text-blue-600 hover:underline font-semibold text-sm disabled:opacity-60"
                  data-testid="identity-recover-btn"
                >
                  Retrouver votre univers →
                </button>
              </div>

              {error && (
                <p className="text-red-600 text-sm mt-4 text-center" data-testid="identity-error">{error}</p>
              )}
            </motion.div>
          )}

          {phase === 'ceremony' && (
            <motion.div key="ceremony"
              initial={{ opacity: 0, scale: 0.9, filter: 'blur(16px)' }}
              animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
              exit={{ opacity: 0, scale: 1.05, filter: 'blur(16px)' }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="text-center py-20"
              data-testid="identity-ceremony"
            >
              <div className="relative w-32 h-32 mx-auto mb-8">
                {[0, 0.3, 0.6].map((delay, i) => (
                  <motion.div key={i}
                    className="absolute inset-0 rounded-full border-2 border-blue-600"
                    animate={{ scale: [1, 1.6, 1.6], opacity: [0.6, 0, 0] }}
                    transition={{ duration: 2, delay, repeat: Infinity, ease: 'easeOut' }}
                  />
                ))}
                <motion.div
                  className="absolute inset-6 rounded-full border-4 border-slate-900 border-t-transparent"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
                />
              </div>
              <p className="text-xl text-slate-900 font-semibold">Autorise sur ton appareil…</p>
              <p className="text-sm text-slate-500 mt-2 tracking-wide">Touch ID · Face ID · Windows Hello · Sécurité biométrique</p>
            </motion.div>
          )}

          {phase === 'protected' && identity && (
            <motion.div key="prot"
              initial={{ opacity: 0, y: 24, filter: 'blur(8px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              data-testid="identity-protected"
            >
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: [0, 1.35, 1], rotate: [-180, 12, 0] }}
                transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
                className="text-7xl text-blue-600 mb-4 inline-block"
              >
                ✓
              </motion.div>
              <h1 className="text-4xl md:text-5xl font-black tracking-tighter text-slate-900 leading-tight mb-3">
                Votre identité FREK est<br />maintenant protégée.
              </h1>
              <p className="text-base text-slate-600 mb-8 leading-relaxed">
                Cette Passkey est votre preuve de contrôle. Elle vit dans le trousseau sécurisé de votre appareil et se synchronise via votre système (iCloud Keychain, Google Password Manager…). Sur un autre appareil, vous pourrez retrouver votre univers en une pression biométrique.
              </p>

              <div className="bg-white/70 backdrop-blur-xl border border-white/50 rounded-3xl p-6 mb-6 shadow-xl space-y-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-1">FREK-ID</div>
                  <div className="text-slate-900 font-mono text-sm break-all" data-testid="identity-frek-id-protected">
                    {identity.frek_id}
                  </div>
                </div>
                <div className="flex flex-wrap gap-4 pt-2 border-t border-slate-100">
                  <div>
                    <div className="text-xs text-slate-500">Passkeys attachées</div>
                    <div className="text-slate-900 font-semibold text-lg" data-testid="identity-cred-count">{identity.credentials_count}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500">Objets liés</div>
                    <div className="text-slate-900 font-semibold text-lg" data-testid="identity-obj-count">{identity.linked_objects_count}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500">Statut</div>
                    <div className="text-blue-600 font-semibold text-sm flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-blue-500" />
                      Protégée
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap gap-3 justify-center">
                <Link to="/mine"
                  className="px-6 py-3 bg-slate-900 text-white rounded-full font-semibold shadow-lg hover:bg-slate-700 transition-colors"
                  data-testid="identity-cta-mine"
                >
                  Voir mon univers →
                </Link>
                <button
                  onClick={register}
                  className="px-6 py-3 bg-white/70 border border-slate-300 text-slate-900 rounded-full font-semibold hover:bg-white transition-colors"
                  data-testid="identity-add-passkey"
                >
                  Ajouter une autre Passkey
                </button>
                <button
                  onClick={signOut}
                  className="px-6 py-3 text-slate-500 hover:text-slate-900 text-sm font-semibold transition-colors"
                  data-testid="identity-signout"
                >
                  Se déconnecter de cet appareil
                </button>
              </div>

              {error && (
                <p className="text-red-600 text-sm mt-4 text-center" data-testid="identity-error-protected">{error}</p>
              )}
            </motion.div>
          )}

          {phase === 'error' && (
            <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20" data-testid="identity-fatal-error">
              <p className="text-red-600 font-semibold mb-4">{error}</p>
              <button onClick={loadCurrent} className="px-5 py-2 bg-slate-900 text-white rounded-full text-sm">Réessayer</button>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="mt-16 text-xs text-slate-400 text-center leading-relaxed max-w-md mx-auto">
          FREKCORE ne crée pas des comptes.<br />
          FREKCORE protège des identités culturelles.
        </div>
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400">
        FREKCORE — Infrastructure de preuve culturelle
      </footer>
    </div>
  );
}
