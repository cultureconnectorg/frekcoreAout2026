/**
 * FREK v2 — Politique de divulgation responsable
 */
import { Link } from 'react-router-dom';

export function Disclosure() {
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
          Politique de divulgation responsable
        </h1>

        <div className="prose prose-slate max-w-none space-y-6">
          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Signaler une vulnérabilité</h2>
            <p className="text-slate-600 leading-relaxed">
              Si vous découvrez une faille de sécurité dans FREK, veuillez nous contacter de manière responsable 
              à l'adresse : <a href="mailto:security@frekcore.com" className="text-[#2cc4f5] hover:underline">security@frekcore.com</a>
            </p>
          </section>

          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Notre engagement</h2>
            <p className="text-slate-600 leading-relaxed">
              Nous nous engageons à répondre sous 48 heures et à traiter toute vulnérabilité signalée avec 
              sérieux. Nous ne poursuivrons pas les chercheurs en sécurité agissant de bonne foi.
            </p>
          </section>

          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Périmètre</h2>
            <p className="text-slate-600 leading-relaxed">
              Cette politique couvre l'application FREK, son API et son infrastructure. 
              Les tests ne doivent pas perturber le service pour les autres utilisateurs.
            </p>
          </section>

          <section>
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Reconnaissance</h2>
            <p className="text-slate-600 leading-relaxed">
              Avec votre accord, nous pouvons vous mentionner dans notre Hall of Fame pour votre contribution 
              à la sécurité de FREK.
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

export default Disclosure;
