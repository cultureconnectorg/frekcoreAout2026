import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = 'frek_moment_session';

export default function MyMoments() {
  const [moments, setMoments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sessionId, setSessionId] = useState('');

  useEffect(() => {
    const s = localStorage.getItem(SESSION_KEY);
    if (!s) { setLoading(false); return; }
    setSessionId(s);
    fetch(`${API}/api/v1/moment/mine?session_id=${s}`)
      .then((r) => r.ok ? r.json() : { moments: [] })
      .then((d) => setMoments(d.moments || []))
      .catch(() => setMoments([]))
      .finally(() => setLoading(false));
  }, []);

  const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
  const item = {
    hidden: { opacity: 0, y: 12 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 overflow-hidden">
      {/* Subtile aura */}
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
        <Link to="/" className="text-xl font-bold text-slate-900" data-testid="mine-brand">FREKCORE</Link>
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="link-back-sign">← Signer</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="link-spec-mine">Spec</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 max-w-4xl mx-auto px-6 py-12">
        <motion.h1
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-5xl md:text-6xl font-black tracking-tighter text-slate-900 mb-2"
          data-testid="mine-headline"
        >
          Ton univers.
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2, duration: 0.6 }}
          className="text-slate-600 mb-10"
        >
          {moments.length === 0 ? 'Aucun moment signé pour l\'instant.'
            : `${moments.length} moment${moments.length > 1 ? 's' : ''} signé${moments.length > 1 ? 's' : ''} depuis ce navigateur.`}
        </motion.p>

        {moments.length >= 3 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="bg-gradient-to-br from-blue-50 to-blue-100/50 backdrop-blur border border-blue-200 rounded-2xl p-6 mb-8"
            data-testid="mine-attach-prompt"
          >
            <div className="text-lg font-bold text-slate-900 mb-2">Conserver ton univers ?</div>
            <p className="text-sm text-slate-600 mb-4">
              Associe une identité pour retrouver tes moments sur tous tes appareils. Aucune donnée n'est publiée — seul un hash est stocké.
            </p>
            <button disabled className="px-5 py-2 bg-slate-300 text-slate-600 rounded-full text-sm cursor-not-allowed" data-testid="mine-attach-btn">
              Associer un email (bientôt)
            </button>
          </motion.div>
        )}

        {loading ? (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="text-center py-12 text-slate-500" data-testid="mine-loading"
          >
            Chargement…
          </motion.div>
        ) : moments.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
            className="text-center py-12"
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className="inline-block">
              <Link
                to="/"
                className="inline-block px-10 py-5 bg-slate-900 text-white rounded-full font-bold tracking-wider shadow-xl hover:shadow-2xl transition-shadow"
                data-testid="mine-cta-first"
              >
                Signer ton premier moment
              </Link>
            </motion.div>
          </motion.div>
        ) : (
          <motion.div variants={container} initial="hidden" animate="show" className="space-y-3" data-testid="mine-list">
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
        Session anonyme : <span className="font-mono">{sessionId.slice(0, 8)}…</span>
      </footer>
    </div>
  );
}
