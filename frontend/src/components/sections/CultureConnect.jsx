import { RevealWrapper } from '../ui/RevealWrapper';

const attestationCards = [
  { id: 'FREK-2026-MQ-001', artist: 'Set Scène Principale', status: 'certified', badge: '✓ CERTIFIÉ' },
  { id: 'FREK-2026-MQ-002', artist: 'Set Scène Chimin', status: 'certified', badge: '✓ CERTIFIÉ' },
  { id: 'FREK-2026-MQ-003', artist: 'Set Late Night', status: 'pending', badge: '⟳ EN COURS' },
];

export function CultureConnect() {
  return (
    <section
      id="cc2026"
      className="py-24 px-6 border-y border-terra/15"
      style={{
        background: 'linear-gradient(135deg, rgba(196,113,74,0.03) 0%, transparent 50%)',
      }}
    >
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left - Text */}
          <RevealWrapper>
            <span className="inline-block px-4 py-2 bg-terra font-mono text-xs uppercase tracking-wider text-fwhite mb-6">
              PREMIER DÉPLOIEMENT OFFICIEL
            </span>
            <h2 className="font-display text-5xl md:text-6xl text-fwhite mb-6">
              Culture Connect{' '}
              <span className="text-terra">2026</span>
            </h2>
            <p className="font-body text-lg text-mid mb-8 leading-relaxed">
              Fort-de-France, Martinique — 20 au 23 mai 2026. Premier événement au monde
              où le standard FREK est déployé en conditions réelles. Tous les DJ sets certifiés
              FREK. La preuve de concept du standard.
            </p>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-dark border border-terra/10">
                <p className="font-display text-4xl text-terra">4</p>
                <p className="font-mono text-xs text-dim">Jours</p>
              </div>
              <div className="p-4 bg-dark border border-terra/10">
                <p className="font-display text-4xl text-terra">MQ</p>
                <p className="font-mono text-xs text-dim">Fort-de-France</p>
              </div>
              <div className="p-4 bg-dark border border-terra/10">
                <p className="font-display text-4xl text-terra">v0.5</p>
                <p className="font-mono text-xs text-dim">FREK actif</p>
              </div>
            </div>
          </RevealWrapper>

          {/* Right - Cards Stack */}
          <RevealWrapper delay={0.2}>
            <div className="relative">
              {attestationCards.map((card, index) => (
                <div
                  key={card.id}
                  className="relative bg-dark border border-terra/20 p-6 mb-4 last:mb-0"
                  style={{
                    transform: `translateX(${index * 8}px)`,
                    zIndex: attestationCards.length - index,
                  }}
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-sm text-terra">{card.id}</span>
                    <span
                      className={`px-3 py-1 font-mono text-xs ${
                        card.status === 'certified'
                          ? 'bg-fgreen/20 text-[#5DC882] border border-fgreen/30'
                          : 'bg-gold/20 text-gold border border-gold/30 animate-pulse'
                      }`}
                    >
                      {card.badge}
                    </span>
                  </div>
                  <p className="font-body text-mid">{card.artist}</p>
                </div>
              ))}
            </div>
          </RevealWrapper>
        </div>
      </div>
    </section>
  );
}

export default CultureConnect;
