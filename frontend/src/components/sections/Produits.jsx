import { RevealWrapper } from '../ui/RevealWrapper';
import { SectionTag } from '../ui/SectionTag';

const frekGo = {
  eyebrow: 'Grand public · Artistes indépendants',
  name: 'FREK Go',
  badge: { text: 'PREUVE STANDARD', color: 'fgreen' },
  price: 'Gratuit',
  features: [
    'App mobile iOS/Android',
    'Interface web simplifiée',
    'Capture micro téléphone ou jack',
    'Analyse FFT automatique',
    'Signature Ed25519 artiste',
    'Ancrage RFC 3161 automatique',
    '.frek.json généré et signé',
    'Gratuit pour tous les artistes',
  ],
  proof: {
    label: 'Niveau de preuve',
    value: 'Standard — Archives personnelles, déclarations complémentaires',
  },
};

const frekNode = {
  eyebrow: 'Professionnel · Institutionnel',
  name: 'FREK Node',
  badge: { text: 'PREUVE FORTE', color: 'gold' },
  price: '99€/an',
  features: [
    'Machine dédiée locale (Mac/Linux)',
    'Mode hors réseau lors des analyses',
    'Capture temps réel flux continu',
    'Fingerprint multi-résolution 4 couches',
    'Empreinte acoustique de salle',
    'Cosignature multi-parties',
    'Triple ancrage : RFC 3161 + Bitcoin + GitHub',
    'Valeur institutionnelle maximale',
  ],
  proof: {
    label: 'Niveau de preuve',
    value: 'Fort — Festivals, droits ADAMI/SACEM, litiges contractuels',
  },
};

function ProductCard({ product, gradient }) {
  const badgeColors = {
    fgreen: 'bg-fgreen/20 text-[#5DC882] border-fgreen/30',
    gold: 'bg-gold/20 text-gold border-gold/30',
  };

  return (
    <div className="bg-dark flex flex-col">
      {/* Gradient Top Border */}
      <div className={`h-[3px] ${gradient}`} />
      
      <div className="p-8 flex-1 flex flex-col">
        <p className="font-mono text-xs text-terra mb-4">{product.eyebrow}</p>
        
        <h3 className="font-display text-5xl text-fwhite mb-4">{product.name}</h3>
        
        <span
          className={`inline-block self-start px-3 py-1 border font-mono text-xs uppercase tracking-wider mb-6 ${
            badgeColors[product.badge.color]
          }`}
        >
          {product.badge.text}
        </span>
        
        <p className="font-display text-4xl text-terra mb-8">{product.price}</p>
        
        <ul className="space-y-3 flex-1">
          {product.features.map((feature) => (
            <li key={feature} className="font-body text-sm text-mid flex items-start gap-3">
              <span className="text-terra mt-0.5">→</span>
              <span>{feature}</span>
            </li>
          ))}
        </ul>
        
        <div className="mt-8 p-4 border-l-2 border-terra bg-navy/30">
          <p className="font-mono text-xs text-dim mb-1">{product.proof.label}</p>
          <p className="font-body text-sm text-mid">{product.proof.value}</p>
        </div>
      </div>
    </div>
  );
}

export function Produits() {
  return (
    <section id="produits" className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <RevealWrapper>
          <SectionTag>Deux produits, un standard</SectionTag>
          <h2 className="font-display text-5xl md:text-6xl text-fwhite mb-4">
            FREK Go &amp; FREK Node
          </h2>
          <p className="font-body text-lg text-mid max-w-3xl mb-12">
            L&apos;architecture professionnelle est préservée. La facilité d&apos;accès aussi.
            Deux produits distincts, deux niveaux de preuve, une seule spécification.
          </p>
        </RevealWrapper>

        <RevealWrapper delay={0.2}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-terra">
            <ProductCard
              product={frekGo}
              gradient="bg-gradient-to-r from-teal to-terra"
            />
            <ProductCard
              product={frekNode}
              gradient="bg-gradient-to-r from-terra to-gold"
            />
          </div>
        </RevealWrapper>
      </div>
    </section>
  );
}

export default Produits;
