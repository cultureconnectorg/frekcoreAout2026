import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, Play, Code, Building2 } from 'lucide-react';
import { useLanguage } from '../lib/LanguageContext';
import { Navigation } from '../components/Navigation';
import { Footer } from '../components/Footer';
import { DOMAINS } from '../lib/domains';

export function PublicLanding() {
  const { t } = useLanguage();
  const docsUrl = DOMAINS.DOCS_BASE;
  
  return (
    <div className="min-h-screen bg-[#030303]">
      <Navigation currentPage="home" />

      {/* Hero Section */}
      <section className="min-h-screen flex items-center justify-center px-6 pt-16">
        <div className="max-w-4xl mx-auto text-center">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-zinc-600 mb-6">
            {t.landing.openProtocol}
          </p>
          
          <h1 className="font-serif text-5xl md:text-7xl lg:text-8xl font-light text-white mb-8 tracking-tight leading-[0.9]">
            {t.landing.title}
          </h1>
          
          <p className="font-serif text-2xl md:text-3xl text-zinc-300 mb-4 font-light">
            {t.landing.subtitle}
          </p>
          
          <p 
            className="font-sans text-lg md:text-xl text-zinc-500 max-w-2xl mx-auto mb-12"
            dangerouslySetInnerHTML={{ __html: t.landing.description }}
          />
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <NavLink 
              to="/verify"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-mono text-sm uppercase tracking-wide hover:bg-zinc-200 transition-colors"
              data-testid="hero-verify-btn"
            >
              <Play className="w-4 h-4" />
              {t.landing.verifyAudio}
            </NavLink>
            <NavLink 
              to="/industry"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border border-zinc-700 text-white font-mono text-sm uppercase tracking-wide hover:border-zinc-500 hover:bg-zinc-900/50 transition-colors"
            >
              <Building2 className="w-4 h-4" />
              {t.landing.industry}
            </NavLink>
            <a 
              href={docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border border-zinc-700 text-white font-mono text-sm uppercase tracking-wide hover:border-zinc-500 hover:bg-zinc-900/50 transition-colors"
              data-testid="hero-docs-btn"
            >
              <Code className="w-4 h-4" />
              {t.nav.developers}
            </a>
          </div>
        </div>
      </section>

      {/* What is FREK */}
      <section className="py-32 px-6 border-t border-zinc-900">
        <div className="max-w-4xl mx-auto">
          <p 
            className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-4"
            dangerouslySetInnerHTML={{ __html: t.landing.whatIs.section }}
          />
          <h2 
            className="font-serif text-3xl md:text-4xl text-white mb-8 font-light"
            dangerouslySetInnerHTML={{ __html: t.landing.whatIs.title }}
          />
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <p 
                className="text-zinc-400 text-lg leading-relaxed"
                dangerouslySetInnerHTML={{ __html: t.landing.whatIs.p1 }}
              />
            </div>
            <div>
              <p 
                className="text-zinc-400 text-lg leading-relaxed"
                dangerouslySetInnerHTML={{ __html: t.landing.whatIs.p2 }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Why it exists */}
      <section className="py-32 px-6 bg-[#050505]">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-4">
            {t.landing.why.section}
          </p>
          <h2 className="font-serif text-3xl md:text-4xl text-white mb-12 font-light">
            {t.landing.why.title}
          </h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-sm uppercase tracking-wide text-white mb-4">{t.landing.why.proof}</h3>
              <p 
                className="text-zinc-500"
                dangerouslySetInnerHTML={{ __html: t.landing.why.proofDesc }}
              />
            </div>
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-sm uppercase tracking-wide text-white mb-4">{t.landing.why.authorship}</h3>
              <p className="text-zinc-500">{t.landing.why.authorshipDesc}</p>
            </div>
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-sm uppercase tracking-wide text-white mb-4">{t.landing.why.neutrality}</h3>
              <p className="text-zinc-500">{t.landing.why.neutralityDesc}</p>
            </div>
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-sm uppercase tracking-wide text-white mb-4">{t.landing.why.privacy}</h3>
              <p 
                className="text-zinc-500"
                dangerouslySetInnerHTML={{ __html: t.landing.why.privacyDesc }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-32 px-6 border-t border-zinc-900">
        <div className="max-w-4xl mx-auto">
          <p 
            className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-4"
            dangerouslySetInnerHTML={{ __html: t.landing.useCases.section }}
          />
          <h2 
            className="font-serif text-3xl md:text-4xl text-white mb-12 font-light"
            dangerouslySetInnerHTML={{ __html: t.landing.useCases.title }}
          />
          
          <div className="space-y-6">
            <div className="flex items-start gap-6 p-6 border-l-2 border-zinc-800 hover:border-[#00F0FF] transition-colors">
              <div className="w-16 text-right">
                <span className="font-mono text-xs text-zinc-600">01</span>
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">{t.landing.useCases.djs}</h3>
                <p 
                  className="text-zinc-500"
                  dangerouslySetInnerHTML={{ __html: t.landing.useCases.djsDesc }}
                />
              </div>
            </div>
            
            <div className="flex items-start gap-6 p-6 border-l-2 border-zinc-800 hover:border-[#00F0FF] transition-colors">
              <div className="w-16 text-right">
                <span className="font-mono text-xs text-zinc-600">02</span>
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">{t.landing.useCases.labels}</h3>
                <p className="text-zinc-500">{t.landing.useCases.labelsDesc}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-6 p-6 border-l-2 border-zinc-800 hover:border-[#00F0FF] transition-colors">
              <div className="w-16 text-right">
                <span className="font-mono text-xs text-zinc-600">03</span>
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">{t.landing.useCases.dsps}</h3>
                <p className="text-zinc-500">{t.landing.useCases.dspsDesc}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-6 p-6 border-l-2 border-zinc-800 hover:border-[#00F0FF] transition-colors">
              <div className="w-16 text-right">
                <span className="font-mono text-xs text-zinc-600">04</span>
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">{t.landing.useCases.festivals}</h3>
                <p 
                  className="text-zinc-500"
                  dangerouslySetInnerHTML={{ __html: t.landing.useCases.festivalsDesc }}
                />
              </div>
            </div>
            
            <div className="flex items-start gap-6 p-6 border-l-2 border-zinc-800 hover:border-[#00F0FF] transition-colors">
              <div className="w-16 text-right">
                <span className="font-mono text-xs text-zinc-600">05</span>
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">{t.landing.useCases.archives}</h3>
                <p className="text-zinc-500">{t.landing.useCases.archivesDesc}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Sections */}
      <section className="py-32 px-6 bg-[#050505]">
        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8">
            {/* Live Demo */}
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A] flex flex-col">
              <div className="w-12 h-12 bg-[#00F0FF]/10 flex items-center justify-center mb-6">
                <Play className="w-6 h-6 text-[#00F0FF]" />
              </div>
              <h3 className="font-mono text-lg text-white mb-3">{t.landing.cta.verifyTitle}</h3>
              <p 
                className="text-zinc-500 text-sm mb-6 flex-1"
                dangerouslySetInnerHTML={{ __html: t.landing.cta.verifyDesc }}
              />
              <NavLink 
                to="/verify"
                className="inline-flex items-center gap-2 font-mono text-sm text-[#00F0FF] hover:underline"
              >
                {t.landing.cta.startVerification} <ArrowRight className="w-4 h-4" />
              </NavLink>
            </div>

            {/* Documentation */}
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A] flex flex-col">
              <div className="w-12 h-12 bg-zinc-800 flex items-center justify-center mb-6">
                <Code className="w-6 h-6 text-zinc-400" />
              </div>
              <h3 className="font-mono text-lg text-white mb-3">{t.landing.cta.devPortal}</h3>
              <p 
                className="text-zinc-500 text-sm mb-6 flex-1"
                dangerouslySetInnerHTML={{ __html: t.landing.cta.devPortalDesc }}
              />
              <a 
                href={docsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 font-mono text-sm text-zinc-400 hover:text-white hover:underline"
              >
                {t.landing.cta.openDevPortal} <ArrowRight className="w-4 h-4" />
              </a>
            </div>

            {/* Industry */}
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A] flex flex-col">
              <div className="w-12 h-12 bg-zinc-800 flex items-center justify-center mb-6">
                <Building2 className="w-6 h-6 text-zinc-400" />
              </div>
              <h3 className="font-mono text-lg text-white mb-3">{t.landing.cta.industryTitle}</h3>
              <p 
                className="text-zinc-500 text-sm mb-6 flex-1"
                dangerouslySetInnerHTML={{ __html: t.landing.cta.industryDesc }}
              />
              <NavLink 
                to="/industry"
                className="inline-flex items-center gap-2 font-mono text-sm text-zinc-400 hover:text-white hover:underline"
              >
                {t.landing.cta.learnMore} <ArrowRight className="w-4 h-4" />
              </NavLink>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

export default PublicLanding;
