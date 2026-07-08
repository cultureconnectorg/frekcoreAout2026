import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import BrandLogo from '../components/BrandLogo';

/**
 * FREKCORE — Verifier offline standalone (page interne).
 *
 * Sert les fichiers exposes par /api/v1/passport/verifier/{python|js|js-demo|readme}
 * dans une interface lisible (au lieu d'ouvrir un raw text/x-python que le
 * navigateur ne sait pas rendre proprement).
 *
 * Doctrine "Montrer la preuve. Cacher la recette." :
 *   Ces verifiers sont deliberement publics — ils tournent HORS-LIGNE et
 *   permettent a un tiers de valider un passport.json SANS FREKCORE.
 *   Rien de sensible n'est exposé ici.
 */

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

const LANGS = [
  {
    id: 'python',
    label: 'Python',
    filename: 'verify_passport.py',
    endpoint: '/api/v1/passport/verifier/python',
    hint: 'Un seul fichier · Dépendance unique : cryptography. Exécutable sur toute machine avec Python 3.8+.',
    lang: 'python',
  },
  {
    id: 'js',
    label: 'JavaScript',
    filename: 'verify_passport.js',
    endpoint: '/api/v1/passport/verifier/js',
    hint: 'Module ES natif · Zero dépendance · Utilise Web Crypto API. Node 20+, Chrome 113+, Firefox 130+, Safari 17+.',
    lang: 'javascript',
  },
];

export default function Verifier() {
  const [params] = useSearchParams();
  const initialLang = LANGS.find((l) => l.id === params.get('lang'))?.id || 'python';
  const [active, setActive] = useState(initialLang);
  const [source, setSource] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const current = LANGS.find((l) => l.id === active) || LANGS[0];

  useEffect(() => {
    let cancel = false;
    setLoading(true);
    setError('');
    setSource('');
    setCopied(false);
    fetch(`${API}${current.endpoint}`)
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.text();
      })
      .then((txt) => { if (!cancel) setSource(txt); })
      .catch((e) => { if (!cancel) setError(e.message || 'Erreur de chargement'); })
      .finally(() => { if (!cancel) setLoading(false); });
    return () => { cancel = true; };
  }, [active, current.endpoint]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(source);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* clipboard denied */ }
  };

  const download = () => {
    const blob = new Blob([source], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = current.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 flex flex-col overflow-hidden">
      <motion.header
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative z-10 p-6 flex justify-between items-center max-w-5xl mx-auto w-full"
      >
        <BrandLogo to="/universe" testId="verifier-brand" />
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/universe" className="hover:text-blue-600 transition-colors" data-testid="verifier-link-universe">Univers</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="verifier-link-spec">Charte</Link>
          <Link to="/manifeste" className="hover:text-blue-600 transition-colors" data-testid="verifier-link-manifeste">Manifeste</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 flex-1 max-w-4xl mx-auto w-full px-6 py-10">
        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          className="text-xs text-slate-500 uppercase tracking-[0.3em] mb-3"
        >
          Vérificateur offline · Open Source
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-4xl md:text-5xl font-black tracking-tighter text-slate-900 mb-4"
          data-testid="verifier-headline"
        >
          Vérifiez un passport FREKCORE<br />sans nous.
        </motion.h1>
        <p className="text-slate-600 max-w-2xl mb-8" data-testid="verifier-subline">
          Ces vérificateurs tournent 100&nbsp;% hors-ligne. Ils ne dépendent d&apos;aucune API FREKCORE.
          Téléchargez, exécutez, vérifiez. Nous ne saurons jamais quand ni comment.
        </p>

        {/* Selecteur de langage */}
        <div className="flex flex-wrap gap-2 mb-4" data-testid="verifier-tabs">
          {LANGS.map((l) => (
            <button
              key={l.id}
              onClick={() => setActive(l.id)}
              className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${
                active === l.id
                  ? 'bg-slate-900 text-white shadow-lg'
                  : 'bg-white/60 text-slate-600 hover:bg-white'
              }`}
              data-testid={`verifier-tab-${l.id}`}
            >
              {l.label}
            </button>
          ))}
        </div>

        <p className="text-xs text-slate-500 mb-5" data-testid="verifier-hint">{current.hint}</p>

        {/* Actions */}
        <div className="flex flex-wrap gap-2 mb-5">
          <button
            onClick={download}
            disabled={loading || !!error || !source}
            className="px-5 py-2.5 bg-slate-900 text-white rounded-full text-sm font-semibold shadow hover:bg-slate-700 disabled:opacity-50 transition-all"
            data-testid="verifier-download"
          >
            Télécharger {current.filename}
          </button>
          <button
            onClick={copy}
            disabled={loading || !!error || !source}
            className="px-5 py-2.5 bg-white/70 border border-slate-300 text-slate-900 rounded-full text-sm font-semibold hover:bg-white disabled:opacity-50 transition-all"
            data-testid="verifier-copy"
          >
            {copied ? 'Copié ✓' : 'Copier le code'}
          </button>
          <a
            href={`${API}/api/v1/passport/verifier/readme`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 text-slate-600 text-sm hover:text-slate-900 self-center"
            data-testid="verifier-readme"
          >
            README →
          </a>
        </div>

        {/* Aperçu code */}
        <div className="bg-slate-900 rounded-2xl overflow-hidden shadow-xl" data-testid="verifier-code-panel">
          <div className="flex items-center justify-between px-4 py-2.5 bg-slate-800 text-slate-300 text-xs font-mono">
            <span>{current.filename}</span>
            <span>{loading ? 'chargement…' : `${source.length.toLocaleString('fr-FR')} caractères`}</span>
          </div>
          {loading ? (
            <div className="h-96 flex items-center justify-center text-slate-500 text-sm" data-testid="verifier-loading">
              <div className="w-8 h-8 border-2 border-slate-700 border-t-blue-400 rounded-full animate-spin" />
            </div>
          ) : error ? (
            <div className="h-96 flex flex-col items-center justify-center text-red-300 text-sm" data-testid="verifier-error">
              <p className="font-semibold mb-2">Erreur de chargement</p>
              <p className="text-xs text-red-400">{error}</p>
            </div>
          ) : (
            <pre
              className="p-5 overflow-auto text-[12px] leading-relaxed text-slate-100 font-mono max-h-[520px]"
              data-testid="verifier-code"
            >
              <code>{source}</code>
            </pre>
          )}
        </div>

        <div className="mt-8 text-xs text-slate-500 leading-relaxed max-w-2xl" data-testid="verifier-legal-notice">
          FREKCORE atteste l&apos;existence, l&apos;intégrité et l&apos;origine déclarée d&apos;un objet numérique.
          Ces vérificateurs sont publiés en clair pour que n&apos;importe quel tiers puisse s&apos;assurer,
          seul et sans nous, qu&apos;un passport a bien été signé par la clé publique de FREKCORE.
        </div>
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400">
        FREKCORE — Infrastructure de preuve culturelle
      </footer>
    </div>
  );
}
