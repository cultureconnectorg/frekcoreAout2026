import { RevealWrapper } from '../ui/RevealWrapper';
import { SectionTag } from '../ui/SectionTag';

const pillars = [
  {
    num: '01',
    title: 'Preuve > Service',
    text: "FREK produit des preuves vérifiables, pas des services qui créent de la dépendance. Une attestation FREK est valide hors ligne, sans compte, sans abonnement — à jamais.",
  },
  {
    num: '02',
    title: 'Local-First',
    text: "L'analyse audio, la génération d'empreinte et la signature cryptographique se déroulent sur une machine locale, hors réseau. Aucun fichier audio ne quitte jamais votre machine.",
  },
  {
    num: '03',
    title: 'Anti-Surveillance',
    text: "FREK ne compare pas l'audio à une base d'œuvres. Il ne reconnaît pas la musique. Il reconnaît un fait technique dans un contexte précis. Ce n'est pas du DRM.",
  },
];

export function Philosophie() {
  return (
    <section
      id="philosophie"
      className="py-24 px-6 bg-navy border-y border-terra/15"
    >
      <div className="max-w-7xl mx-auto">
        <RevealWrapper>
          <SectionTag>Pourquoi FREK existe</SectionTag>
          <h2 className="font-display text-5xl md:text-6xl text-fwhite mb-8">
            La philosophie
          </h2>
          <p className="font-body text-lg text-mid max-w-3xl mb-16 leading-relaxed">
            Un titre enregistré a un ISRC. Un album a un UPC. Un DJ mix contenant 80 œuvres
            de 80 artistes n&apos;a aucun identifiant reconnu. FREK comble ce vide — sans devenir
            le problème qu&apos;il résout.
          </p>
        </RevealWrapper>

        {/* Three Pillars */}
        <RevealWrapper delay={0.2}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border border-terra/15">
            {pillars.map((pillar, index) => (
              <div
                key={pillar.num}
                className={`relative p-8 bg-dark/30 hover:bg-dark/50 transition-colors ${
                  index < pillars.length - 1 ? 'md:border-r border-b md:border-b-0 border-terra/15' : ''
                }`}
              >
                <span className="absolute top-4 right-4 font-display text-7xl text-terra/15">
                  {pillar.num}
                </span>
                <h3 className="font-display text-2xl text-terra mb-4 relative z-10">
                  {pillar.title}
                </h3>
                <p className="font-body text-mid text-sm leading-relaxed relative z-10">
                  {pillar.text}
                </p>
              </div>
            ))}
          </div>
        </RevealWrapper>

        {/* Emphasis Block */}
        <RevealWrapper delay={0.3}>
          <div className="mt-12 p-6 bg-dark/60 border-l-[3px] border-terra">
            <p className="font-mono text-sm text-light">
              <strong className="text-fwhite">FREK ne reconnaît pas la musique.</strong>
              <br />
              FREK reconnaît un fait technique, dans un contexte précis.
            </p>
          </div>
        </RevealWrapper>
      </div>
    </section>
  );
}

export default Philosophie;
