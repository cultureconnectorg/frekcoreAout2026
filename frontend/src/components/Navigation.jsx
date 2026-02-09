import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { useLanguage } from '../lib/LanguageContext';
import { LanguageSelector } from './LanguageSelector';
import { DOMAINS } from '../lib/domains';

export function Navigation({ currentPage }) {
  const { t } = useLanguage();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const docsUrl = DOMAINS.DOCS_BASE;

  const navItems = [
    { key: 'standard', path: '/standard', label: t.nav.standard },
    { key: 'manifesto', path: '/manifesto', label: t.nav.manifesto },
    { key: 'industry', path: '/industry', label: t.nav.industry },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#030303]/90 backdrop-blur-sm border-b border-zinc-900" role="navigation" aria-label="Main navigation">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <NavLink to="/" className="flex items-center gap-3" data-testid="nav-logo" aria-label="FREK Home">
          <img 
            src="/logo.svg" 
            alt="FREK Logo" 
            className="w-8 h-8"
          />
          <span className="font-mono font-bold text-lg tracking-tight text-white" aria-hidden="true">FREK</span>
        </NavLink>
        
        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-6">
          {navItems.map(item => (
            currentPage === item.key ? (
              <span key={item.key} className="font-mono text-sm text-white">
                {item.label}
              </span>
            ) : (
              <NavLink 
                key={item.key}
                to={item.path} 
                className="font-mono text-sm text-zinc-400 hover:text-white transition-colors"
              >
                {item.label}
              </NavLink>
            )
          ))}
          
          <a 
            href={docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-sm text-zinc-400 hover:text-white transition-colors"
          >
            {t.nav.developers}
          </a>
          
          {currentPage === 'verify' ? (
            <span className="font-mono text-sm px-4 py-2 bg-[#00F0FF] text-black">
              {t.nav.verify}
            </span>
          ) : (
            <NavLink 
              to="/verify" 
              className="font-mono text-sm px-4 py-2 bg-[#00F0FF] text-black hover:bg-[#00F0FF]/90 transition-colors"
              data-testid="nav-verify-btn"
            >
              {t.nav.verify}
            </NavLink>
          )}
          
          <LanguageSelector />
        </div>

        {/* Mobile Menu Button */}
        <div className="flex md:hidden items-center gap-4">
          <LanguageSelector />
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="text-zinc-400 hover:text-white"
            data-testid="mobile-menu-btn"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#030303] border-t border-zinc-900 px-6 py-4 space-y-4">
          {navItems.map(item => (
            <NavLink
              key={item.key}
              to={item.path}
              onClick={() => setMobileMenuOpen(false)}
              className={`block font-mono text-sm ${
                currentPage === item.key ? 'text-white' : 'text-zinc-400'
              }`}
            >
              {item.label}
            </NavLink>
          ))}
          <a 
            href={docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="block font-mono text-sm text-zinc-400"
          >
            {t.nav.developers}
          </a>
          <NavLink 
            to="/verify"
            onClick={() => setMobileMenuOpen(false)}
            className="block font-mono text-sm px-4 py-2 bg-[#00F0FF] text-black text-center"
          >
            {t.nav.verify}
          </NavLink>
        </div>
      )}
    </nav>
  );
}

export default Navigation;
