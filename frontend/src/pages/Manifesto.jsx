import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, Shield } from 'lucide-react';
import { useLanguage } from '../lib/LanguageContext';
import { Navigation } from '../components/Navigation';
import { Footer } from '../components/Footer';
import { DOMAINS } from '../lib/domains';

export function Manifesto() {
  const { t } = useLanguage();
  const docsUrl = DOMAINS.DOCS_BASE;
  
  return (
    <div className="min-h-screen bg-[#030303]">
      <Navigation currentPage="manifesto" />

      {/* Hero */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-6">
            {t.manifesto.section}
          </p>
          <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl text-white mb-6 font-light leading-tight">
            {t.manifesto.title}
          </h1>
          <p 
            className="text-xl text-zinc-500"
            dangerouslySetInnerHTML={{ __html: t.manifesto.description }}
          />
        </div>
      </section>

      {/* Content */}
      <section className="py-16 px-6">
        <div className="max-w-2xl mx-auto">
          <article className="prose prose-invert prose-lg">
            
            {/* Section 1 */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                {t.manifesto.djGesture}
              </h2>
              <p 
                className="text-zinc-400 leading-relaxed mb-4"
                dangerouslySetInnerHTML={{ __html: t.manifesto.djGestureP1 }}
              />
              <p 
                className="text-zinc-400 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: t.manifesto.djGestureP2 }}
              />
            </div>

            {/* Section 2 */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                {t.manifesto.sovereignty}
              </h2>
              <p 
                className="text-zinc-400 leading-relaxed mb-4"
                dangerouslySetInnerHTML={{ __html: t.manifesto.sovereigntyP1 }}
              />
              <p 
                className="text-zinc-400 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: t.manifesto.sovereigntyP2 }}
              />
            </div>

            {/* Section 3 */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                {t.manifesto.proofWithout}
              </h2>
              <p 
                className="text-zinc-400 leading-relaxed mb-4"
                dangerouslySetInnerHTML={{ __html: t.manifesto.proofWithoutP1 }}
              />
              <p 
                className="text-zinc-400 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: t.manifesto.proofWithoutP2 }}
              />
            </div>

            {/* Section 4 */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                {t.manifesto.openStandards}
              </h2>
              <p 
                className="text-zinc-400 leading-relaxed mb-4"
                dangerouslySetInnerHTML={{ __html: t.manifesto.openStandardsP1 }}
              />
              <p 
                className="text-zinc-400 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: t.manifesto.openStandardsP2 }}
              />
            </div>

            {/* Section 5 */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                {t.manifesto.commitments}
              </h2>
              <div className="bg-[#0A0A0A] border border-zinc-800 p-8 not-prose">
                <ul className="space-y-4">
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">{t.manifesto.commitment1}</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">{t.manifesto.commitment2}</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">{t.manifesto.commitment3}</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">{t.manifesto.commitment4}</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">{t.manifesto.commitment5}</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">{t.manifesto.commitment6}</span>
                  </li>
                </ul>
              </div>
            </div>

            {/* Closing */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                {t.manifesto.future}
              </h2>
              <p 
                className="text-zinc-400 leading-relaxed mb-4"
                dangerouslySetInnerHTML={{ __html: t.manifesto.futureP1 }}
              />
              <p 
                className="text-zinc-400 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: t.manifesto.futureP2 }}
              />
              <p 
                className="text-zinc-400 leading-relaxed italic mt-8"
                dangerouslySetInnerHTML={{ __html: t.manifesto.closing }}
              />
            </div>
          </article>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-zinc-900">
        <div className="max-w-xl mx-auto text-center">
          <h2 className="font-serif text-2xl text-white mb-6 font-light">
            {t.manifesto.joinMovement}
          </h2>
          <p 
            className="text-zinc-500 mb-8"
            dangerouslySetInnerHTML={{ __html: t.manifesto.joinMovementDesc }}
          />
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <NavLink 
              to="/verify"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-mono text-sm uppercase tracking-wide hover:bg-zinc-200 transition-colors"
            >
              <Shield className="w-4 h-4" />
              {t.manifesto.verifyNow}
            </NavLink>
            <a 
              href={docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border border-zinc-700 text-white font-mono text-sm uppercase tracking-wide hover:border-zinc-500 transition-colors"
            >
              {t.manifesto.devPortal}
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

export default Manifesto;
