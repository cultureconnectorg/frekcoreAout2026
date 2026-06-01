/**
 * FREK — Page Card plein écran /card/:frek_id
 * Affiche la FrekCard virtuelle nominative en grand, partageable.
 */
import { Link, useParams } from 'react-router-dom';
import FrekCard from '../components/FrekCard';

export default function Card() {
  const { frekId } = useParams();

  if (!frekId) {
    return (
      <div className="min-h-screen bg-[#f8fafc] flex items-center justify-center p-6">
        <div className="font-mono text-sm text-slate-500">
          FREK-ID manquant. <Link to="/accueil" className="text-[#0ea5e9] underline">Retour</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 relative overflow-hidden">
      {/* Décor blob cyan */}
      <div aria-hidden className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl opacity-40" />
      <div aria-hidden className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl opacity-30" />

      <header className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 py-6 flex items-center justify-between">
        <Link to={`/profil/${encodeURIComponent(frekId)}`} className="flex items-center gap-2" data-testid="card-back-link">
          <span className="font-display text-lg tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">FREK</span>
        </Link>
        <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">FREK Card</span>
      </header>

      <main className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 pb-16 pt-4 sm:pt-8">
        <div className="text-center mb-8">
          <div className="font-mono text-[10px] sm:text-xs uppercase tracking-[0.3em] text-[#0ea5e9] mb-2">Carte virtuelle nominative</div>
          <h1 className="font-display text-3xl sm:text-4xl text-slate-800">À vie. Vivante. Vôtre.</h1>
          <p className="font-mono text-sm text-slate-500 mt-3 max-w-xl mx-auto">
            Mise à jour en continu. Classée automatiquement par l'agent culturel
            FrekCore en présences, œuvres et croisements.
          </p>
        </div>

        <div className="max-w-md mx-auto" data-testid="card-frek-container">
          <FrekCard frekId={frekId} fullscreen showQrAlways />
        </div>

        <div className="text-center mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link
            to={`/profil/${encodeURIComponent(frekId)}`}
            data-testid="card-link-profile"
            className="px-5 py-2.5 bg-white border border-slate-200 hover:border-[#2cc4f5] text-slate-700 font-mono text-xs uppercase tracking-wider rounded-xl transition-colors shadow-sm"
          >
            Mon profil
          </Link>
          <Link
            to={`/verify/${encodeURIComponent(frekId)}`}
            data-testid="card-link-verify"
            className="px-5 py-2.5 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white font-mono text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-[#2cc4f5]/30 hover:shadow-xl hover:shadow-[#2cc4f5]/40 transition-all"
          >
            Vérification publique
          </Link>
        </div>
      </main>
    </div>
  );
}
