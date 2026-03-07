import { RevealWrapper } from '../ui/RevealWrapper';
import { SectionTag } from '../ui/SectionTag';

const steps = [
  {
    num: '01',
    label: 'Source',
    title: 'Capture',
    items: ['DJ Mix live', 'Performance scénique', 'Fichier audio'],
  },
  {
    num: '02',
    label: 'Traitement',
    title: 'Analyse',
    items: ['Machine locale', 'Hors réseau', 'Empreinte unique'],
  },
  {
    num: '03',
    label: 'Preuve',
    title: 'Attestation',
    items: ['FREK-ID unique', 'Horodatage précis', 'Vérifiable'],
  },
  {
    num: '04',
    label: 'Usage',
    title: 'Vérification',
    items: ['Comparaison possible', 'Décision humaine', 'Standard ouvert'],
  },
];

const responsibilities = [
  { role: 'Capture', who: 'Opérateur' },
  { role: 'Analyse', who: 'Automatique' },
  { role: 'Attestation', who: 'FREK' },
  { role: 'Interprétation', who: 'Humain' },
  { role: 'Décision', who: 'Humain' },
];

export function Architecture() {
  return (
    <section id="architecture" className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <RevealWrapper>
          <SectionTag>Comment ça fonctionne</SectionTag>
          <h2 className="font-display text-5xl md:text-6xl text-fwhite mb-4">
            Processus
          </h2>
        </RevealWrapper>

        {/* Flow Steps */}
        <RevealWrapper delay={0.2}>
          <div className="flex flex-nowrap gap-4 overflow-x-auto pb-4 mt-12 scrollbar-thin">
            {steps.map((step, index) => (
              <div key={step.num} className="flex items-center">
                <div className="min-w-[280px] p-6 bg-navy/50 border border-terra/15 hover:bg-navy/70 transition-colors">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="font-mono text-xs text-terra">{step.num}</span>
                    <span className="font-mono text-xs text-dim">·</span>
                    <span className="font-mono text-xs text-dim">{step.label}</span>
                  </div>
                  <h3 className="font-display text-2xl text-fwhite mb-4">{step.title}</h3>
                  <ul className="space-y-2">
                    {step.items.map((item) => (
                      <li key={item} className="font-mono text-xs text-mid flex items-start gap-2">
                        <span className="text-terra mt-0.5">→</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                {index < steps.length - 1 && (
                  <div className="flex-shrink-0 w-10 h-10 mx-2 rounded-full bg-terra/20 border border-terra/30 flex items-center justify-center">
                    <span className="text-terra">→</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </RevealWrapper>

        {/* Responsibilities */}
        <RevealWrapper delay={0.3}>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-12">
            {responsibilities.map((item) => (
              <div key={item.role} className="p-4 bg-dark border border-terra/10">
                <p className="font-mono text-xs text-terra mb-1">{item.role}</p>
                <p className="font-body text-sm text-mid">{item.who}</p>
              </div>
            ))}
          </div>
        </RevealWrapper>
      </div>
    </section>
  );
}

export default Architecture;
