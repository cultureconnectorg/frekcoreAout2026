/**
 * FREK v2 — Mentions légales (Imprint)
 */
import { Link } from 'react-router-dom';

export function Imprint() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-slate-50 to-gray-100 text-slate-800">
      <header className="bg-white/80 backdrop-blur-xl border-b border-slate-200/50 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 sm:gap-3">
            <img src="/frek-logo.png" alt="FREK" className="h-6 sm:h-8 w-auto" />
            <span className="font-display text-lg sm:text-xl tracking-wider text-[#2cc4f5]">FREK</span>
          </Link>
          <Link to="/" className="px-3 sm:px-4 py-1.5 sm:py-2 bg-[#2cc4f5] text-white font-mono text-[10px] sm:text-xs uppercase tracking-wider rounded-lg hover:bg-[#1a9fd4] transition-all font-bold shadow-lg shadow-[#2cc4f5]/20">
            Certifier
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        <h1 className="font-display text-3xl sm:text-4xl tracking-wider text-[#2cc4f5] mb-8">
          Mentions légales
        </h1>

        <div className="prose prose-slate max-w-none space-y-6">
          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Éditeur</h2>
            <p className="text-slate-600 leading-relaxed">
              <strong>CVLN Group</strong><br />
              Bruxelles, Belgique<br />
              <a href="mailto:contact@frekcore.com" className="text-[#2cc4f5] hover:underline">contact@frekcore.com</a>
            </p>
          </section>

          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Directeur de publication</h2>
            <p className="text-slate-600 leading-relaxed">
              CVLN Group
            </p>
          </section>

          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Hébergement</h2>
            <p className="text-slate-600 leading-relaxed">
              Infrastructure cloud sécurisée<br />
              Union Européenne
            </p>
          </section>

          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Propriété intellectuelle</h2>
            <p className="text-slate-600 leading-relaxed">
              FREK® est une marque déposée de CVLN Group.<br />
              Le standard FREK est distribué sous licence CC BY 4.0.
            </p>
          </section>
        </div>

        <p className="font-mono text-xs text-slate-400 mt-12">
          Dernière mise à jour : Mars 2026
        </p>
      </main>
    </div>
  );
}

export default Imprint;
