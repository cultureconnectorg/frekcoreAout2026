/**
 * FREK v2 — Aide / Support
 */
import { Link } from 'react-router-dom';

export function Help() {
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
          Aide
        </h1>

        <div className="prose prose-slate max-w-none space-y-8">
          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Comment certifier ?</h2>
            <ol className="text-slate-600 leading-relaxed space-y-2 list-decimal list-inside">
              <li>Cliquez sur le bouton bleu sur la page d'accueil</li>
              <li>Sélectionnez votre fichier audio</li>
              <li>Attendez quelques secondes</li>
              <li>Recevez votre FREK-ID unique</li>
            </ol>
          </section>

          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Formats supportés</h2>
            <p className="text-slate-600 leading-relaxed">
              WAV, MP3, FLAC, OGG, AAC et la plupart des formats audio courants.
            </p>
          </section>

          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Vérifier une attestation</h2>
            <p className="text-slate-600 leading-relaxed">
              Scannez le QR code ou entrez le FREK-ID sur la page de vérification pour confirmer l'authenticité d'une attestation.
            </p>
          </section>

          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
            <h2 className="font-mono text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">Contact</h2>
            <p className="text-slate-600 leading-relaxed">
              Pour toute question : <a href="mailto:support@frekcore.com" className="text-[#2cc4f5] hover:underline">support@frekcore.com</a>
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}

export default Help;
