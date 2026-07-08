import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

/**
 * FREKCORE — Manifeste (page publique).
 * Identite visuelle v1.0 unifiee. Niveau IP : Public.
 * Vend le POURQUOI, jamais le COMMENT.
 */

export function Manifeste() {
  const container = { hidden: {}, show: { transition: { staggerChildren: 0.12 } } };
  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] } },
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 overflow-hidden">
      <div aria-hidden="true" className="fixed inset-0 pointer-events-none">
        <motion.div
          className="absolute top-0 left-1/4 w-[500px] h-[500px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.1), transparent 70%)', filter: 'blur(80px)' }}
          animate={{ y: [0, 30, 0], scale: [1, 1.1, 1] }}
          transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
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
        <Link to="/" className="text-xl font-bold text-slate-900" data-testid="manifeste-brand">FREKCORE</Link>
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/universe" className="hover:text-blue-600 transition-colors" data-testid="link-universe-mf">Univers</Link>
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="link-back-sign-mf">Signer</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="link-spec-mf">Charte</Link>
          <Link to="/explorer" className="hover:text-blue-600 transition-colors" data-testid="link-explorer-mf">Explorer</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 max-w-3xl mx-auto px-6 py-20">
        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
          className="text-xs text-slate-500 uppercase tracking-[0.3em] mb-4"
        >
          Manifeste
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-5xl md:text-7xl font-black tracking-tighter text-slate-900 mb-16 leading-tight"
          data-testid="manifeste-headline"
        >
          Pour que rien ne s'efface.
        </motion.h1>

        <motion.div variants={container} initial="hidden" animate="show" className="space-y-10 text-lg md:text-xl text-slate-700 font-light leading-relaxed">
          <motion.p variants={item}>
            La culture n'est pas un divertissement. C'est la mémoire de ce que nous choisissons de retenir, de transmettre, de défendre.
          </motion.p>
          <motion.p variants={item}>
            Chaque moment culturel — un concert, une œuvre, une parole, une rencontre — mérite une trace que le temps ne dévore pas.
          </motion.p>
          <motion.p variants={item}>
            FREKCORE existe pour cette raison unique : <span className="text-slate-900 font-semibold">rendre l'instant permanent, la présence vérifiable, la mémoire souveraine.</span>
          </motion.p>
          <motion.p variants={item}>
            Nous ne construisons pas une plateforme. Nous construisons une institution numérique qui engage sa parole.
          </motion.p>
          <motion.p variants={item}>
            Ce que tu signes aujourd'hui pourra être lu dans dix ans, dans cinquante ans, sans nous demander la permission.
          </motion.p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5, duration: 0.8 }}
          className="mt-20 flex flex-wrap gap-4"
        >
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link to="/" className="inline-block px-8 py-4 bg-slate-900 text-white rounded-full font-bold tracking-wider shadow-xl hover:shadow-2xl transition-shadow" data-testid="manifeste-cta-sign">
              Signer un moment
            </Link>
          </motion.div>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link to="/philosophy" className="inline-block px-8 py-4 bg-white/70 backdrop-blur border border-slate-300 text-slate-900 rounded-full font-semibold hover:bg-white transition-colors" data-testid="manifeste-cta-philo">
              Lire la vision →
            </Link>
          </motion.div>
        </motion.div>
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400">
        <div className="mb-2 max-w-lg mx-auto leading-relaxed" data-testid="manifeste-legal-notice">
          FREKCORE atteste l&apos;existence, l&apos;intégrité et l&apos;origine déclarée d&apos;un objet numérique. Nous ne remplaçons ni un juge ni un notaire d&apos;État.
        </div>
        FREKCORE — Infrastructure de preuve culturelle
      </footer>
    </div>
  );
}

export default Manifeste;
