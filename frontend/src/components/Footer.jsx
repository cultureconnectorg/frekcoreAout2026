import React from 'react';
import { NavLink } from 'react-router-dom';
import { useLanguage } from '../lib/LanguageContext';
import { DOMAINS } from '../lib/domains';

export function Footer() {
  const { t } = useLanguage();
  const docsUrl = DOMAINS.DOCS_BASE;

  return (
    <footer className="py-16 px-6 border-t border-zinc-900">
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <img src="/logo.svg" alt="FREK" className="w-6 h-6" />
              <span className="font-mono font-bold text-white">FREK</span>
              <span className="font-mono text-xs text-zinc-600">v0.4</span>
            </div>
            <p className="font-mono text-xs text-zinc-600 max-w-xs">
              {t.landing.footer.tagline}
            </p>
          </div>
          
          <div className="flex gap-8">
            <div>
              <p className="font-mono text-xs uppercase tracking-wide text-zinc-600 mb-3">
                {t.landing.footer.protocol}
              </p>
              <div className="space-y-2">
                <a 
                  href={docsUrl} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="block font-mono text-sm text-zinc-500 hover:text-white"
                >
                  {t.landing.footer.documentation}
                </a>
                <a 
                  href={`${docsUrl}/spec`} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="block font-mono text-sm text-zinc-500 hover:text-white"
                >
                  {t.landing.footer.specification}
                </a>
                <a 
                  href={`${docsUrl}/changelog`} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="block font-mono text-sm text-zinc-500 hover:text-white"
                >
                  {t.landing.footer.changelog}
                </a>
              </div>
            </div>
            <div>
              <p className="font-mono text-xs uppercase tracking-wide text-zinc-600 mb-3">
                {t.landing.footer.resources}
              </p>
              <div className="space-y-2">
                <NavLink to="/verify" className="block font-mono text-sm text-zinc-500 hover:text-white">
                  {t.landing.footer.verifyTool}
                </NavLink>
                <NavLink to="/standard" className="block font-mono text-sm text-zinc-500 hover:text-white">
                  {t.nav.standard}
                </NavLink>
                <NavLink to="/manifesto" className="block font-mono text-sm text-zinc-500 hover:text-white">
                  {t.nav.manifesto}
                </NavLink>
                <NavLink to="/industry" className="block font-mono text-sm text-zinc-500 hover:text-white">
                  {t.nav.industry}
                </NavLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
