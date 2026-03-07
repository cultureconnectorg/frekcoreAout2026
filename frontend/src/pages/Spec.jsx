/**
 * FREK v2 — Page Spécifications
 * Version publique simplifiée
 */
import { Link } from 'react-router-dom';

export function Spec() {
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
            Spécifications
          </h1>
          <p className="font-mono text-xs sm:text-sm text-[#8ab4c8]/60 uppercase tracking-wider">
            Standard FREK v2.0
          </p>
        </div>

        <div className="space-y-8 sm:space-y-12">
          {/* Principe */}
          <section className="bg-[#0a1520]/50 rounded-xl p-6 sm:p-8 border border-[#2cc4f5]/10">
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Certification Fréquentielle
            </h2>
            <p className="font-body text-sm sm:text-base text-[#8ab4c8]/80 leading-relaxed">
              FREK transforme chaque fichier audio en une <strong className="text-[#2cc4f5]">empreinte unique</strong> — 
              un vecteur mathématique qui caractérise la signature fréquentielle de l'œuvre sans permettre 
              sa reconstitution.
            </p>
          </section>

          {/* FREK-ID */}
          <section>
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Format FREK-ID
            </h2>
            <div className="bg-[#0a1520]/50 rounded-xl p-5 sm:p-6 border border-[#2cc4f5]/10 mb-4">
              <code className="font-mono text-sm sm:text-base text-[#2cc4f5] break-all">
                FREK-{'{YYYY}'}-{'{NNNN}'}-{'{hash}'}-{'{chain}'}
              </code>
            </div>
            <div className="font-body text-sm text-[#8ab4c8]/70 space-y-2">
              <p><strong className="text-[#8ab4c8]">YYYY</strong> — Année de création</p>
              <p><strong className="text-[#8ab4c8]">NNNN</strong> — Numéro séquentiel</p>
              <p><strong className="text-[#8ab4c8]">hash</strong> — Empreinte cryptographique</p>
              <p><strong className="text-[#8ab4c8]">chain</strong> — Lien de chaînage</p>
            </div>
          </section>

          {/* Cycle de vie */}
          <section className="bg-[#0a1520]/50 rounded-xl p-6 sm:p-8 border border-[#2cc4f5]/10">
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Cycle de Vie
            </h2>
            <div className="flex flex-wrap gap-2 sm:gap-3">
              {[
                { num: 1, name: 'GENESIS' },
                { num: 2, name: 'WORKSHOP' },
                { num: 3, name: 'METAMORPHOSE' },
                { num: 4, name: 'EMISSION' },
                { num: 5, name: 'LEGACY' },
              ].map((stade) => (
                <div key={stade.num} className="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-full bg-[#2cc4f5]/10 border border-[#2cc4f5]/20">
                  <span className="font-mono text-xs text-[#2cc4f5]/50">{stade.num}</span>
                  <span className="font-mono text-[10px] sm:text-xs text-[#2cc4f5] uppercase">{stade.name}</span>
                </div>
              ))}
            </div>
            <p className="font-body text-sm text-[#8ab4c8]/60 mt-4">
              L'EMISSION est <strong className="text-[#2cc4f5]">irréversible</strong> — une fois émise, 
              une attestation ne peut plus être modifiée.
            </p>
          </section>

          {/* Garanties */}
          <section>
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Garanties
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div className="bg-[#0a1520]/50 rounded-lg p-4 border border-[#2cc4f5]/10">
                <div className="font-mono text-sm text-[#2cc4f5] mb-2">Unicité</div>
                <p className="font-body text-xs text-[#8ab4c8]/60">Chaque FREK-ID est unique et vérifiable</p>
              </div>
              <div className="bg-[#0a1520]/50 rounded-lg p-4 border border-[#2cc4f5]/10">
                <div className="font-mono text-sm text-[#2cc4f5] mb-2">Horodatage</div>
                <p className="font-body text-xs text-[#8ab4c8]/60">Timestamp précis de l'attestation</p>
              </div>
              <div className="bg-[#0a1520]/50 rounded-lg p-4 border border-[#2cc4f5]/10">
                <div className="font-mono text-sm text-[#2cc4f5] mb-2">Chaînage</div>
                <p className="font-body text-xs text-[#8ab4c8]/60">Attestations liées cryptographiquement</p>
              </div>
              <div className="bg-[#0a1520]/50 rounded-lg p-4 border border-[#2cc4f5]/10">
                <div className="font-mono text-sm text-[#2cc4f5] mb-2">Immuabilité</div>
                <p className="font-body text-xs text-[#8ab4c8]/60">Impossible de modifier une émission</p>
              </div>
            </div>
          </section>

          {/* Standard ouvert */}
          <section className="bg-gradient-to-r from-[#2cc4f5]/5 to-transparent rounded-xl p-6 sm:p-8 border border-[#2cc4f5]/10">
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Standard Ouvert
            </h2>
            <p className="font-body text-sm sm:text-base text-[#8ab4c8]/80 leading-relaxed">
              FREK est un protocole ouvert sous licence <strong className="text-[#2cc4f5]">CC BY 4.0</strong>. 
              Les spécifications d'interopérabilité sont disponibles pour les opérateurs agréés.
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#2cc4f5]/10 mt-auto">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 text-center">
          <div className="flex flex-wrap justify-center gap-4 sm:gap-6 mb-4">
            <Link to="/legal" className="font-mono text-[10px] sm:text-xs text-[#8ab4c8]/40 hover:text-[#2cc4f5]/70 uppercase tracking-wider transition-colors">
              Cadre Juridique
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

export default Spec;
