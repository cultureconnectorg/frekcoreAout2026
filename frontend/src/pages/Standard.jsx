import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, Shield, Music, Lock, FileCheck } from 'lucide-react';
import { useLanguage } from '../lib/LanguageContext';
import { Navigation } from '../components/Navigation';
import { Footer } from '../components/Footer';
import { DOMAINS } from '../lib/domains';

export function Standard() {
  const { t } = useLanguage();
  const docsUrl = DOMAINS.DOCS_BASE;
  
  return (
    <div className="min-h-screen bg-[#030303]">
      <Navigation currentPage="standard" />

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-6">
            {t.standard.section}
          </p>
          <h1 
            className="font-serif text-4xl md:text-5xl lg:text-6xl text-white mb-6 font-light leading-tight"
            dangerouslySetInnerHTML={{ __html: t.standard.title }}
          />
          <p 
            className="text-xl text-zinc-400 max-w-2xl mx-auto"
            dangerouslySetInnerHTML={{ __html: t.standard.description }}
          />
        </div>
      </section>

      {/* Simple Explanation */}
      <section className="py-24 px-6 border-t border-zinc-900">
        <div className="max-w-3xl mx-auto">
          <h2 className="font-serif text-3xl text-white mb-8 font-light text-center">
            {t.standard.simpleTitle}
          </h2>
          
          <div className="space-y-8 text-lg text-zinc-400 leading-relaxed">
            <p dangerouslySetInnerHTML={{ __html: t.standard.p1 }} />
            <p dangerouslySetInnerHTML={{ __html: t.standard.p2 }} />
            <p dangerouslySetInnerHTML={{ __html: t.standard.p3 }} />

            <div className="bg-[#0A0A0A] border border-zinc-800 p-6 my-8">
              <p className="text-zinc-300 font-medium mb-2">{t.standard.keyDifference}</p>
              <p 
                className="text-zinc-500"
                dangerouslySetInnerHTML={{ __html: t.standard.keyDifferenceDesc }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6 bg-[#050505]">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-serif text-3xl text-white mb-12 font-light text-center">
            {t.standard.howItWorks}
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-6">
                <Music className="w-8 h-8 text-zinc-600" />
              </div>
              <h3 className="font-mono text-white mb-3">1. {t.standard.create}</h3>
              <p 
                className="text-zinc-500 text-sm"
                dangerouslySetInnerHTML={{ __html: t.standard.createDesc }}
              />
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-6">
                <Lock className="w-8 h-8 text-zinc-600" />
              </div>
              <h3 className="font-mono text-white mb-3">2. {t.standard.sign}</h3>
              <p 
                className="text-zinc-500 text-sm"
                dangerouslySetInnerHTML={{ __html: t.standard.signDesc }}
              />
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-6">
                <FileCheck className="w-8 h-8 text-zinc-600" />
              </div>
              <h3 className="font-mono text-white mb-3">3. {t.standard.verifyStep}</h3>
              <p 
                className="text-zinc-500 text-sm"
                dangerouslySetInnerHTML={{ __html: t.standard.verifyStepDesc }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* What FREK Is Not */}
      <section className="py-24 px-6 border-t border-zinc-900">
        <div className="max-w-3xl mx-auto">
          <h2 
            className="font-serif text-3xl text-white mb-12 font-light text-center"
            dangerouslySetInnerHTML={{ __html: t.standard.whatIsNot }}
          />
          
          <div className="space-y-6">
            <div className="flex gap-4 items-start">
              <div className="w-8 h-8 bg-[#FF3333]/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-[#FF3333] font-mono text-sm">X</span>
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">{t.standard.notPlatform}</h3>
                <p 
                  className="text-zinc-500"
                  dangerouslySetInnerHTML={{ __html: t.standard.notPlatformDesc }}
                />
              </div>
            </div>
            
            <div className="flex gap-4 items-start">
              <div className="w-8 h-8 bg-[#FF3333]/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-[#FF3333] font-mono text-sm">X</span>
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">{t.standard.notTracking}</h3>
                <p 
                  className="text-zinc-500"
                  dangerouslySetInnerHTML={{ __html: t.standard.notTrackingDesc }}
                />
              </div>
            </div>
            
            <div className="flex gap-4 items-start">
              <div className="w-8 h-8 bg-[#FF3333]/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-[#FF3333] font-mono text-sm">X</span>
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">{t.standard.notRecognition}</h3>
                <p 
                  className="text-zinc-500"
                  dangerouslySetInnerHTML={{ __html: t.standard.notRecognitionDesc }}
                />
              </div>
            </div>
            
            <div className="flex gap-4 items-start">
              <div className="w-8 h-8 bg-[#FF3333]/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-[#FF3333] font-mono text-sm">X</span>
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">{t.standard.notRanking}</h3>
                <p 
                  className="text-zinc-500"
                  dangerouslySetInnerHTML={{ __html: t.standard.notRankingDesc }}
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Who Uses FREK */}
      <section className="py-24 px-6 bg-[#050505]">
        <div className="max-w-3xl mx-auto">
          <h2 className="font-serif text-3xl text-white mb-12 font-light text-center">
            {t.standard.whoUses}
          </h2>
          
          <div className="space-y-6">
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-white mb-2">{t.landing.useCases.djs}</h3>
              <p className="text-zinc-500" dangerouslySetInnerHTML={{ __html: t.landing.useCases.djsDesc }} />
            </div>
            
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-white mb-2">{t.landing.useCases.labels}</h3>
              <p className="text-zinc-500">{t.landing.useCases.labelsDesc}</p>
            </div>
            
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-white mb-2">{t.landing.useCases.festivals}</h3>
              <p className="text-zinc-500" dangerouslySetInnerHTML={{ __html: t.landing.useCases.festivalsDesc }} />
            </div>
            
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-white mb-2">{t.landing.useCases.archives}</h3>
              <p className="text-zinc-500">{t.landing.useCases.archivesDesc}</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-zinc-900">
        <div className="max-w-xl mx-auto text-center">
          <h2 className="font-serif text-3xl text-white mb-6 font-light">
            {t.standard.tryIt}
          </h2>
          <p 
            className="text-zinc-500 mb-8"
            dangerouslySetInnerHTML={{ __html: t.standard.tryItDesc }}
          />
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <NavLink 
              to="/verify"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-mono text-sm uppercase tracking-wide hover:bg-zinc-200 transition-colors"
            >
              <Shield className="w-4 h-4" />
              {t.standard.verifyAudio}
            </NavLink>
            <NavLink 
              to="/manifesto"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border border-zinc-700 text-white font-mono text-sm uppercase tracking-wide hover:border-zinc-500 transition-colors"
            >
              {t.standard.readManifesto}
              <ArrowRight className="w-4 h-4" />
            </NavLink>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

export default Standard;
