import { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * FREKCORE — La porte d'entrée de l'univers.
 *
 * Doctrine :
 *   Un utilisateur ne doit plus percevoir plusieurs applications séparées.
 *   Il traverse un seul parcours : Identité → Preuve → Création → Patrimoine.
 *
 * Cette page ne crée AUCUN nouveau système. Elle orchestre les briques existantes :
 *   /api/v1/identity/init          (bootstrap FREK-ID + attache session moments)
 *   /api/v1/identity/me            (état courant, protection Passkey)
 *   /api/v1/identity/{id}/objects  (moments + FK unifiés)
 *   /api/v1/moment/stats, /fk/stats (compteurs pulse)
 *
 * Le "profil d'usage" (Artiste / Institution / …) est un choix d'expérience,
 * jamais un compte séparé. FREK-ID reste l'identité universelle.
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
    detail: 'Signer chaque morceau, chaque œuvre, chaque captation. Les transformer en objets culturels vérifiables.',
  },
  {
    id: 'institution',
    label: 'Institution',
    tagline: 'préserver mon patrimoine',
    identity_type: 'institution',
    detail: 'Archiver des collections avec preuve d\'existence, d\'intégrité et d\'origine déclarée sur la durée.',
  },
  {
    id: 'professionnel',
    label: 'Professionnel',
    tagline: 'gérer mes preuves numériques',
    identity_type: 'professional',
    detail: 'Notariser des contrats, des livrables, des décisions. Vérifiables sans dépendre de FREKCORE.',
  },
  {
    id: 'organisation',
    label: 'Organisation',
    tagline: 'préparer mes usages collaboratifs',
    identity_type: 'institution',
    detail: 'Fondation posée pour des flux multi-membres. Aucune structure imposée avant qu\'un besoin réel n\'apparaisse.',
  },
  {
    id: 'personnel',
    label: 'Personnel',
    tagline: 'conserver mes moments importants',
    identity_type: 'individual',
    detail: 'Un souvenir, un instant, une preuve. Aucun compte, aucun mot de passe.',
  },
];

const STEPS = [
  { id: 1, key: 'identity', title: 'Créer ou retrouver votre FREK-ID', hint: 'Une identité culturelle souveraine, à vie.' },
  { id: 2, key: 'passkey',  title: 'Associer une Passkey',              hint: 'Touch ID, Face ID, Windows Hello — clé de contrôle.' },
  { id: 3, key: 'create',   title: 'Créer vos premiers objets',         hint: 'Un moment signé, un objet FK culturel.' },
  { id: 4, key: 'universe', title: 'Construire votre patrimoine',       hint: 'Retrouver, vérifier, transmettre.' },
];

export default function Universe() {
  const navigate = useNavigate();
  const [identity, setIdentity] = useState(null);
  const [protectedIdentity, setProtectedIdentity] = useState(false);
  const [profile, setProfile] = useState(() => {
    try { return JSON.parse(localStorage.getItem(PROFILE_KEY) || 'null'); } catch { return null; }
  });
  const [stats, setStats] = useState({ moments: 0, fk: 0 });
  const [loading, setLoading] = useState(true);
  const [showProfilePicker, setShowProfilePicker] = useState(false);

  const bootstrap = useCallback(async () => {
    setLoading(true);
    const token = localStorage.getItem(IDENTITY_TOKEN_KEY);

    // 1. Charger identité protégée (si token)
    if (token) {
      try {
        const meRes = await fetch(`${API}/api/v1/identity/me`, { headers: { 'X-FREK-Session': token } });
        if (meRes.ok) {
          const me = await meRes.json();
          setIdentity(me);
          setProtectedIdentity(true);
          // Compter objets
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
          setLoading(false);
          return;
        }
      } catch { /* fallback */ }
    }

    // 2. Sinon : identité anonyme rattachée à la session moment
    const sessionId = localStorage.getItem(SESSION_KEY);
    const existingId = localStorage.getItem(IDENTITY_ID_KEY);
    if (existingId) {
      try {
        const res = await fetch(`${API}/api/v1/identity/${existingId}`);
        if (res.ok) {
          const data = await res.json();
          setIdentity(data);
          setProtectedIdentity(data.status === 'protected');
        }
      } catch { /* ignore */ }
    } else if (sessionId || profile) {
      try {
        const res = await fetch(`${API}/api/v1/identity/init`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            identity_type: profile?.identity_type || 'individual',
          }),
        });
        if (res.ok) {
          const data = await res.json();
          setIdentity(data);
          localStorage.setItem(IDENTITY_ID_KEY, data.frek_id);
        }
      } catch { /* ignore */ }
    }
    setLoading(false);
  }, [profile]);

  useEffect(() => { bootstrap(); }, [bootstrap]);

  const chooseProfile = (p) => {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(p));
    setProfile(p);
    setShowProfilePicker(false);
    // Si identité pas encore créée, la créer avec le bon type
    if (!identity) bootstrap();
  };

  const clearProfile = () => {
    localStorage.removeItem(PROFILE_KEY);
    setProfile(null);
  };

  // Statuts des 4 étapes
  const stepStatus = {
    identity: identity ? 'done' : 'todo',
    passkey: protectedIdentity ? 'done' : identity ? 'ready' : 'locked',
    create: (stats.moments + stats.fk) > 0 ? 'done' : identity ? 'ready' : 'locked',
    universe: (stats.moments + stats.fk) > 0 ? 'ready' : 'locked',
  };

  const nextStep = STEPS.find((s) => stepStatus[s.key] === 'ready' || stepStatus[s.key] === 'todo') || STEPS[3];

  const goToStep = (key) => {
    if (key === 'identity') {
      if (!profile) { setShowProfilePicker(true); return; }
      navigate('/identity');
    }
    if (key === 'passkey') navigate('/identity');
    if (key === 'create') navigate('/');
    if (key === 'universe') navigate('/mine');
  };

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
        <Link to="/" className="text-xl font-bold text-slate-900" data-testid="universe-brand">FREKCORE</Link>
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="universe-link-sign">Signer</Link>
          <Link to="/mine" className="hover:text-blue-600 transition-colors" data-testid="universe-link-mine">Mon univers</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="universe-link-spec">Charte</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 max-w-3xl mx-auto px-6 py-12">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20, filter: 'blur(10px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-16"
        >
          <p className="text-xs text-slate-500 uppercase tracking-[0.3em] mb-4">Univers FREKCORE</p>
          <h1 className="text-5xl md:text-6xl font-black tracking-tighter text-slate-900 leading-tight mb-4" data-testid="universe-headline">
            Bienvenue dans votre<br />univers FREKCORE.
          </h1>
          <p className="text-lg text-slate-600 max-w-xl mx-auto" data-testid="universe-subline">
            Créez, protégez et retrouvez vos objets numériques dans un espace souverain.
          </p>
        </motion.div>

        {/* Profil d'usage */}
        {!profile && !showProfilePicker && (
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4, duration: 0.6 }}
            className="mb-10 text-center"
          >
            <button
              onClick={() => setShowProfilePicker(true)}
              className="px-6 py-3 bg-white/70 backdrop-blur border border-blue-200 text-slate-700 rounded-full text-sm font-semibold hover:bg-white hover:border-blue-400 transition-all"
              data-testid="universe-choose-profile-btn"
            >
              Choisir mon rôle dans l&apos;univers →
            </button>
            <p className="text-xs text-slate-500 mt-3">
              Cela personnalise votre parcours — votre FREK-ID reste unique.
            </p>
          </motion.div>
        )}

        {profile && !showProfilePicker && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            className="mb-10 bg-white/70 backdrop-blur-xl border border-blue-200 rounded-2xl p-5 flex items-center justify-between"
            data-testid="universe-profile-card"
          >
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-blue-600 mb-1">Je crée mon univers en tant que</div>
              <div className="text-slate-900 font-bold text-lg" data-testid="universe-profile-label">{profile.label}</div>
              <div className="text-slate-600 text-sm">{profile.tagline}</div>
            </div>
            <button
              onClick={() => setShowProfilePicker(true)}
              className="text-blue-600 hover:text-blue-800 text-xs font-semibold"
              data-testid="universe-profile-change"
            >
              Changer
            </button>
          </motion.div>
        )}

        <AnimatePresence>
          {showProfilePicker && (
            <motion.div
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 12 }}
              transition={{ duration: 0.4 }}
              className="mb-10 bg-white/80 backdrop-blur-xl border border-blue-200 rounded-3xl p-6 shadow-xl"
              data-testid="universe-profile-picker"
            >
              <div className="text-slate-900 font-bold text-lg mb-4">Je crée mon univers en tant que :</div>
              <div className="grid md:grid-cols-2 gap-3">
                {PROFILES.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => chooseProfile(p)}
                    className={`text-left p-4 rounded-xl border-2 transition-all ${
                      profile?.id === p.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-slate-200 bg-white/60 hover:border-blue-300 hover:bg-blue-50/40'
                    }`}
                    data-testid={`universe-profile-${p.id}`}
                  >
                    <div className="text-slate-900 font-bold">{p.label}</div>
                    <div className="text-xs text-blue-600 uppercase tracking-wide mb-1">{p.tagline}</div>
                    <div className="text-xs text-slate-600 leading-relaxed">{p.detail}</div>
                  </button>
                ))}
              </div>
              <div className="flex justify-between items-center mt-5">
                {profile && (
                  <button
                    onClick={clearProfile}
                    className="text-xs text-slate-400 hover:text-slate-700"
                    data-testid="universe-profile-clear"
                  >
                    Effacer mon rôle
                  </button>
                )}
                <button
                  onClick={() => setShowProfilePicker(false)}
                  className="ml-auto text-xs text-slate-500 hover:text-slate-900"
                  data-testid="universe-profile-close"
                >
                  Fermer
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 4 étapes */}
        <motion.ol
          initial="hidden" animate="show"
          variants={{ hidden: {}, show: { transition: { staggerChildren: 0.1 } } }}
          className="space-y-3 mb-10"
          data-testid="universe-steps"
        >
          {STEPS.map((step) => {
            const status = stepStatus[step.key];
            const isActive = nextStep?.key === step.key;
            return (
              <motion.li
                key={step.id}
                variants={{ hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.5 } } }}
              >
                <button
                  onClick={() => status !== 'locked' && goToStep(step.key)}
                  disabled={status === 'locked'}
                  className={`w-full text-left flex items-center gap-5 p-5 rounded-2xl border transition-all ${
                    status === 'done'
                      ? 'bg-blue-50/70 border-blue-200'
                      : status === 'locked'
                      ? 'bg-white/40 border-slate-100 opacity-50 cursor-not-allowed'
                      : isActive
                      ? 'bg-white/90 border-blue-400 shadow-lg hover:shadow-xl'
                      : 'bg-white/70 border-slate-200 hover:border-blue-300'
                  }`}
                  data-testid={`universe-step-${step.key}`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-black text-sm shrink-0 ${
                    status === 'done' ? 'bg-blue-600 text-white'
                    : status === 'locked' ? 'bg-slate-200 text-slate-400'
                    : 'bg-slate-900 text-white'
                  }`}>
                    {status === 'done' ? '✓' : step.id}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-slate-900 font-bold" data-testid={`universe-step-${step.key}-title`}>{step.title}</div>
                    <div className="text-sm text-slate-500 mt-0.5">{step.hint}</div>
                  </div>
                  <div className="shrink-0 text-xs text-slate-400 uppercase tracking-wider">
                    {status === 'done' ? 'Fait'
                      : status === 'locked' ? 'Verrouillé'
                      : isActive ? 'Continuer →'
                      : 'Ouvrir →'}
                  </div>
                </button>
              </motion.li>
            );
          })}
        </motion.ol>

        {/* État identité courant */}
        {!loading && identity && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}
            className="mb-10 bg-white/60 backdrop-blur border border-slate-200 rounded-2xl p-5"
            data-testid="universe-identity-status"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-[10px] text-slate-500 uppercase tracking-[0.2em] mb-1">Votre FREK-ID</div>
                <div className="font-mono text-sm text-slate-900 break-all" data-testid="universe-frek-id">{identity.frek_id}</div>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${protectedIdentity ? 'bg-blue-600' : 'bg-amber-400'}`} />
                <span className={protectedIdentity ? 'text-blue-700 font-semibold' : 'text-amber-700'}>
                  {protectedIdentity ? 'Protégé (Passkey)' : 'Non protégé'}
                </span>
              </div>
            </div>
            {(stats.moments + stats.fk) > 0 && (
              <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-2 gap-4 text-center">
                <div>
                  <div className="text-2xl font-black text-slate-900" data-testid="universe-count-moments">{stats.moments}</div>
                  <div className="text-xs text-slate-500 uppercase tracking-wide">Moment{stats.moments > 1 ? 's' : ''} signé{stats.moments > 1 ? 's' : ''}</div>
                </div>
                <div>
                  <div className="text-2xl font-black text-slate-900" data-testid="universe-count-fk">{stats.fk}</div>
                  <div className="text-xs text-slate-500 uppercase tracking-wide">Objet{stats.fk > 1 ? 's' : ''} FK</div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Message légal explicite */}
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 }}
          className="mt-12 mb-6 text-xs text-slate-500 text-center max-w-xl mx-auto leading-relaxed"
          data-testid="universe-legal-notice"
        >
          FREKCORE atteste l&apos;existence, l&apos;intégrité et l&apos;origine déclarée d&apos;un objet numérique.
          <br />Ce n&apos;est ni une autorité judiciaire, ni une preuve absolue de vérité.
        </motion.div>
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400">
        FREKCORE — Infrastructure de preuve culturelle
      </footer>
    </div>
  );
}
