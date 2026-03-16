const footerNav = [
  { label: 'Philosophie', href: '#philosophie' },
  { label: 'Architecture', href: '#architecture' },
  { label: 'FREK Go / Node', href: '#produits' },
  { label: 'Vérifier un mix', href: '#verifier' },
  { label: 'Spécification', href: '#spec' },
  { label: 'Écosystème', href: '#ecosysteme' },
];

const footerLinks = [
  { label: 'GitHub — frek-standard', href: 'https://github.com/cvln-group/frek-standard', external: true },
  { label: 'kiltikonet.fr', href: 'https://kiltikonet.fr', external: true },
  { label: 'Culture Connect 2026', href: '#cc2026' },
  { label: 'Charte Opérateur', href: '#' },
  { label: 'Whitepaper v0.4', href: '#' },
  { label: 'contact@frekcore.com', href: 'mailto:contact@frekcore.com' },
];

const pills = [
  'Protocole ouvert',
  'Aucun cookie',
  'Aucune donnée collectée',
  'Local-First',
];

export function Footer() {
  return (
    <footer className="bg-[#040404] border-t border-terra/15">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <img 
                src="/frek-logo.png" 
                alt="FREK" 
                className="h-12 w-auto"
              />
            </div>
            <p className="font-body text-sm text-dim leading-relaxed">
              Infrastructure de Preuve Audio Locale
              <br />
              Standard ouvert · Licence CC BY 4.0
              <br />
              © 2025–2026 FREK® / CVLN Group
              <br />
              Bruxelles, Belgique
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h3 className="font-mono text-xs uppercase tracking-wider text-mid mb-4">
              Navigation
            </h3>
            <ul className="space-y-2">
              {footerNav.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="font-body text-sm text-dim hover:text-terra transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Links */}
          <div>
            <h3 className="font-mono text-xs uppercase tracking-wider text-mid mb-4">
              Liens
            </h3>
            <ul className="space-y-2">
              {footerLinks.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    target={link.external ? '_blank' : undefined}
                    rel={link.external ? 'noopener noreferrer' : undefined}
                    className="font-body text-sm text-dim hover:text-terra transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-16 pt-8 border-t border-terra/10">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="font-mono text-xs text-dim">
              FREK® v0.4 · frekcore.com · CVLN Group Bruxelles
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <a href="/dashboard" className="px-3 py-1 bg-navy/50 border border-terra/10 font-mono text-xs text-dim rounded-full hover:text-terra hover:border-terra/30 transition-colors">
                Ops
              </a>
              {pills.map((pill) => (
                <span
                  key={pill}
                  className="px-3 py-1 bg-navy/50 border border-terra/10 font-mono text-xs text-dim rounded-full"
                >
                  {pill}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
