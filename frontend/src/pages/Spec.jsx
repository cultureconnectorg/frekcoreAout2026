import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

/**
 * FREKCORE — Charte de confiance (page publique).
 * Niveau IP : PUBLIC. Aucune ingenierie exposee.
 * Doctrine : "Montrer la preuve. Cacher la recette."
 */

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

export function Spec() {
  const [charter, setCharter] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/v1/spec/`).then((r) => r.json()).then(setCharter).catch(() => {});
  }, []);

  const container = { hidden: {}, show: { transition: { staggerChildren: 0.15 } } };
  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] } },
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 overflow-hidden">
      <div aria-hidden="true" className="fixed inset-0 pointer-events-none">
        <motion.div
          className="absolute top-1/4 right-0 w-[500px] h-[500px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.1), transparent 70%)', filter: 'blur(80px)' }}
          animate={{ x: [-30, 30, -30], opacity: [0.5, 0.8, 0.5] }}
          transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      <motion.header
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative z-10 p-6 flex justify-between items-center max-w-5xl mx-auto"
      >
        <Link to="/" className="text-xl font-bold text-slate-900" data-testid="spec-brand">FREKCORE</Link>
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="link-back-sign">← Signer</Link>
          <Link to="/manifeste" className="hover:text-blue-600 transition-colors" data-testid="link-manifesto-spec">Manifeste</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 max-w-3xl mx-auto px-6 py-16">
        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3, duration: 0.6 }}
          className="text-xs text-slate-500 uppercase tracking-[0.3em] mb-4"
        >
          Charte de confiance · v{charter?.charter_version || '1.0'}
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-5xl md:text-7xl font-black tracking-tighter text-slate-900 mb-12 leading-tight"
          data-testid="spec-headline"
        >
          Notre engagement.
        </motion.h1>

        <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
          {(charter?.principles || []).map((p, idx) => (
            <motion.div
              key={idx}
              variants={item}
              className="border-l-2 border-blue-600 pl-6 py-2"
              data-testid={`spec-principle-${idx + 1}`}
            >
              <div className="text-xs text-blue-600 font-mono mb-1">0{idx + 1}</div>
              <p className="text-xl md:text-2xl text-slate-800 leading-relaxed font-light">{p}</p>
            </motion.div>
          ))}

          {charter?.commitment && (
            <motion.div
              variants={item}
              className="mt-16 p-8 bg-white/60 backdrop-blur border border-white/40 rounded-3xl shadow-xl"
              data-testid="spec-commitment"
            >
              <p className="text-lg text-slate-900 font-semibold leading-relaxed">
                {charter.commitment}
              </p>
            </motion.div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5, duration: 0.8 }}
          className="mt-20 text-sm text-slate-500 space-y-2"
        >
          <p>
            Partenaire ? <span className="text-slate-700">La documentation complète est accessible sous NDA.</span>
          </p>
          <p className="text-xs text-slate-400">
            Développeur ? Le vérificateur standalone est <Link to="/api/v1/passport/verifier/python" className="text-blue-600 hover:underline">accessible ici</Link>.
          </p>
        </motion.div>
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400">
        FREKCORE — Infrastructure de preuve culturelle
      </footer>
    </div>
  );
}

export default Spec;
