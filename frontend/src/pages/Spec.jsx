/**
 * FREK v2 — Page Spécifications Techniques
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
            Architecture technique FREK v2.0
          </p>
        </div>

        <div className="space-y-8 sm:space-y-12">
          {/* Vecteur 528D */}
          <section className="bg-[#0a1520]/50 rounded-xl p-6 sm:p-8 border border-[#2cc4f5]/10">
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Vecteur Fréquentiel 528D
            </h2>
            <p className="font-body text-sm sm:text-base text-[#8ab4c8]/80 leading-relaxed mb-6">
              Chaque fichier audio est transformé en un vecteur de <strong className="text-[#2cc4f5]">528 dimensions</strong> :
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
              <div className="bg-[#050a0d]/50 rounded-lg p-3 sm:p-4 border border-[#2cc4f5]/5">
                <div className="font-mono text-2xl sm:text-3xl text-[#2cc4f5] mb-1">512</div>
                <div className="font-mono text-[9px] sm:text-[10px] text-[#8ab4c8]/50 uppercase">FFT Bands</div>
              </div>
              <div className="bg-[#050a0d]/50 rounded-lg p-3 sm:p-4 border border-[#2cc4f5]/5">
                <div className="font-mono text-2xl sm:text-3xl text-[#2cc4f5] mb-1">12</div>
                <div className="font-mono text-[9px] sm:text-[10px] text-[#8ab4c8]/50 uppercase">MFCC</div>
              </div>
              <div className="bg-[#050a0d]/50 rounded-lg p-3 sm:p-4 border border-[#2cc4f5]/5">
                <div className="font-mono text-2xl sm:text-3xl text-[#2cc4f5] mb-1">1</div>
                <div className="font-mono text-[9px] sm:text-[10px] text-[#8ab4c8]/50 uppercase">RMS</div>
              </div>
              <div className="bg-[#050a0d]/50 rounded-lg p-3 sm:p-4 border border-[#2cc4f5]/5">
                <div className="font-mono text-2xl sm:text-3xl text-[#2cc4f5] mb-1">1</div>
                <div className="font-mono text-[9px] sm:text-[10px] text-[#8ab4c8]/50 uppercase">ZCR</div>
              </div>
              <div className="bg-[#050a0d]/50 rounded-lg p-3 sm:p-4 border border-[#2cc4f5]/5">
                <div className="font-mono text-2xl sm:text-3xl text-[#2cc4f5] mb-1">1</div>
                <div className="font-mono text-[9px] sm:text-[10px] text-[#8ab4c8]/50 uppercase">Centroid</div>
              </div>
              <div className="bg-[#050a0d]/50 rounded-lg p-3 sm:p-4 border border-[#2cc4f5]/5">
                <div className="font-mono text-2xl sm:text-3xl text-[#2cc4f5] mb-1">1</div>
                <div className="font-mono text-[9px] sm:text-[10px] text-[#8ab4c8]/50 uppercase">Spectral Flux</div>
              </div>
            </div>
            <p className="font-mono text-xs text-[#8ab4c8]/40 mt-4">
              Total: 512 + 12 + 1 + 1 + 1 + 1 = 528 dimensions
            </p>
          </section>

          {/* FREK-ID */}
          <section>
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Format FREK-ID
            </h2>
            <div className="bg-[#0a1520]/50 rounded-xl p-5 sm:p-6 border border-[#2cc4f5]/10 mb-4">
              <code className="font-mono text-sm sm:text-base text-[#2cc4f5] break-all">
                FREK-{'{YYYY}'}-{'{NNNN}'}-{'{hash8}'}-{'{chain8}'}
              </code>
            </div>
            <div className="font-body text-sm text-[#8ab4c8]/70 space-y-2">
              <p><strong className="text-[#8ab4c8]">YYYY</strong> — Année de création</p>
              <p><strong className="text-[#8ab4c8]">NNNN</strong> — Numéro séquentiel (base 36)</p>
              <p><strong className="text-[#8ab4c8]">hash8</strong> — 8 premiers caractères du SHA-256 signal</p>
              <p><strong className="text-[#8ab4c8]">chain8</strong> — 8 premiers caractères du hash chaîné</p>
            </div>
          </section>

          {/* Architecture 11 Nœuds */}
          <section>
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Architecture 11 Nœuds
            </h2>
            <div className="space-y-3">
              {[
                { num: '01', name: 'EXTRACTION', desc: 'Audio → Vecteur 528D' },
                { num: '02', name: 'IDENTITÉ', desc: 'Triple SHA-256 → FREK-ID' },
                { num: '03', name: 'CYCLE', desc: '5 stades (Genesis → Legacy)' },
                { num: '04', name: 'MÉMOIRE', desc: 'pgvector ~2.5KB/œuvre' },
                { num: '05', name: 'RÉSONANCE', desc: 'Similarité, cohérence' },
                { num: '06', name: 'RÉSEAU', desc: 'Graphe relationnel' },
                { num: '07', name: 'TRANSMISSION', desc: 'Multi-protocole' },
                { num: '08', name: 'SYSTÈME', desc: 'Couche API' },
                { num: '09', name: 'JURIDIQUE', desc: 'Notaire de fait' },
                { num: '10', name: 'INSTITUTIONNEL', desc: 'Observatoire culturel' },
                { num: '11', name: 'INVISIBLE', desc: '3% visible · 1 bouton' },
              ].map((node) => (
                <div key={node.num} className="flex items-center gap-3 sm:gap-4 bg-[#0a1520]/30 rounded-lg p-3 sm:p-4 border border-[#2cc4f5]/5">
                  <div className="font-mono text-xs sm:text-sm text-[#2cc4f5]/50">{node.num}</div>
                  <div className="font-mono text-xs sm:text-sm text-[#2cc4f5] uppercase tracking-wider min-w-[100px] sm:min-w-[120px]">
                    {node.name}
                  </div>
                  <div className="font-body text-xs sm:text-sm text-[#8ab4c8]/60">
                    {node.desc}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Cycle de vie */}
          <section className="bg-[#0a1520]/50 rounded-xl p-6 sm:p-8 border border-[#2cc4f5]/10">
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Cycle de Vie (5 Stades)
            </h2>
            <div className="flex flex-wrap gap-2 sm:gap-3">
              {[
                { num: 1, name: 'GENESIS', color: 'from-violet-500/20 to-violet-500/5' },
                { num: 2, name: 'WORKSHOP', color: 'from-amber-500/20 to-amber-500/5' },
                { num: 3, name: 'METAMORPHOSE', color: 'from-emerald-500/20 to-emerald-500/5' },
                { num: 4, name: 'EMISSION', color: 'from-[#2cc4f5]/30 to-[#2cc4f5]/10' },
                { num: 5, name: 'LEGACY', color: 'from-rose-500/20 to-rose-500/5' },
              ].map((stade) => (
                <div key={stade.num} className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-full bg-gradient-to-r ${stade.color} border border-white/5`}>
                  <span className="font-mono text-xs text-white/40">{stade.num}</span>
                  <span className="font-mono text-[10px] sm:text-xs text-white/70 uppercase">{stade.name}</span>
                </div>
              ))}
            </div>
            <p className="font-body text-sm text-[#8ab4c8]/60 mt-4">
              L'EMISSION (stade 4) est <strong className="text-[#2cc4f5]">irréversible</strong> — une fois émise, 
              une attestation ne peut plus être modifiée.
            </p>
          </section>

          {/* Stack technique */}
          <section>
            <h2 className="font-mono text-sm sm:text-base text-[#2cc4f5] uppercase tracking-wider mb-4">
              Stack Technique
            </h2>
            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              <div className="bg-[#0a1520]/50 rounded-lg p-4 border border-[#2cc4f5]/10">
                <div className="font-mono text-xs text-[#2cc4f5]/50 uppercase mb-2">Backend</div>
                <div className="font-body text-sm text-[#8ab4c8]/70">FastAPI · Python 3</div>
              </div>
              <div className="bg-[#0a1520]/50 rounded-lg p-4 border border-[#2cc4f5]/10">
                <div className="font-mono text-xs text-[#2cc4f5]/50 uppercase mb-2">Frontend</div>
                <div className="font-body text-sm text-[#8ab4c8]/70">React 18 · Vite</div>
              </div>
              <div className="bg-[#0a1520]/50 rounded-lg p-4 border border-[#2cc4f5]/10">
                <div className="font-mono text-xs text-[#2cc4f5]/50 uppercase mb-2">Database</div>
                <div className="font-body text-sm text-[#8ab4c8]/70">PostgreSQL · pgvector</div>
              </div>
              <div className="bg-[#0a1520]/50 rounded-lg p-4 border border-[#2cc4f5]/10">
                <div className="font-mono text-xs text-[#2cc4f5]/50 uppercase mb-2">Audio</div>
                <div className="font-body text-sm text-[#8ab4c8]/70">librosa · numpy</div>
              </div>
            </div>
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

export default Spec;
