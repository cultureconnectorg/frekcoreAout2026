import { RevealWrapper } from '../ui/RevealWrapper';
import { SectionTag } from '../ui/SectionTag';

const specFields = [
  { name: 'frek_id', type: 'string', desc: 'Identifiant unique FREK', required: true },
  { name: 'timestamp', type: 'number', desc: 'Horodatage de l\'attestation', required: true },
  { name: 'stade', type: 'number', desc: 'Stade du cycle de vie (1-5)', required: true },
  { name: 'artiste_id', type: 'string', desc: 'Identifiant anonyme', required: true },
  { name: 'hash', type: 'string', desc: 'Empreinte cryptographique', required: true },
];

const sampleFrekJson = `{
  "frek_id": "FREK-2026-001A-ab12cd34-ef567890",
  "timestamp": 1735689600000,
  "stade": 4,
  "artiste_id": "UUID-ANONYMOUS",
  "verified": true
}`;

export function Spec() {
  return (
    <section id="spec" className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <RevealWrapper>
          <SectionTag>Format d'attestation</SectionTag>
          <h2 className="font-display text-5xl md:text-6xl text-fwhite mb-12">
            Structure FREK
          </h2>
        </RevealWrapper>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Fields List */}
          <RevealWrapper delay={0.1}>
            <div className="space-y-3">
              {specFields.map((field) => (
                <div
                  key={field.name}
                  className="p-4 bg-navy/30 border border-terra/10 hover:bg-navy/50 transition-colors group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-sm text-gold">{field.name}</span>
                    <span
                      className={`px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${
                        field.required
                          ? 'bg-terra/20 text-terra'
                          : 'bg-dim/20 text-dim'
                      }`}
                    >
                      {field.required ? 'OBL' : 'OPT'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-dim">{field.type}</span>
                    <span className="text-terra/30">·</span>
                    <span className="font-body text-xs text-mid">{field.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </RevealWrapper>

          {/* Code Block - Sticky */}
          <RevealWrapper delay={0.2}>
            <div className="lg:sticky lg:top-24">
              <div className="bg-dark border border-terra/20 overflow-hidden">
                <div className="px-4 py-2 bg-navy border-b border-terra/20 font-mono text-xs text-terra">
                  attestation.json
                </div>
                <pre className="p-4 overflow-x-auto text-xs font-mono leading-relaxed max-h-[600px] overflow-y-auto">
                  <code>
                    {sampleFrekJson.split('\n').map((line, i) => {
                      let highlighted = line
                        .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
                        .replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>')
                        .replace(/: (\d+)/g, ': <span class="json-number">$1</span>')
                        .replace(/: (null|true|false)/g, ': <span class="json-number">$1</span>')
                        .replace(/([{}[\],])/g, '<span class="json-bracket">$1</span>');
                      
                      return (
                        <div key={i} dangerouslySetInnerHTML={{ __html: highlighted }} />
                      );
                    })}
                  </code>
                </pre>
              </div>
            </div>
          </RevealWrapper>
        </div>
      </div>
    </section>
  );
}

export default Spec;
