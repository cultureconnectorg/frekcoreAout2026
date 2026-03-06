import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { JsonBlock } from '../ui/JsonBlock';

const heroJsonExample = `{
  "frek_version": "0.4",
  "mix_id": "FREK-2026-MQ-001",
  "artist": { "name": "DJ Chimin", "territory": "MQ" },
  "event": {
    "name": "Culture Connect 2026",
    "date": "2026-05-22",
    "location": "Fort-de-France, MQ"
  },
  "proof_level": "strong",
  "audio_fingerprint": "frek:fp:a3f2b1c4...",
  "rfc3161_token": "MIIBxTCCAW0...",
  "jurisdiction": "WIPO-CAM",
  "signature": "ed25519:ccddee3344..."
}`;

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: 'easeOut' },
  },
};

export function Hero() {
  const scrollToVerifier = (e) => {
    e.preventDefault();
    document.querySelector('#verifier')?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToSpec = (e) => {
    e.preventDefault();
    document.querySelector('#spec')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section
      id="hero"
      className="min-h-screen pt-32 pb-20 px-6 relative overflow-hidden"
      style={{
        background: 'radial-gradient(ellipse at right top, rgba(196,113,74,0.07) 0%, transparent 50%)',
      }}
    >
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center min-h-[calc(100vh-12rem)]">
        {/* Left Column */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-8"
        >
          <motion.div variants={itemVariants}>
            <span className="inline-block px-4 py-2 border border-terra/40 font-mono text-xs uppercase tracking-wider text-terra">
              Standard ouvert · v0.4 · Mars 2026
            </span>
          </motion.div>

          <motion.h1 variants={itemVariants} className="relative">
            <span className="font-display text-[8rem] md:text-[10rem] lg:text-[12rem] text-fwhite leading-none tracking-tight">
              FREK
            </span>
            <span className="font-display text-4xl md:text-5xl text-gold absolute top-0 ml-2">®</span>
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="font-body text-xl md:text-2xl text-mid max-w-xl leading-relaxed"
          >
            Infrastructure de preuve audio locale pour les DJ mixes et performances composites.
            Standard neutre, open source, cryptographiquement signé.
          </motion.p>

          <motion.div
            variants={itemVariants}
            className="flex flex-wrap gap-4 font-mono text-sm text-dim"
          >
            <span>Preuve {'>'} Service</span>
            <span className="text-terra/40">·</span>
            <span>Local-First</span>
            <span className="text-terra/40">·</span>
            <span>Anti-Surveillance</span>
          </motion.div>

          <motion.div variants={itemVariants} className="flex flex-wrap gap-4 pt-4">
            <Link to="/generate" className="btn-primary">
              Générer mon attestation
            </Link>
            <button onClick={scrollToVerifier} className="btn-outline">
              Vérifier un mix
            </button>
            <button onClick={scrollToSpec} className="btn-outline">
              Documentation
            </button>
          </motion.div>
        </motion.div>

        {/* Right Column - JSON Preview */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4, ease: 'easeOut' }}
          className="hidden lg:block"
        >
          <JsonBlock
            code={heroJsonExample}
            filename="FREK-2026-MQ-001.frek.json"
            verified={true}
          />
        </motion.div>
      </div>
    </section>
  );
}

export default Hero;
