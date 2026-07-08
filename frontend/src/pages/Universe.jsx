import { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import BrandLogo from '../components/BrandLogo';

/**
 * FREKCORE — La porte d'entrée unifiée.
 *
 * Deux journées possibles au premier affichage :
 *
 *   NOUVEL UTILISATEUR              UTILISATEUR EXISTANT
 *   ────────────────────            ────────────────────────
 *   "Créer mon univers"             "Retrouver mon univers"
 *          ↓                                 ↓
 *      FREK-ID                          Passkey
 *          ↓                                 ↓
 *   Choix du rôle                   Patrimoine existant
 *          ↓
 *   Premier objet / première preuve
 *
 * Cette page ne crée aucun endpoint nouveau. Elle orchestre les briques
 * existantes : /api/v1/identity/init, /identity/me, /identity/{id}/objects,
 * /identity/authenticate/begin+complete.
 *
 * FREK-ID reste l'identité universelle ; le "rôle" est un choix d'expérience.
 */

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = 'frek_moment_session';
const IDENTITY_TOKEN_KEY = 'frek_identity_token';
const IDENTITY_ID_KEY = 'frek_identity_id';
const PROFILE_KEY = 'frek_universe_profile';

const PROFILES = [
  {
    id: 'artiste',
    label: 'Artiste',
    tagline: 'protéger mes créations',
    identity_type: 'individual',
    detail: 'FREKCORE transforme une création numérique en objet culturel vérifiable : son identité, son histoire et son intégrité peuvent l\u2019accompagner dans le temps.',
  },
  {
    id: 'label',
    label: 'Label / Industrie musicale',
    tagline: 'connecter créateurs, œuvres et exploitants',
    identity_type: 'institution',
    detail: 'FREKCORE crée une couche de confiance entre les créateurs, les œuvres et les acteurs qui les exploitent. Chaque création peut transporter son identité, ses contributeurs et sa preuve d\u2019existence.',
  },
  {
    id: 'notaire',
    label: 'Notaire / Juriste',
    tagline: 'apporter une couche de preuve vérifiable',
    identity_type: 'professional',
    detail: 'FREKCORE fournit une attestation numérique d\u2019existence, d\u2019intégrité et d\u2019origine déclarée d\u2019un objet. Il ne remplace pas l\u2019autorité juridique, il apporte une couche de preuve vérifiable.',
  },
  {
    id: 'institution',
    label: 'Institution culturelle',
    tagline: 'préserver et transmettre',
    identity_type: 'institution',
    detail: 'FREKCORE permet de préserver et transmettre des objets culturels numériques avec leur contexte, leur histoire et leur preuve d\u2019intégrité.',
  },
  {
    id: 'developpeur',
    label: 'Développeur / Partenaire technique',
    tagline: 'créer et vérifier via une infrastructure ouverte',
    identity_type: 'professional',
    detail: 'FREKCORE fournit une infrastructure ouverte permettant de créer et vérifier des objets numériques porteurs d\u2019identité, de métadonnées, de droits et de preuves.',
  },
];

const Hero = (
  <motion.div
    initial={{ opacity: 0, y: 20, filter: 'blur(10px)' }}
    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
    transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
    className="text-center mb-14"
  >
    <p className="text-xs text-slate-500 uppercase tracking-[0.3em] mb-4">Univers FREKCORE</p>
    <h1 className="text-5xl md:text-6xl font-black tracking-tighter text-slate-900 leading-tight mb-4" data-testid="universe-headline">
      Bienvenue dans votre<br />univers FREKCORE.
    </h1>
    <p className="text-base text-slate-700 max-w-xl mx-auto leading-relaxed" data-testid="universe-subline">
      <span className="font-bold text-slate-900">FREKCORE est une infrastructure de confiance</span> qui permet de créer, protéger et transmettre des objets numériques vérifiables.
    </p>
    <p className="mt-4 text-sm text-slate-500 italic max-w-xl mx-auto leading-relaxed" data-testid="universe-rdv-phrase">
      Aujourd&apos;hui, un fichier transporte des données. FREKCORE permet aux créations numériques de transporter leur identité, leur histoire et leur preuve.
    </p>
  </motion.div>
);

function Shell({ children }) {
  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 overflow-hidden">
      <div aria-hidden="true" className="fixed inset-0 pointer-events-none">
        <motion.div
          className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.10), transparent 70%)', filter: 'blur(80px)' }}
          animate={{ scale: [1, 1.12, 1], opacity: [0.5, 0.85, 0.5] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute bottom-0 right-0 w-[600px] h-[600px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(147,197,253,0.12), transparent 70%)', filter: 'blur(90px)' }}
          animate={{ x: [-30, 30, -30] }}
          transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>
      <motion.header
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative z-10 p-6 flex justify-between items-center max-w-5xl mx-auto"
      >
        <BrandLogo to="/universe" testId="universe-brand" />
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="universe-link-sign">Signer</Link>
          <Link to="/mine" className="hover:text-blue-600 transition-colors" data-testid="universe-link-mine">Mon univers</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="universe-link-spec">Charte</Link>
        </nav>
      </motion.header>
      <main className="relative z-10 max-w-3xl mx-auto px-6 py-12">
        {children}
      </main>
      <footer className="relative z-10 p-6 text-center text-xs text-slate-400" data-testid="universe-legal-notice">
        FREKCORE atteste l&apos;existence, l&apos;intégrité et l&apos;origine déclarée d&apos;un objet numérique.
      </footer>
    </div>
  );
}

// Modes de la page :
//   'entrance' — 2 grandes cartes : créer OU retrouver
//   'create'   — parcours nouveau (FREK-ID + rôle + premier objet)
//   'resume'   — parcours existant (résumé patrimoine + accès rapide)
export default function Universe() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('loading');
  const [identity, setIdentity] = useState(null);
  const [protectedIdentity, setProtectedIdentity] = useState(false);
  const [stats, setStats] = useState({ moments: 0, fk: 0 });
  const [profile, setProfile] = useState(() => {
    try { return JSON.parse(localStorage.getItem(PROFILE_KEY) || 'null'); } catch { return null; }
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  // Detection iframe (WebAuthn refuse dans les iframes cross-origin comme Emergent preview).
  const inIframe = typeof window !== 'undefined' && (() => {
    try { return window.self !== window.top; } catch { return true; }
  })();
  const backendOrigin = (API || '').replace(/\/$/, '');
  const openInNewTab = () => {
    const url = backendOrigin
      ? `${backendOrigin}${window.location.pathname}`
      : window.location.href;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  // Detection state initial : token valide → resume ; sinon → entrance.
  const bootstrap = useCallback(async () => {
    setErr('');
    const token = localStorage.getItem(IDENTITY_TOKEN_KEY);
    if (token) {
      try {
        const meRes = await fetch(`${API}/api/v1/identity/me`, { headers: { 'X-FREK-Session': token } });
        if (meRes.ok) {
          const me = await meRes.json();
          setIdentity(me);
          setProtectedIdentity(true);
          try {
            const objRes = await fetch(`${API}/api/v1/identity/${me.frek_id}/objects`, {
              headers: { 'X-FREK-Session': token },
            });
            if (objRes.ok) {
              const data = await objRes.json();
              setStats({
                moments: (data.moments || []).length,
                fk: (data.fk_objects || []).length,
              });
            }
          } catch { /* ignore */ }
          setMode('resume');
          return;
        }
      } catch { /* fallthrough */ }
    }
    // Pas de token — mais on peut avoir un frek_id anonyme deja cree
    const existingId = localStorage.getItem(IDENTITY_ID_KEY);
    if (existingId) {
      try {
        const res = await fetch(`${API}/api/v1/identity/${existingId}`);
        if (res.ok) {
          const data = await res.json();
          setIdentity(data);
          setProtectedIdentity(false);
        }
      } catch { /* ignore */ }
    }
    setMode('entrance');
  }, []);

  useEffect(() => { bootstrap(); }, [bootstrap]);

  // Cree une FREKIdentity anonyme et bascule en mode "create"
  const startCreation = async () => {
    setBusy(true); setErr('');
    try {
      const sessionId = localStorage.getItem(SESSION_KEY);
      const res = await fetch(`${API}/api/v1/identity/init`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          identity_type: profile?.identity_type || 'individual',
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setIdentity(data);
      localStorage.setItem(IDENTITY_ID_KEY, data.frek_id);
      setMode('create');
    } catch (e) {
      setErr(e.message || 'Impossible de créer l\u2019identité.');
    } finally {
      setBusy(false);
    }
  };

  const chooseProfile = (p) => {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(p));
    setProfile(p);
  };

  const clearAll = () => {
    localStorage.removeItem(PROFILE_KEY);
    localStorage.removeItem(IDENTITY_ID_KEY);
    setProfile(null);
    setIdentity(null);
    setProtectedIdentity(false);
    setStats({ moments: 0, fk: 0 });
    setMode('entrance');
  };

  const signOut = () => {
    localStorage.removeItem(IDENTITY_TOKEN_KEY);
    bootstrap();
  };

  // Wrapper visuel commun (Shell + Hero sont définis en haut du fichier).

  // ────────── MODE : LOADING ──────────
  if (mode === 'loading') {
    return (
      <Shell>
        <div className="flex items-center justify-center py-20" data-testid="universe-loading">
          <div className="w-10 h-10 border-2 border-slate-200 border-t-blue-600 rounded-full animate-spin" />
        </div>
      </Shell>
    );
  }

  // ────────── MODE : ENTRANCE (deux journées) ──────────
  if (mode === 'entrance') {
    return (
      <Shell>
        {Hero}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.7 }}
          className="grid md:grid-cols-2 gap-5 mb-10"
          data-testid="universe-entrance"
        >
          {/* Nouvelle personne */}
          <motion.button
            whileHover={{ y: -4, boxShadow: '0 20px 40px -12px rgba(15,23,42,0.15)' }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 260, damping: 20 }}
            onClick={startCreation}
            disabled={busy}
            className="text-left bg-slate-900 text-white rounded-3xl p-7 shadow-xl transition-all disabled:opacity-70 disabled:cursor-wait"
            data-testid="universe-cta-create"
          >
            <div className="text-[10px] uppercase tracking-[0.3em] text-blue-300 mb-3">Nouvel utilisateur</div>
            <div className="text-2xl font-black tracking-tight mb-3 leading-snug">
              Créer mon univers FREKCORE
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              Générer votre FREK-ID, choisir votre rôle, signer votre première preuve.
            </p>
            <div className="mt-6 flex items-center gap-2 text-blue-300 text-sm font-semibold">
              {busy ? 'Création…' : 'Commencer'} <span aria-hidden="true">→</span>
            </div>
          </motion.button>

          {/* Utilisateur existant */}
          <motion.button
            whileHover={{ y: -4, boxShadow: '0 20px 40px -12px rgba(59,130,246,0.20)' }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 260, damping: 20 }}
            onClick={() => setMode('recover')}
            className="text-left bg-white/80 backdrop-blur-xl border border-blue-200 rounded-3xl p-7 shadow-xl transition-all"
            data-testid="universe-cta-recover"
          >
            <div className="text-[10px] uppercase tracking-[0.3em] text-blue-600 mb-3">Utilisateur existant</div>
            <div className="text-2xl font-black tracking-tight text-slate-900 mb-3 leading-snug">
              Retrouver mon univers
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">
              Utiliser votre Passkey (Touch ID / Face ID / Windows Hello) pour retrouver votre patrimoine.
            </p>
            <div className="mt-6 flex items-center gap-2 text-blue-700 text-sm font-semibold">
              Se reconnecter <span aria-hidden="true">→</span>
            </div>
          </motion.button>
        </motion.div>

        {identity && !protectedIdentity && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="text-center text-xs text-slate-500"
            data-testid="universe-anonymous-hint"
          >
            Vous avez déjà commencé une identité anonyme dans ce navigateur ({identity.frek_id.slice(0, 15)}…).{' '}
            <button onClick={() => setMode('create')} className="text-blue-600 hover:underline font-semibold" data-testid="universe-resume-draft">
              Continuer là où vous en étiez →
            </button>
          </motion.div>
        )}

        {err && (
          <p className="text-center text-red-600 text-sm mt-6" data-testid="universe-entrance-error">{err}</p>
        )}
      </Shell>
    );
  }

  // ────────── MODE : RECOVER (Passkey pour utilisateur existant) ──────────
  if (mode === 'recover') {
    const originMismatch = typeof window !== 'undefined'
      && backendOrigin && window.location.origin !== backendOrigin;
    return (
      <Shell>
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}
          data-testid="universe-recover-panel"
        >
          <button onClick={() => setMode('entrance')} className="text-sm text-slate-500 hover:text-slate-900 mb-6" data-testid="universe-recover-back">
            ← Retour
          </button>
          <p className="text-xs text-blue-600 uppercase tracking-[0.3em] mb-3">Utilisateur existant</p>
          <h2 className="text-4xl md:text-5xl font-black tracking-tighter text-slate-900 leading-tight mb-4">
            Retrouvez votre univers.
          </h2>
          <p className="text-slate-600 mb-8 max-w-xl leading-relaxed">
            Votre Passkey vit dans le trousseau sécurisé de votre appareil (iCloud Keychain, Google Password Manager, Windows Hello…). Une pression suffit pour retrouver votre patrimoine complet.
          </p>

          {(inIframe || originMismatch) && (
            <div className="mb-6 bg-amber-50 border border-amber-300 rounded-2xl p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4" data-testid="universe-iframe-warning">
              <div className="flex-1 min-w-0">
                <div className="text-amber-900 font-bold text-sm mb-1">
                  {inIframe ? 'Passkey bloquée dans ce cadre' : 'Domaine incohérent'}
                </div>
                <div className="text-amber-800 text-xs leading-relaxed">
                  {inIframe
                    ? 'Les navigateurs interdisent WebAuthn dans une prévisualisation intégrée. Ouvrez FREKCORE dans un nouvel onglet.'
                    : `Votre onglet n'est pas sur le domaine servi par l'API. Passez sur ${backendOrigin} pour continuer.`}
                </div>
              </div>
              <button onClick={openInNewTab} className="shrink-0 px-4 py-2 bg-amber-600 text-white rounded-full text-xs font-semibold hover:bg-amber-700" data-testid="universe-open-new-tab">
                Ouvrir dans un nouvel onglet →
              </button>
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            <Link
              to="/identity"
              className="px-7 py-3.5 bg-slate-900 text-white rounded-full font-semibold shadow-xl hover:bg-slate-700 transition-colors"
              data-testid="universe-recover-passkey-btn"
            >
              Utiliser ma Passkey →
            </Link>
            <button
              onClick={() => setMode('entrance')}
              className="px-7 py-3.5 bg-white/70 border border-slate-300 text-slate-700 rounded-full font-semibold hover:bg-white transition-colors"
              data-testid="universe-recover-cancel"
            >
              Annuler
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-6 max-w-xl">
            Pas encore de Passkey ? <button onClick={() => setMode('entrance')} className="text-blue-600 hover:underline">Créez d&apos;abord votre univers</button>.
          </p>
        </motion.div>
      </Shell>
    );
  }

  // ────────── MODE : RESUME (utilisateur déjà protégé) ──────────
  if (mode === 'resume' && identity) {
    return (
      <Shell>
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}
          data-testid="universe-resume-panel"
        >
          <p className="text-xs text-blue-600 uppercase tracking-[0.3em] mb-3">Votre univers</p>
          <h2 className="text-4xl md:text-5xl font-black tracking-tighter text-slate-900 leading-tight mb-3">
            Vous êtes de retour.
          </h2>
          <p className="text-slate-600 mb-8 leading-relaxed max-w-xl">
            {stats.moments + stats.fk === 0
              ? 'Votre univers est prêt mais encore vide. C\u2019est le bon moment pour signer votre premier moment ou créer votre premier objet FK.'
              : `Votre patrimoine numérique est intact. ${stats.moments} moment${stats.moments > 1 ? 's' : ''} + ${stats.fk} objet${stats.fk > 1 ? 's' : ''} FK vous attendent.`}
          </p>

          <div className="bg-white/70 backdrop-blur-xl border border-white/50 rounded-3xl p-6 mb-6 shadow-xl" data-testid="universe-resume-card">
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <div className="text-[10px] text-slate-500 uppercase tracking-[0.2em] mb-1">FREK-ID</div>
                <div className="font-mono text-xs text-slate-900 break-all" data-testid="universe-frek-id">{identity.frek_id}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase tracking-[0.2em] mb-1">Passkeys</div>
                <div className="text-slate-900 text-sm font-semibold flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-blue-600" /> {identity.credentials_count || 1} active{(identity.credentials_count || 1) > 1 ? 's' : ''}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase tracking-[0.2em] mb-1">Objets liés</div>
                <div className="text-2xl font-black text-slate-900" data-testid="universe-count-total">{stats.moments + stats.fk}</div>
              </div>
            </div>
            {profile && (
              <div className="mt-5 pt-5 border-t border-slate-100 text-sm text-slate-700">
                <span className="text-[10px] uppercase tracking-[0.2em] text-blue-600 mr-2">Rôle</span>
                {profile.label}
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-3 mb-8">
            <Link to="/mine" className="px-6 py-3 bg-slate-900 text-white rounded-full font-semibold shadow-lg hover:bg-slate-700 transition-colors" data-testid="universe-cta-mine">
              Voir mon patrimoine →
            </Link>
            <Link to="/" className="px-6 py-3 bg-white/70 border border-slate-300 text-slate-900 rounded-full font-semibold hover:bg-white transition-colors" data-testid="universe-cta-sign-again">
              Signer un moment
            </Link>
            <Link to="/fk" className="px-6 py-3 bg-white/70 border border-slate-300 text-slate-900 rounded-full font-semibold hover:bg-white transition-colors" data-testid="universe-cta-fk">
              Créer un objet FK
            </Link>
          </div>

          <div className="flex flex-wrap gap-4 text-xs">
            <Link to="/identity" className="text-blue-600 hover:underline" data-testid="universe-manage-passkey">
              Gérer mes Passkeys →
            </Link>
            <button onClick={signOut} className="text-slate-500 hover:text-slate-900" data-testid="universe-signout">
              Se déconnecter de cet appareil
            </button>
          </div>
        </motion.div>
      </Shell>
    );
  }

  // ────────── MODE : CREATE (nouveau parcours) ──────────
  return (
    <Shell>
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}
        data-testid="universe-create-panel"
      >
        <button onClick={() => setMode('entrance')} className="text-sm text-slate-500 hover:text-slate-900 mb-6" data-testid="universe-create-back">
          ← Retour
        </button>
        <p className="text-xs text-blue-600 uppercase tracking-[0.3em] mb-3">Nouvel utilisateur</p>
        <h2 className="text-4xl md:text-5xl font-black tracking-tighter text-slate-900 leading-tight mb-8">
          Créez votre univers FREKCORE.
        </h2>

        {/* Étape 1 — FREK-ID (déjà fait au start) */}
        {identity && (
          <motion.div
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            className="mb-5 bg-blue-50/70 backdrop-blur border border-blue-200 rounded-2xl p-5 flex items-center gap-4"
            data-testid="universe-create-step1"
          >
            <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-black shrink-0">✓</div>
            <div className="flex-1 min-w-0">
              <div className="text-slate-900 font-bold">1. Votre FREK-ID est créé</div>
              <div className="font-mono text-xs text-slate-600 break-all mt-0.5" data-testid="universe-create-frek-id">{identity.frek_id}</div>
            </div>
          </motion.div>
        )}

        {/* Étape 2 — Choix du rôle */}
        <motion.div
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className={`mb-5 rounded-2xl p-5 border ${profile ? 'bg-blue-50/70 border-blue-200' : 'bg-white/80 border-slate-300'}`}
          data-testid="universe-create-step2"
        >
          <div className="flex items-start gap-4 mb-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-black shrink-0 ${profile ? 'bg-blue-600 text-white' : 'bg-slate-900 text-white'}`}>
              {profile ? '✓' : '2'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-slate-900 font-bold">2. Choisissez votre rôle</div>
              <div className="text-sm text-slate-600 mt-0.5">
                {profile ? `Vous créez votre univers en tant que ${profile.label.toLowerCase()}.` : 'Ce choix personnalise votre parcours — votre FREK-ID reste unique.'}
              </div>
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-3" data-testid="universe-role-grid">
            {PROFILES.map((p) => (
              <button
                key={p.id}
                onClick={() => chooseProfile(p)}
                className={`text-left p-4 rounded-xl border-2 transition-all ${
                  profile?.id === p.id
                    ? 'border-blue-500 bg-white shadow-md'
                    : 'border-slate-200 bg-white/60 hover:border-blue-300'
                }`}
                data-testid={`universe-profile-${p.id}`}
              >
                <div className="text-slate-900 font-bold">{p.label}</div>
                <div className="text-xs text-blue-600 uppercase tracking-wide mb-1.5">{p.tagline}</div>
                <div className="text-xs text-slate-600 leading-relaxed line-clamp-3">{p.detail}</div>
              </button>
            ))}
          </div>
          {profile && (
            <p className="mt-4 text-sm text-slate-700 border-t border-blue-100 pt-4 leading-relaxed" data-testid="universe-profile-message">
              {profile.detail}
            </p>
          )}
        </motion.div>

        {/* Étape 3 — Première preuve */}
        <motion.div
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className={`mb-6 rounded-2xl p-5 border ${profile ? 'bg-white/90 border-blue-400 shadow-lg' : 'bg-white/40 border-slate-200 opacity-60'}`}
          data-testid="universe-create-step3"
        >
          <div className="flex items-start gap-4 mb-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-black shrink-0 ${profile ? 'bg-slate-900 text-white' : 'bg-slate-200 text-slate-500'}`}>
              3
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-slate-900 font-bold">3. Signez votre première preuve</div>
              <div className="text-sm text-slate-600 mt-0.5">
                Un moment signé horodaté sur Bitcoin, ou un objet culturel FK vérifiable.
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-3 pl-14">
            <Link
              to="/"
              className={`px-6 py-3 rounded-full font-semibold shadow-lg transition-colors ${
                profile ? 'bg-slate-900 text-white hover:bg-slate-700' : 'bg-slate-300 text-slate-500 pointer-events-none'
              }`}
              data-testid="universe-cta-first-moment"
            >
              Signer un moment →
            </Link>
            <Link
              to="/fk"
              className={`px-6 py-3 rounded-full font-semibold transition-colors ${
                profile ? 'bg-white border border-slate-300 text-slate-900 hover:bg-blue-50' : 'bg-slate-100 text-slate-400 pointer-events-none border border-slate-200'
              }`}
              data-testid="universe-cta-first-fk"
            >
              Créer un objet FK
            </Link>
          </div>
        </motion.div>

        {/* Étape 4 — Passkey (optionnel mais recommandé) */}
        <motion.div
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="mb-6 bg-white/60 backdrop-blur border border-slate-200 rounded-2xl p-5"
          data-testid="universe-create-step4"
        >
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center font-black shrink-0">
              4
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-slate-900 font-bold">4. Protéger — quand vous voulez</div>
              <div className="text-sm text-slate-600 mt-0.5 leading-relaxed">
                Associez une Passkey plus tard pour retrouver votre univers sur tous vos appareils. Vos preuves déjà signées restent ancrées dans tous les cas.
              </div>
              <Link
                to="/identity"
                className="inline-block mt-3 text-blue-600 text-sm font-semibold hover:underline"
                data-testid="universe-cta-passkey-later"
              >
                Associer une Passkey →
              </Link>
            </div>
          </div>
        </motion.div>

        {err && <p className="text-red-600 text-sm mb-4" data-testid="universe-create-error">{err}</p>}

        <div className="flex justify-between items-center text-xs">
          <button onClick={clearAll} className="text-slate-400 hover:text-slate-700" data-testid="universe-create-reset">
            Effacer et recommencer
          </button>
        </div>
      </motion.div>
    </Shell>
  );
}
