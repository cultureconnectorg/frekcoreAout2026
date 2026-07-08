import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import BrandLogo from '../components/BrandLogo';

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = 'frek_moment_session';
const IDENTITY_TOKEN_KEY = 'frek_identity_token';

export default function MyMoments() {
  const [moments, setMoments] = useState([]);
  const [fkObjects, setFkObjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sessionId, setSessionId] = useState('');
  const [protectedIdentity, setProtectedIdentity] = useState(null);

  useEffect(() => {
    const s = localStorage.getItem(SESSION_KEY);
    const token = localStorage.getItem(IDENTITY_TOKEN_KEY);
    if (s) setSessionId(s);

    const load = async () => {
      // 1. Charger l'identity protegee (si token)
      if (token) {
        try {
          const meRes = await fetch(`${API}/api/v1/identity/me`, { headers: { 'X-FREK-Session': token } });
          if (meRes.ok) {
            const me = await meRes.json();
            setProtectedIdentity(me);
            // 2. Fetch univers unifie (moments + FK) via l'endpoint identity
            const objRes = await fetch(`${API}/api/v1/identity/${me.frek_id}/objects`, {
              headers: { 'X-FREK-Session': token },
            });
            if (objRes.ok) {
              const data = await objRes.json();
              setMoments(data.moments || []);
              setFkObjects(data.fk_objects || []);
              setLoading(false);
              return;
            }
          }
        } catch { /* fallback below */ }
      }
      // 3. Fallback anonyme : seulement les moments de la session locale
      if (s) {
        try {
          const r = await fetch(`${API}/api/v1/moment/mine?session_id=${s}`);
          const d = r.ok ? await r.json() : { moments: [] };
          setMoments(d.moments || []);
        } catch { setMoments([]); }
      }
      setLoading(false);
    };
    load();
  }, []);

  const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
  const item = {
    hidden: { opacity: 0, y: 12 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
  };

  const totalObjects = moments.length + fkObjects.length;

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 overflow-hidden">
      <div aria-hidden="true" className="fixed inset-0 pointer-events-none">
        <motion.div
          className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.08), transparent 70%)', filter: 'blur(60px)' }}
          animate={{ scale: [1, 1.15, 1], opacity: [0.5, 0.8, 0.5] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      <motion.header
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative z-10 p-6 flex justify-between items-center max-w-5xl mx-auto"
      >
        <BrandLogo to="/universe" testId="mine-brand" />
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/universe" className="hover:text-blue-600 transition-colors" data-testid="link-universe-mine">Univers</Link>
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="link-back-sign">Signer</Link>
          <Link to="/identity" className="hover:text-blue-600 transition-colors" data-testid="link-identity-mine">Identité</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="link-spec-mine">Charte</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 max-w-4xl mx-auto px-6 py-12">
        <motion.h1
          initial={{ opacity: 0, y: 30, filter: 'blur(8px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          className="text-5xl md:text-6xl font-black tracking-tighter text-slate-900 mb-2"
          data-testid="mine-headline"
        >
          Mon univers.
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2, duration: 0.6 }}
          className="text-slate-600 mb-2"
        >
          {totalObjects === 0 ? 'Aucune signature pour l\'instant.'
            : `${moments.length} moment${moments.length > 1 ? 's' : ''}${fkObjects.length > 0 ? ` · ${fkObjects.length} objet${fkObjects.length > 1 ? 's' : ''} FK` : ''}`}
        </motion.p>

        {protectedIdentity && (
          <motion.div
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35, duration: 0.5 }}
            className="mb-8 bg-white/60 backdrop-blur border border-slate-200 rounded-2xl p-5"
            data-testid="mine-identity-panel"
          >
            <div className="grid md:grid-cols-3 gap-4 text-center md:text-left">
              <div>
                <div className="text-[10px] text-slate-500 uppercase tracking-[0.2em] mb-1">FREK-ID</div>
                <div className="font-mono text-xs text-slate-900 break-all" data-testid="mine-identity-frek-id">{protectedIdentity.frek_id}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase tracking-[0.2em] mb-1">Passkey</div>
                <div className="text-blue-700 text-sm font-semibold flex items-center gap-1 md:justify-start justify-center">
                  <span className="w-2 h-2 rounded-full bg-blue-600" /> {protectedIdentity.credentials_count || 1} active{(protectedIdentity.credentials_count || 1) > 1 ? 's' : ''}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase tracking-[0.2em] mb-1">Niveau de protection</div>
                <div className="text-slate-900 text-sm font-semibold">Souverain · à vie</div>
              </div>
            </div>
          </motion.div>
        )}

        {protectedIdentity ? (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
            className="text-xs text-blue-700 mb-10 flex items-center gap-2"
            data-testid="mine-identity-notice"
          >
            <span className="w-2 h-2 rounded-full bg-blue-600" />
            Univers protégé par Passkey · {protectedIdentity.frek_id}
          </motion.div>
        ) : (
          <motion.p
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35, duration: 0.5 }}
            className="text-xs text-slate-500 mb-10 flex items-center gap-2"
            data-testid="mine-identity-notice"
          >
            <span data-testid="mine-isolation-notice" className="flex items-center gap-2">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m0 0v3m0-3h.01M17 9V7a5 5 0 00-10 0v2M5 9h14v11a2 2 0 01-2 2H7a2 2 0 01-2-2V9z" />
              </svg>
              Cet espace est privé à ce navigateur. Personne d&apos;autre ne peut le voir.
            </span>
          </motion.p>
        )}

        {!protectedIdentity && moments.length >= 1 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="bg-gradient-to-br from-blue-50 to-blue-100/50 backdrop-blur border border-blue-200 rounded-2xl p-6 mb-8"
            data-testid="mine-attach-prompt"
          >
            <div className="text-lg font-bold text-slate-900 mb-2">Protéger cet univers ?</div>
            <p className="text-sm text-slate-600 mb-4">
              Associe une Passkey (Touch ID / Face ID / Windows Hello) pour retrouver ces signatures depuis n&apos;importe quel appareil. Aucun compte, aucun mot de passe.
            </p>
            <Link to="/identity"
              className="inline-block px-5 py-2 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-700 transition-colors"
              data-testid="mine-attach-btn"
            >
              Protéger mon univers →
            </Link>
          </motion.div>
        )}

        {loading ? (
          <div className="text-center py-12 text-slate-500" data-testid="mine-loading">Chargement…</div>
        ) : totalObjects === 0 ? (
          <div className="text-center py-12">
            <Link to="/" className="inline-block px-10 py-5 bg-slate-900 text-white rounded-full font-bold tracking-wider shadow-xl" data-testid="mine-cta-first">
              Signer ton premier moment
            </Link>
          </div>
        ) : (
          <motion.div variants={container} initial="hidden" animate="show" className="space-y-3" data-testid="mine-list">
            {fkObjects.map((f) => (
              <motion.div key={`fk-${f.frek_id}`} variants={item} whileHover={{ x: 4 }}>
                <div className="block bg-white/70 backdrop-blur border border-blue-200 rounded-xl p-5 hover:border-blue-400 transition-all" data-testid={`mine-fk-${f.frek_id}`}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 text-slate-900 font-semibold truncate">
                        <span className="px-2 py-0.5 bg-blue-600 text-white rounded-full text-[10px] font-bold">FK</span>
                        <span className="truncate">{f.title || 'Objet FK sans titre'}</span>
                      </div>
                      <div className="text-xs text-slate-500 font-mono mt-1 truncate">#{f.frek_id}</div>
                      <div className="text-xs text-slate-400 mt-2">
                        {f.object_type} · {new Date(f.created_at).toLocaleString('fr-FR', { dateStyle: 'short' })}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
            {moments.map((m) => (
              <motion.div key={m.frek_id} variants={item} whileHover={{ x: 4 }} transition={{ type: 'spring', stiffness: 300, damping: 25 }}>
                <Link
                  to={`/verify/${m.frek_id}`}
                  className="block bg-white/70 backdrop-blur border border-slate-200 rounded-xl p-5 hover:border-blue-400 hover:shadow-lg transition-all"
                  data-testid={`mine-item-${m.frek_id}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="text-slate-900 font-semibold truncate">
                        {m.metadata?.title || 'Moment sans titre'}
                      </div>
                      <div className="text-xs text-slate-500 font-mono mt-1 truncate">#{m.frek_id}</div>
                      <div className="text-xs text-slate-400 mt-2">
                        {new Date(m.created_at).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1 justify-end max-w-[40%]">
                      {(m.metadata?.layers_captured || []).map((l) => (
                        <span key={l} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-[10px] font-medium">{l}</span>
                      ))}
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        )}
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400">
        <div className="mb-2 max-w-md mx-auto leading-relaxed" data-testid="mine-legal-notice">
          FREKCORE atteste l&apos;existence, l&apos;intégrité et l&apos;origine déclarée d&apos;un objet numérique.
        </div>
        {protectedIdentity ? 'Univers protégé' : sessionId ? <>Session anonyme : <span className="font-mono">{sessionId.slice(0, 8)}…</span></> : null}
      </footer>
    </div>
  );
}
