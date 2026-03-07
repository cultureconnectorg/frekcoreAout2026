/**
 * FREK v2 — Conditions d'utilisation
 */
import { Link } from 'react-router-dom';

export function Terms() {
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
          Conditions d'utilisation
        </h1>

        <div className="prose prose-slate max-w-none space-y-6">
          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Acceptation</h2>
            <p className="text-slate-600 leading-relaxed">
              En utilisant FREK, vous acceptez les présentes conditions. FREK est un service de certification 
              fréquentielle, pas un service de protection des droits d'auteur.
            </p>
          </section>

          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Nature du service</h2>
            <p className="text-slate-600 leading-relaxed">
              FREK atteste l'existence d'une empreinte fréquentielle à un instant T. FREK n'atteste pas 
              l'originalité, la propriété ou les droits sur une œuvre.
            </p>
          </section>

          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Responsabilité</h2>
            <p className="text-slate-600 leading-relaxed">
              L'utilisateur est seul responsable du contenu qu'il certifie. FREK agit comme un notaire de fait 
              technique et ne porte aucun jugement sur la légalité ou la légitimité des fichiers soumis.
            </p>
          </section>

          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Licence</h2>
            <p className="text-slate-600 leading-relaxed">
              FREK est un standard ouvert sous licence CC BY 4.0. Le code source est disponible publiquement.
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

export default Terms;
