import { RevealWrapper } from '../ui/RevealWrapper';
import { SectionTag } from '../ui/SectionTag';

const frekIdParts = [
  { label: 'Préfixe', value: 'FREK', desc: 'Constant — identifie le standard', color: 'text-fwhite' },
  { label: 'Année', value: 'YYYY', desc: 'Année de la performance', color: 'text-gold' },
  { label: 'Territoire', value: 'XX', desc: 'ISO 3166-1 alpha-2 (MQ, FR, CO…)', color: 'text-terra' },
  { label: 'Numéro', value: 'NNN', desc: 'Séquentiel — minimum 3 chiffres', color: 'text-mid' },
];

export function FrekId() {
  return (
    <section id="frek-id" className="py-24 px-6 bg-navy/20">
      <div className="max-w-5xl mx-auto">
        <RevealWrapper>
          <SectionTag>Format de l&apos;identifiant</SectionTag>
          <h2 className="font-display text-5xl md:text-6xl text-fwhite mb-12">
            FREK-ID
          </h2>
        </RevealWrapper>

        {/* Large Display */}
        <RevealWrapper delay={0.1}>
          <div className="flex flex-wrap items-center justify-center gap-2 md:gap-4 mb-16">
            <span className="font-display text-5xl md:text-7xl text-fwhite">FREK</span>
            <span className="font-display text-5xl md:text-7xl text-terra">–</span>
            <span className="font-display text-5xl md:text-7xl text-gold">2026</span>
            <span className="font-display text-5xl md:text-7xl text-terra">–</span>
            <span className="font-display text-5xl md:text-7xl text-terra">MQ</span>
            <span className="font-display text-5xl md:text-7xl text-terra">–</span>
            <span className="font-display text-5xl md:text-7xl text-mid">001</span>
          </div>
        </RevealWrapper>

        {/* Parts Grid */}
        <RevealWrapper delay={0.2}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {frekIdParts.map((part) => (
              <div key={part.label} className="p-6 bg-dark border border-terra/10">
                <p className="font-mono text-xs text-dim mb-2">{part.label}</p>
                <p className={`font-display text-3xl ${part.color} mb-2`}>{part.value}</p>
                <p className="font-body text-xs text-mid">{part.desc}</p>
              </div>
            ))}
          </div>
        </RevealWrapper>
      </div>
    </section>
  );
}

export default FrekId;
