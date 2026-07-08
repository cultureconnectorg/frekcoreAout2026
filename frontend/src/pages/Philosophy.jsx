import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

/**
 * FREKCORE — Philosophie (page publique).
 * Identite visuelle v1.0 unifiee. Niveau IP : Public.
 * Vision long terme. Aucune ingenierie.
 */

export function Philosophy() {
  const container = { hidden: {}, show: { transition: { staggerChildren: 0.15 } } };
  const item = {
    hidden: { opacity: 0, y: 30 },
    show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.22, 1, 0.36, 1] } },
  };

  const pillars = [
    { n: '01', title: 'Mémoire', text: 'Une culture qui n\'est pas tracée disparaît. Une culture tracée mais falsifiable disparaît autrement.' },
    { n: '02', title: 'Souveraineté', text: 'La preuve ne doit dépendre d\'aucune entreprise, d\'aucun régime, d\'aucune juridiction seule.' },
    { n: '03', title: 'Responsabilité', text: 'Signer un moment, c\'est en accepter la trace publique. FREKCORE ne modifie jamais rétroactivement ce qui a été signé.' },
    { n: '04', title: 'Transmission', text: 'Une preuve n\'a de sens que si elle survit à celui qui l\'a créée. Nous concevons pour cinquante ans, pas pour cinq.' },
    { n: '05', title: 'Universalité', text: 'Toute culture, toute origine, tout patrimoine peut trouver sa place. FREKCORE ne juge pas le contenu — il en garantit l\'existence.' },
  ];

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 overflow-hidden">
      <div aria-hidden="true" className="fixed inset-0 pointer-events-none">
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.06), transparent 70%)', filter: 'blur(100px)' }}
          animate={{ scale: [1, 1.15, 1], opacity: [0.4, 0.7, 0.4] }}
          transition={{ duration: 15, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      <motion.header
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative z-10 p-6 flex justify-between items-center max-w-5xl mx-auto"
      >
        <Link to="/" className="text-xl font-bold text-slate-900" data-testid="philo-brand">FREKCORE</Link>
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="link-back-sign-philo">← Signer</Link>
          <Link to="/manifeste" className="hover:text-blue-600 transition-colors" data-testid="link-manifeste-philo">Manifeste</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="link-spec-philo">Charte</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 max-w-4xl mx-auto px-6 py-20">
        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
          className="text-xs text-slate-500 uppercase tracking-[0.3em] mb-4"
        >
          Philosophie
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-5xl md:text-7xl font-black tracking-tighter text-slate-900 mb-8 leading-tight"
          data-testid="philo-headline"
        >
          Nos convictions.
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6, duration: 0.7 }}
          className="text-xl text-slate-600 font-light mb-16 max-w-2xl leading-relaxed"
        >
          Cinq principes qui structurent tout ce que nous construisons — et tout ce que nous refusons de construire.
        </motion.p>

        <motion.div variants={container} initial="hidden" animate="show" className="space-y-12">
          {pillars.map((p) => (
            <motion.div key={p.n} variants={item} className="flex gap-8 items-start" data-testid={`philo-pillar-${p.n}`}>
              <div className="text-blue-600 font-mono text-sm tracking-widest pt-2 flex-shrink-0">{p.n}</div>
              <div>
                <h2 className="text-3xl md:text-4xl font-black text-slate-900 mb-3 tracking-tight">{p.title}</h2>
                <p className="text-lg text-slate-700 font-light leading-relaxed max-w-2xl">{p.text}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.8, duration: 0.8 }}
          className="mt-24 p-10 bg-white/60 backdrop-blur-xl border border-white/40 rounded-3xl shadow-xl"
        >
          <p className="text-xl md:text-2xl text-slate-900 font-light leading-relaxed">
            Nous ne prétendons pas être neutres. Nous prétendons être <span className="font-semibold">responsables</span>.
          </p>
        </motion.div>
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400">
        FREKCORE — Infrastructure de preuve culturelle
      </footer>
    </div>
  );
}

export default Philosophy;
