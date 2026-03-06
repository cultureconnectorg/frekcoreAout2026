import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LanguageSwitcher } from '../ui/LanguageSwitcher';

export function Nav() {
  const { t } = useTranslation();
  const [isScrolled, setIsScrolled] = useState(false);

  const navLinks = [
    { label: t('philosophy.tag'), href: '#philosophie' },
    { label: t('nav.products'), href: '#produits' },
    { label: t('nav.verifier'), href: '#verifier' },
    { label: t('nav.generate'), href: '/generate', isRoute: true },
    { label: t('nav.spec'), href: '#spec' },
  ];

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (e, href) => {
    e.preventDefault();
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-dark/95 backdrop-blur-md border-b border-terra/20'
          : 'bg-dark/85 backdrop-blur-sm border-b border-terra/10'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <a href="#" className="flex items-baseline gap-0.5" aria-label="FREK Home">
          <span className="font-display text-2xl text-terra tracking-tight">FREK</span>
          <span className="font-display text-sm text-gold">®</span>
        </a>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            link.isRoute ? (
              <Link
                key={link.href}
                to={link.href}
                className="font-mono text-xs uppercase tracking-wider text-terra hover:text-gold transition-colors"
              >
                {link.label}
              </Link>
            ) : (
              <a
                key={link.href}
                href={link.href}
                onClick={(e) => scrollToSection(e, link.href)}
                className="font-mono text-xs uppercase tracking-wider text-mid hover:text-terra transition-colors"
              >
                {link.label}
              </a>
            )
          ))}
        </div>

        {/* Right side: Language + CTA */}
        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          <a
            href="#verifier"
            onClick={(e) => scrollToSection(e, '#verifier')}
            className="btn-primary text-xs hidden sm:inline-block"
          >
            {t('hero.verify')}
          </a>
        </div>
      </div>
    </nav>
  );
}

export default Nav;
