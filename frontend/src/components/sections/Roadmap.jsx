import { RevealWrapper } from '../ui/RevealWrapper';
import { SectionTag } from '../ui/SectionTag';
import { roadmapData } from '../../data/roadmap';

export function Roadmap() {
  const statusStyles = {
    current: 'bg-terra/20',
    dev: 'bg-gold/10',
    plan: 'bg-dim/10',
  };

  const statusBadgeStyles = {
    current: 'bg-terra/20 text-terra border-terra/30',
    dev: 'bg-gold/20 text-gold border-gold/30',
    plan: 'bg-dim/20 text-dim border-dim/30',
  };

  return (
    <section id="roadmap" className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <RevealWrapper>
          <SectionTag>Feuille de route</SectionTag>
          <h2 className="font-display text-5xl md:text-6xl text-fwhite mb-12">
            De spec à standard
          </h2>
        </RevealWrapper>

        <RevealWrapper delay={0.2}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {roadmapData.map((item) => (
              <div
                key={item.version}
                className={`p-6 border border-terra/10 ${statusStyles[item.status]}`}
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="font-display text-3xl text-fwhite">{item.version}</span>
                  <span
                    className={`px-2 py-1 font-mono text-[10px] uppercase tracking-wider border ${
                      statusBadgeStyles[item.status]
                    }`}
                  >
                    {item.statusLabel}
                  </span>
                </div>
                <p className="font-mono text-xs text-terra mb-4">{item.period}</p>
                <ul className="space-y-2">
                  {item.items.map((task) => (
                    <li key={task} className="font-body text-sm text-mid flex items-start gap-2">
                      <span className="text-terra mt-0.5">·</span>
                      <span>{task}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </RevealWrapper>
      </div>
    </section>
  );
}

export default Roadmap;
