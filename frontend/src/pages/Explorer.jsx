import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

/**
 * FREKCORE — Explorer public.
 * Niveau IP : PUBLIC. Cas d'usages narres, PAS de raw blockchain.
 * Le raw est deplace sur /admin/explorer (X-Admin-Key).
 */

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

export function Explorer() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/v1/moment/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  const useCases = [
    { icon: '🎵', title: 'Un concert', desc: 'Chaque spectateur repart avec la preuve d\'y avoir été.' },
    { icon: '🎨', title: 'Un vernissage', desc: 'L\'artiste et ses témoins signent le moment de rencontre.' },
    { icon: '📚', title: 'Une conférence', desc: 'La parole prononcée devient une empreinte partagée.' },
    { icon: '🌍', title: 'Un événement citoyen', desc: 'La présence collective se fige, vérifiable dans dix ans.' },
    { icon: '🏛️', title: 'Une institution', desc: 'Chaque acte culturel devient une trace certifiée.' },
    { icon: '⛰️', title: 'Un patrimoine', desc: 'Un lieu, un instant, une transmission durable.' },
  ];

  const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 overflow-hidden">
      <div aria-hidden="true" className="fixed inset-0 pointer-events-none">
        <motion.div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[700px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.08), transparent 70%)', filter: 'blur(80px)' }}
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      <motion.header
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative z-10 p-6 flex justify-between items-center max-w-5xl mx-auto"
      >
        <Link to="/" className="text-xl font-bold text-slate-900" data-testid="explorer-brand">FREKCORE</Link>
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="link-back-sign-explorer">← Signer</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="link-spec-explorer">Charte</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 max-w-5xl mx-auto px-6 py-12">
        <motion.h1
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-5xl md:text-7xl font-black tracking-tighter text-slate-900 mb-4"
          data-testid="explorer-headline"
        >
          Ce qui se passe.
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3, duration: 0.6 }}
          className="text-lg text-slate-600 mb-16"
        >
          Chaque moment signé devient une empreinte durable.
          <br />
          Voici la respiration de FREKCORE, en direct.
        </motion.p>

        {/* Compteur central */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.8 }}
          className="mb-20 bg-white/60 backdrop-blur-xl border border-white/40 rounded-3xl p-10 text-center shadow-xl"
          data-testid="explorer-counter"
        >
          <div className="text-xs text-slate-500 uppercase tracking-[0.3em] mb-3">Moments signés</div>
          <motion.div
            key={stats?.total_moments_signed || 0}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 200, damping: 15 }}
            className="text-7xl md:text-8xl font-black text-slate-900 tabular-nums tracking-tighter"
          >
            {stats?.total_moments_signed ?? '—'}
          </motion.div>
          <div className="text-sm text-slate-500 mt-3">
            dont <span className="text-blue-600 font-semibold">{stats?.last_24h ?? 0}</span> dans les dernières 24h
          </div>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-3xl font-bold text-slate-900 mb-2 tracking-tight"
        >
          Exemples d'usages.
        </motion.h2>
        <p className="text-slate-500 mb-10">Six façons dont FREKCORE prend son sens.</p>

        <motion.div
          variants={container} initial="hidden" whileInView="show" viewport={{ once: true }}
          className="grid md:grid-cols-2 gap-6"
          data-testid="explorer-usecases"
        >
          {useCases.map((u, idx) => (
            <motion.div
              key={idx}
              variants={item}
              whileHover={{ y: -4, boxShadow: '0 20px 40px -20px rgba(15, 23, 42, 0.15)' }}
              transition={{ type: 'spring', stiffness: 300, damping: 22 }}
              className="bg-white/70 backdrop-blur border border-slate-200 rounded-2xl p-6"
              data-testid={`explorer-usecase-${idx}`}
            >
              <div className="text-3xl mb-3">{u.icon}</div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">{u.title}</h3>
              <p className="text-slate-600 text-sm leading-relaxed">{u.desc}</p>
            </motion.div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="mt-20 text-center"
        >
          <p className="text-slate-500 text-sm mb-4">Chaque preuve individuelle est vérifiable publiquement.</p>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className="inline-block">
            <Link
              to="/"
              className="inline-block px-10 py-4 bg-slate-900 text-white rounded-full font-bold tracking-wider shadow-xl hover:shadow-2xl transition-shadow"
              data-testid="explorer-cta-sign"
            >
              Signer mon moment
            </Link>
          </motion.div>
        </motion.div>
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400">
        FREKCORE — {stats?.total_moments_signed ?? 0} moments signés à ce jour
      </footer>
    </div>
  );
}

export default Explorer;
