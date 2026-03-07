/**
 * FREK v2 — Page Juridique
 * Version publique simplifiée
 */
import { Link } from 'react-router-dom';

export function Legal() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#050a0d] via-[#0a1520] to-[#050a0d] text-white">
      {/* Header */}
      <header className="bg-[#050a0d]/95 backdrop-blur-xl border-b border-[#2cc4f5]/10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 sm:gap-3">
            <img src="/frek-logo.png" alt="FREK" className="h-6 sm:h-8 w-auto" />
            <span className="font-display text-lg sm:text-xl tracking-wider text-[#2cc4f5]">FREK</span>
          </Link>
          <Link
            to="/"
            className="px-3 sm:px-4 py-1.5 sm:py-2 bg-[#2cc4f5] text-[#050a0d] font-mono text-[10px] sm:text-xs uppercase tracking-wider rounded hover:bg-[#33cfff] transition-all font-bold"
          >
            Certifier
          </Link>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
        <div className="mb-8 sm:mb-12">
          <h1 className="font-display text-3xl sm:text-4xl md:text-5xl tracking-wider text-[#2cc4f5] mb-4">
            Cadre Juridique
          </h1>
          <p className="font-mono text-xs sm:text-sm text-[#8ab4c8]/60 uppercase tracking-wider">
            Neutralité et transparence
          </p>
        </div>

        <div className="space-y-8 sm:space-y-12">
          {/* Principe fondamental */}
          <section className="bg-[#0a1520]/50 rounded-xl p-6 sm:p-8 border border-[#2cc4f5]/10">
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Principe Fondamental
            </h2>
            <blockquote className="font-body text-base sm:text-lg text-[#8ab4c8] leading-relaxed border-l-2 border-[#2cc4f5]/30 pl-4 sm:pl-6 italic">
              "FREK ne reconnaît pas la musique. FREK reconnaît un fait technique, dans un contexte précis."
            </blockquote>
          </section>

          {/* Notaire de fait */}
          <section>
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Notaire de Fait
            </h2>
            <div className="font-body text-sm sm:text-base text-[#8ab4c8]/80 leading-relaxed space-y-4">
              <p>
                FREK agit comme un <strong className="text-[#2cc4f5]">notaire de fait technique</strong> — 
                il atteste l'existence d'une empreinte fréquentielle à un instant T, sans jamais porter 
                de jugement sur la nature, l'origine ou la qualité de l'œuvre.
              </p>
            </div>
          </section>

          {/* Ce que FREK fait / ne fait pas */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            <div className="bg-[#0a1520]/50 rounded-xl p-5 sm:p-6 border border-[#2cc4f5]/10">
              <h3 className="font-mono text-xs sm:text-sm text-[#2cc4f5] uppercase tracking-wider mb-3">
                FREK Atteste
              </h3>
              <ul className="font-body text-sm text-[#8ab4c8]/70 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-[#2cc4f5] mt-1">•</span>
                  Une empreinte fréquentielle unique
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#2cc4f5] mt-1">•</span>
                  Un horodatage précis
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#2cc4f5] mt-1">•</span>
                  Un identifiant vérifiable
                </li>
              </ul>
            </div>
            
            <div className="bg-[#0a1520]/50 rounded-xl p-5 sm:p-6 border border-red-500/10">
              <h3 className="font-mono text-xs sm:text-sm text-red-400 uppercase tracking-wider mb-3">
                FREK N'atteste Pas
              </h3>
              <ul className="font-body text-sm text-[#8ab4c8]/70 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">•</span>
                  L'originalité ou la création
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">•</span>
                  La propriété intellectuelle
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">•</span>
                  La qualité artistique
                </li>
              </ul>
            </div>
          </section>

          {/* Confidentialité */}
          <section className="bg-[#0a1520]/50 rounded-xl p-6 sm:p-8 border border-[#2cc4f5]/10">
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Confidentialité
            </h2>
            <div className="font-body text-sm sm:text-base text-[#8ab4c8]/80 leading-relaxed space-y-4">
              <p>
                <strong className="text-[#2cc4f5]">Aucun fichier audio n'est stocké.</strong> Seule une 
                empreinte mathématique est conservée, ne permettant pas de reconstituer l'audio original.
              </p>
              <p>
                Les identifiants sont anonymes. Aucune donnée personnelle n'est collectée.
              </p>
            </div>
          </section>

          {/* Licence */}
          <section>
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Licence
            </h2>
            <p className="font-body text-sm sm:text-base text-[#8ab4c8]/80 leading-relaxed mb-4">
              FREK est un standard ouvert sous licence <strong className="text-[#2cc4f5]">CC BY 4.0</strong>.
            </p>
            <div className="font-mono text-xs text-[#8ab4c8]/40">
              © 2025–2026 CVLN Group · Bruxelles, Belgique
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#2cc4f5]/10 mt-auto">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 text-center">
          <div className="flex flex-wrap justify-center gap-4 sm:gap-6 mb-4">
            <Link to="/spec" className="font-mono text-[10px] sm:text-xs text-[#8ab4c8]/40 hover:text-[#2cc4f5]/70 uppercase tracking-wider transition-colors">
              Spécifications
            </Link>
            <Link to="/philosophy" className="font-mono text-[10px] sm:text-xs text-[#8ab4c8]/40 hover:text-[#2cc4f5]/70 uppercase tracking-wider transition-colors">
              Philosophie
            </Link>
          </div>
          <p className="font-mono text-[9px] sm:text-[10px] text-[#8ab4c8]/20 uppercase tracking-wider">
            © 2026 CVLN Group · frekcore.com
          </p>
        </div>
      </footer>
    </div>
  );
}

export default Legal;
