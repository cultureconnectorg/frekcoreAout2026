import { RevealWrapper } from '../ui/RevealWrapper';
import { SectionTag } from '../ui/SectionTag';
import { ecosystemData } from '../../data/ecosystem';

export function Ecosysteme() {
  return (
    <section id="ecosysteme" className="py-24 px-6 bg-navy">
      <div className="max-w-7xl mx-auto">
        <RevealWrapper>
          <SectionTag>Écosystème CVLN Group</SectionTag>
          <h2 className="font-display text-5xl md:text-6xl text-fwhite mb-4">
            FREK s&apos;intègre
          </h2>
          <p className="font-body text-lg text-mid max-w-2xl mb-12">
            FREK ne remplace rien. Il s&apos;insère comme couche de référence dans un
            écosystème déjà existant.
          </p>
        </RevealWrapper>

        <RevealWrapper delay={0.2}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {ecosystemData.map((item) => (
              <div
                key={item.name}
                className="group relative bg-dark p-6 border-t-2 border-t-transparent hover:border-t-terra transition-all duration-300 overflow-hidden"
              >
                {/* Animated border */}
                <div className="absolute top-0 left-0 w-0 h-[2px] bg-terra group-hover:w-full transition-all duration-500" />
                
                <span className="text-3xl mb-4 block">{item.icon}</span>
                <h3 className="font-display text-xl text-fwhite mb-1">{item.name}</h3>
                <p className="font-mono text-xs text-terra mb-4">{item.role}</p>
                <p className="font-body text-sm text-mid leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </RevealWrapper>
      </div>
    </section>
  );
}

export default Ecosysteme;
