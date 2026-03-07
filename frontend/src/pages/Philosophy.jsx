/**
 * FREK v2 — Page Philosophie
 * La vision et les principes fondateurs
 */
import { Link } from 'react-router-dom';

export function Philosophy() {
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
            Philosophie
          </h1>
          <p className="font-mono text-xs sm:text-sm text-[#8ab4c8]/60 uppercase tracking-wider">
            La luciole — 3% visible, 97% invisible
          </p>
        </div>

        <div className="space-y-8 sm:space-y-12">
          {/* Citation principale */}
          <section className="bg-gradient-to-br from-[#2cc4f5]/10 to-transparent rounded-2xl p-8 sm:p-12 border border-[#2cc4f5]/20">
            <blockquote className="font-display text-xl sm:text-2xl md:text-3xl text-[#2cc4f5] leading-relaxed text-center">
              "FREK atteste un fait technique — jamais un droit."
            </blockquote>
            <p className="font-mono text-xs text-[#8ab4c8]/40 text-center mt-6 uppercase tracking-wider">
              Principe fondateur
            </p>
          </section>

          {/* Pourquoi FREK */}
          <section>
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Pourquoi FREK ?
            </h2>
            <div className="font-body text-sm sm:text-base text-[#8ab4c8]/80 leading-relaxed space-y-4">
              <p>
                Dans un monde où la musique électronique et les DJ mixes se partagent instantanément, 
                il manquait un système simple pour <strong className="text-[#2cc4f5]">prouver l'existence</strong> 
                d'une création sonore à un instant précis — sans surveillance, sans collecte de données, 
                sans jugement artistique.
              </p>
              <p>
                FREK répond à ce besoin avec une approche radicalement minimaliste : 
                <strong className="text-[#2cc4f5]"> un bouton, trois secondes, une preuve immuable.</strong>
              </p>
            </div>
          </section>

          {/* Métaphore de la luciole */}
          <section className="bg-[#0a1520]/50 rounded-xl p-6 sm:p-8 border border-[#2cc4f5]/10">
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              La Métaphore de la Luciole
            </h2>
            <div className="font-body text-sm sm:text-base text-[#8ab4c8]/80 leading-relaxed space-y-4">
              <p>
                Comme une luciole qui ne révèle que <strong className="text-[#2cc4f5]">3% de sa lumière</strong> 
                au monde extérieur, FREK ne montre que l'essentiel : un identifiant unique et vérifiable.
              </p>
              <p>
                Les 97% restants — l'architecture complexe des 11 nœuds, les calculs vectoriels, 
                le chaînage cryptographique — restent invisibles. L'utilisateur n'a pas besoin de 
                comprendre la mécanique pour bénéficier de la preuve.
              </p>
            </div>
          </section>

          {/* Principes */}
          <section>
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-6">
              Principes Fondateurs
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-[#0a1520]/50 rounded-xl p-5 sm:p-6 border border-[#2cc4f5]/10">
                <div className="font-mono text-lg sm:text-xl text-[#2cc4f5] mb-2">Preuve {'>'} Service</div>
                <p className="font-body text-sm text-[#8ab4c8]/60">
                  FREK prouve l'existence d'un fait, pas la légitimité d'un droit.
                </p>
              </div>
              <div className="bg-[#0a1520]/50 rounded-xl p-5 sm:p-6 border border-[#2cc4f5]/10">
                <div className="font-mono text-lg sm:text-xl text-[#2cc4f5] mb-2">Local-First</div>
                <p className="font-body text-sm text-[#8ab4c8]/60">
                  Aucun fichier audio n'est jamais uploadé ni stocké. Traitement local.
                </p>
              </div>
              <div className="bg-[#0a1520]/50 rounded-xl p-5 sm:p-6 border border-[#2cc4f5]/10">
                <div className="font-mono text-lg sm:text-xl text-[#2cc4f5] mb-2">Anti-Surveillance</div>
                <p className="font-body text-sm text-[#8ab4c8]/60">
                  Pas de cookies, pas de tracking, identifiants anonymes uniquement.
                </p>
              </div>
              <div className="bg-[#0a1520]/50 rounded-xl p-5 sm:p-6 border border-[#2cc4f5]/10">
                <div className="font-mono text-lg sm:text-xl text-[#2cc4f5] mb-2">Standard Ouvert</div>
                <p className="font-body text-sm text-[#8ab4c8]/60">
                  Architecture publique, licence CC BY 4.0, interopérable.
                </p>
              </div>
            </div>
          </section>

          {/* Culture Connect 2026 */}
          <section className="bg-gradient-to-r from-[#2cc4f5]/5 to-transparent rounded-xl p-6 sm:p-8 border border-[#2cc4f5]/10">
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Culture Connect 2026
            </h2>
            <p className="font-body text-sm sm:text-base text-[#8ab4c8]/80 leading-relaxed">
              Premier déploiement officiel à <strong className="text-[#2cc4f5]">Fort-de-France, Martinique</strong> 
              dans le cadre de Culture Connect 2026. FREK permettra aux artistes locaux de certifier 
              leurs créations dans un cadre de confiance et de souveraineté numérique.
            </p>
          </section>

          {/* Qui sommes-nous */}
          <section>
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              CVLN Group
            </h2>
            <p className="font-body text-sm sm:text-base text-[#8ab4c8]/80 leading-relaxed">
              FREK est développé par <strong className="text-[#2cc4f5]">CVLN Group</strong>, basé à Bruxelles, 
              en collaboration avec <strong className="text-[#2cc4f5]">Kilti Konet</strong> et 
              <strong className="text-[#2cc4f5]"> Factory Maker Studio</strong>.
            </p>
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
            <Link to="/legal" className="font-mono text-[10px] sm:text-xs text-[#8ab4c8]/40 hover:text-[#2cc4f5]/70 uppercase tracking-wider transition-colors">
              Cadre Juridique
            </Link>
            <Link to="/about" className="font-mono text-[10px] sm:text-xs text-[#8ab4c8]/40 hover:text-[#2cc4f5]/70 uppercase tracking-wider transition-colors">
              Architecture
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

export default Philosophy;
