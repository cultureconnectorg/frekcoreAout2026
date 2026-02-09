import React from 'react';
import { ArrowRight, Check, Lock, Scale, Globe, Mail } from 'lucide-react';
import { useLanguage } from '../lib/LanguageContext';
import { Navigation } from '../components/Navigation';
import { Footer } from '../components/Footer';
import { DOMAINS } from '../lib/domains';

export function Industry() {
  const { t } = useLanguage();
  const docsUrl = DOMAINS.DOCS_BASE;
  
  return (
    <div className="min-h-screen bg-[#030303]">
      <Navigation currentPage="industry" />

      {/* Hero */}
      <section className="pt-32 pb-20 px-6 border-b border-zinc-900">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-6">
            {t.industry.section}
          </p>
          <h1 
            className="font-serif text-4xl md:text-5xl lg:text-6xl text-white mb-6 font-light leading-tight"
            dangerouslySetInnerHTML={{ __html: t.industry.title }}
          />
          <p 
            className="text-xl text-zinc-400 max-w-2xl"
            dangerouslySetInnerHTML={{ __html: t.industry.description }}
          />
        </div>
      </section>

      {/* Infrastructure Layer */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-zinc-600 mb-4">
            {t.industry.infrastructure}
          </p>
          <h2 className="font-serif text-3xl text-white mb-8 font-light">
            {t.industry.infraTitle}
          </h2>
          
          <div className="grid md:grid-cols-2 gap-12 mb-12">
            <div>
              <p 
                className="text-zinc-400 leading-relaxed mb-6"
                dangerouslySetInnerHTML={{ __html: t.industry.infraP1 }}
              />
              <p 
                className="text-zinc-400 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: t.industry.infraP2 }}
              />
            </div>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
              <p className="font-mono text-xs uppercase tracking-wide text-zinc-600 mb-4">
                {t.industry.architecture}
              </p>
              <div className="space-y-3 font-mono text-sm">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#00F0FF]"></div>
                  <span className="text-zinc-400">{t.industry.localFirst}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#00F0FF]"></div>
                  <span className="text-zinc-400">{t.industry.ed25519}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#00F0FF]"></div>
                  <span className="text-zinc-400">{t.industry.sha256}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#00F0FF]"></div>
                  <span className="text-zinc-400">{t.industry.jsonFormat}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#00F0FF]"></div>
                  <span className="text-zinc-400">{t.industry.noAuthority}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Neutral Standard */}
      <section className="py-24 px-6 bg-[#050505]">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-zinc-600 mb-4">
            {t.industry.neutrality}
          </p>
          <h2 className="font-serif text-3xl text-white mb-8 font-light">
            {t.industry.neutralTitle}
          </h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <Lock className="w-8 h-8 text-zinc-600 mb-4" />
              <h3 className="font-mono text-white mb-2">{t.industry.noLockIn}</h3>
              <p className="text-zinc-500 text-sm">{t.industry.noLockInDesc}</p>
            </div>
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <Scale className="w-8 h-8 text-zinc-600 mb-4" />
              <h3 className="font-mono text-white mb-2">{t.industry.governance}</h3>
              <p className="text-zinc-500 text-sm">{t.industry.governanceDesc}</p>
            </div>
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <Globe className="w-8 h-8 text-zinc-600 mb-4" />
              <h3 className="font-mono text-white mb-2">{t.industry.agnostic}</h3>
              <p className="text-zinc-500 text-sm">{t.industry.agnosticDesc}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Adoption Benefits */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-zinc-600 mb-4">
            {t.industry.benefits}
          </p>
          <h2 className="font-serif text-3xl text-white mb-12 font-light">
            {t.industry.benefitsTitle}
          </h2>
          
          <div className="space-y-8">
            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00F0FF]/10 flex items-center justify-center flex-shrink-0">
                <Check className="w-6 h-6 text-[#00F0FF]" />
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">{t.industry.benefit1}</h3>
                <p className="text-zinc-500">{t.industry.benefit1Desc}</p>
              </div>
            </div>
            
            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00F0FF]/10 flex items-center justify-center flex-shrink-0">
                <Check className="w-6 h-6 text-[#00F0FF]" />
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">{t.industry.benefit2}</h3>
                <p className="text-zinc-500">{t.industry.benefit2Desc}</p>
              </div>
            </div>
            
            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00F0FF]/10 flex items-center justify-center flex-shrink-0">
                <Check className="w-6 h-6 text-[#00F0FF]" />
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">{t.industry.benefit3}</h3>
                <p className="text-zinc-500">{t.industry.benefit3Desc}</p>
              </div>
            </div>
            
            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00F0FF]/10 flex items-center justify-center flex-shrink-0">
                <Check className="w-6 h-6 text-[#00F0FF]" />
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">{t.industry.benefit4}</h3>
                <p className="text-zinc-500">{t.industry.benefit4Desc}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Integration Scenarios */}
      <section className="py-24 px-6 bg-[#050505]">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-zinc-600 mb-4">
            {t.industry.integration}
          </p>
          <h2 className="font-serif text-3xl text-white mb-12 font-light">
            {t.industry.integrationTitle}
          </h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-lg text-white mb-4">{t.industry.streaming}</h3>
              <ul className="space-y-3 text-zinc-500 text-sm">
                {t.industry.streamingItems.map((item, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-[#00F0FF]">-</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-lg text-white mb-4">{t.industry.recordLabels}</h3>
              <ul className="space-y-3 text-zinc-500 text-sm">
                {t.industry.recordLabelsItems.map((item, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-[#00F0FF]">-</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-lg text-white mb-4">{t.industry.daw}</h3>
              <ul className="space-y-3 text-zinc-500 text-sm">
                {t.industry.dawItems.map((item, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-[#00F0FF]">-</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-lg text-white mb-4">{t.industry.archivesLib}</h3>
              <ul className="space-y-3 text-zinc-500 text-sm">
                {t.industry.archivesLibItems.map((item, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-[#00F0FF]">-</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Governance */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-zinc-600 mb-4">
            {t.industry.governanceSection}
          </p>
          <h2 className="font-serif text-3xl text-white mb-8 font-light">
            {t.industry.governanceTitle}
          </h2>
          
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <p className="text-zinc-400 leading-relaxed mb-6">
                {t.industry.governanceP1}
              </p>
              <ul className="space-y-3 text-zinc-500">
                {t.industry.governanceItems.map((item, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-[#00F0FF]">*</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
              <p className="font-mono text-xs uppercase tracking-wide text-zinc-600 mb-4">
                Governance Principles
              </p>
              <div className="space-y-4">
                <div>
                  <p className="font-mono text-sm text-white">{t.industry.visionLayer}</p>
                  <p className="text-zinc-600 text-sm">{t.industry.visionLayerDesc}</p>
                </div>
                <div className="border-t border-zinc-800 pt-4">
                  <p className="font-mono text-sm text-white">{t.industry.specLayer}</p>
                  <p className="text-zinc-600 text-sm">{t.industry.specLayerDesc}</p>
                </div>
                <div className="border-t border-zinc-800 pt-4">
                  <p className="font-mono text-sm text-white">{t.industry.implLayer}</p>
                  <p className="text-zinc-600 text-sm">{t.industry.implLayerDesc}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="py-24 px-6 bg-[#050505]">
        <div className="max-w-4xl mx-auto text-center">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-zinc-600 mb-4">
            {t.industry.partnership}
          </p>
          <h2 className="font-serif text-3xl text-white mb-6 font-light">
            {t.industry.partnershipTitle}
          </h2>
          <p className="text-zinc-400 mb-8 max-w-xl mx-auto">
            {t.industry.partnershipDesc}
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="mailto:contact@frek.org"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-mono text-sm uppercase tracking-wide hover:bg-zinc-200 transition-colors"
            >
              <Mail className="w-4 h-4" />
              {t.industry.contactPartnership}
            </a>
            <a 
              href={docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border border-zinc-700 text-white font-mono text-sm uppercase tracking-wide hover:border-zinc-500 transition-colors"
            >
              {t.industry.techDocs}
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

export default Industry;
