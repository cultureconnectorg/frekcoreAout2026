import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, Shield, Check, Building2, Users, Globe, Lock, Scale, Mail } from 'lucide-react';
import { DOMAINS } from '../lib/domains';

export function Industry() {
  const docsUrl = DOMAINS.DOCS_BASE;
  return (
    <div className="min-h-screen bg-[#030303]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#030303]/90 backdrop-blur-sm border-b border-zinc-900">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#00F0FF] flex items-center justify-center">
              <span className="font-mono font-bold text-black text-sm">F</span>
            </div>
            <span className="font-mono font-bold text-lg tracking-tight text-white">FREK</span>
          </NavLink>
          
          <div className="hidden md:flex items-center gap-8">
            <NavLink to="/standard" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Standard
            </NavLink>
            <NavLink to="/manifesto" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Manifesto
            </NavLink>
            <span className="font-mono text-sm text-white">Industry</span>
            <a 
              href={docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-sm text-zinc-400 hover:text-white transition-colors"
            >
              Developers
            </a>
            <NavLink 
              to="/verify" 
              className="font-mono text-sm px-4 py-2 bg-[#00F0FF] text-black hover:bg-[#00F0FF]/90 transition-colors"
            >
              Verify
            </NavLink>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6 border-b border-zinc-900">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-6">
            Industry Solutions
          </p>
          <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl text-white mb-6 font-light leading-tight">
            FREK for the<br />Music Industry
          </h1>
          <p className="text-xl text-zinc-400 max-w-2xl">
            A neutral, open infrastructure layer for verifying musical authenticity 
            across the entire music ecosystem.
          </p>
        </div>
      </section>

      {/* Infrastructure Layer */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-zinc-600 mb-4">
            Infrastructure
          </p>
          <h2 className="font-serif text-3xl text-white mb-8 font-light">
            A foundational layer, not a platform
          </h2>
          
          <div className="grid md:grid-cols-2 gap-12 mb-12">
            <div>
              <p className="text-zinc-400 leading-relaxed mb-6">
                FREK is designed as infrastructure — like TCP/IP for the internet or MIDI for music hardware. 
                It provides a common protocol that any system can implement independently.
              </p>
              <p className="text-zinc-400 leading-relaxed">
                Unlike proprietary platforms, FREK does not create lock-in. Organizations maintain full control 
                over their implementations and data.
              </p>
            </div>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
              <p className="font-mono text-xs uppercase tracking-wide text-zinc-600 mb-4">Architecture</p>
              <div className="space-y-3 font-mono text-sm">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#00F0FF]"></div>
                  <span className="text-zinc-400">Local-first processing</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#00F0FF]"></div>
                  <span className="text-zinc-400">Ed25519 cryptographic signatures</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#00F0FF]"></div>
                  <span className="text-zinc-400">SHA-256 audio fingerprinting</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#00F0FF]"></div>
                  <span className="text-zinc-400">JSON-based portable format</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#00F0FF]"></div>
                  <span className="text-zinc-400">No central authority required</span>
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
            Neutrality
          </p>
          <h2 className="font-serif text-3xl text-white mb-8 font-light">
            Positioned as a neutral standard
          </h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <Lock className="w-8 h-8 text-zinc-600 mb-4" />
              <h3 className="font-mono text-white mb-2">No Vendor Lock-in</h3>
              <p className="text-zinc-500 text-sm">
                Open specification. Any organization can implement FREK independently without licensing fees.
              </p>
            </div>
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <Scale className="w-8 h-8 text-zinc-600 mb-4" />
              <h3 className="font-mono text-white mb-2">Non-Commercial Governance</h3>
              <p className="text-zinc-500 text-sm">
                The standard is maintained by an independent body with explicit anti-capture mechanisms.
              </p>
            </div>
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <Globe className="w-8 h-8 text-zinc-600 mb-4" />
              <h3 className="font-mono text-white mb-2">Industry-Agnostic</h3>
              <p className="text-zinc-500 text-sm">
                Works equally for independent artists, major labels, streaming platforms, and archival institutions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Adoption Benefits */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-zinc-600 mb-4">
            Benefits
          </p>
          <h2 className="font-serif text-3xl text-white mb-12 font-light">
            Why adopt FREK
          </h2>
          
          <div className="space-y-8">
            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00F0FF]/10 flex items-center justify-center flex-shrink-0">
                <Check className="w-6 h-6 text-[#00F0FF]" />
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">Reduced Dispute Resolution Costs</h3>
                <p className="text-zinc-500">
                  Cryptographic proof of authenticity can resolve ownership and timing disputes 
                  without expensive litigation or manual verification processes.
                </p>
              </div>
            </div>
            
            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00F0FF]/10 flex items-center justify-center flex-shrink-0">
                <Check className="w-6 h-6 text-[#00F0FF]" />
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">Enhanced Trust Infrastructure</h3>
                <p className="text-zinc-500">
                  Provide artists, labels, and platforms with verifiable proof of musical content 
                  provenance throughout the distribution chain.
                </p>
              </div>
            </div>
            
            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00F0FF]/10 flex items-center justify-center flex-shrink-0">
                <Check className="w-6 h-6 text-[#00F0FF]" />
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">Privacy-Compliant by Design</h3>
                <p className="text-zinc-500">
                  No personal data collection required. FREK attestations contain only technical 
                  proof data, simplifying GDPR and privacy regulation compliance.
                </p>
              </div>
            </div>
            
            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00F0FF]/10 flex items-center justify-center flex-shrink-0">
                <Check className="w-6 h-6 text-[#00F0FF]" />
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">Future-Proof Interoperability</h3>
                <p className="text-zinc-500">
                  Standard JSON format ensures compatibility across systems. Versioned specification 
                  guarantees backward compatibility as the protocol evolves.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Integration Scenarios */}
      <section className="py-24 px-6 bg-[#050505]">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-zinc-600 mb-4">
            Integration
          </p>
          <h2 className="font-serif text-3xl text-white mb-12 font-light">
            Implementation scenarios
          </h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-lg text-white mb-4">Streaming Platforms</h3>
              <ul className="space-y-3 text-zinc-500 text-sm">
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Embed FREK verification in upload workflows
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Display proof badges on verified content
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  API integration for automated verification
                </li>
              </ul>
            </div>
            
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-lg text-white mb-4">Record Labels</h3>
              <ul className="space-y-3 text-zinc-500 text-sm">
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Master recording certification
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Distribution chain verification
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Artist contract compliance proof
                </li>
              </ul>
            </div>
            
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-lg text-white mb-4">DAW Integration</h3>
              <ul className="space-y-3 text-zinc-500 text-sm">
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Plugin for Ableton, Logic, Traktor
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Real-time attestation during mixing
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Export FREK files alongside audio
                </li>
              </ul>
            </div>
            
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-lg text-white mb-4">Archives & Libraries</h3>
              <ul className="space-y-3 text-zinc-500 text-sm">
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Long-term preservation metadata
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Provenance chain documentation
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">→</span>
                  Interoperability with existing standards
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Governance */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-zinc-600 mb-4">
            Governance
          </p>
          <h2 className="font-serif text-3xl text-white mb-8 font-light">
            Anti-capture governance model
          </h2>
          
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <p className="text-zinc-400 leading-relaxed mb-6">
                FREK is maintained by an independent foundation with explicit mechanisms to prevent 
                commercial capture or centralization of control.
              </p>
              <ul className="space-y-3 text-zinc-500">
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">•</span>
                  Copyleft licensing prevents proprietary forks
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">•</span>
                  Rotating maintainers with conflict-of-interest rules
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">•</span>
                  Community veto power on specification changes
                </li>
                <li className="flex gap-2">
                  <span className="text-[#00F0FF]">•</span>
                  Public proposal process for all modifications
                </li>
              </ul>
            </div>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
              <p className="font-mono text-xs uppercase tracking-wide text-zinc-600 mb-4">Governance Principles</p>
              <div className="space-y-4">
                <div>
                  <p className="font-mono text-sm text-white">Vision Layer</p>
                  <p className="text-zinc-600 text-sm">Defines what FREK is and is not</p>
                </div>
                <div className="border-t border-zinc-800 pt-4">
                  <p className="font-mono text-sm text-white">Specification Layer</p>
                  <p className="text-zinc-600 text-sm">Technical format and rules</p>
                </div>
                <div className="border-t border-zinc-800 pt-4">
                  <p className="font-mono text-sm text-white">Implementation Layer</p>
                  <p className="text-zinc-600 text-sm">Independent, unrestricted</p>
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
            Partnership
          </p>
          <h2 className="font-serif text-3xl text-white mb-6 font-light">
            Interested in adopting FREK?
          </h2>
          <p className="text-zinc-400 mb-8 max-w-xl mx-auto">
            We work with organizations across the music industry to implement 
            FREK verification infrastructure.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="mailto:contact@frek.org"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-mono text-sm uppercase tracking-wide hover:bg-zinc-200 transition-colors"
            >
              <Mail className="w-4 h-4" />
              Contact for Partnership
            </a>
            <a 
              href={docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border border-zinc-700 text-white font-mono text-sm uppercase tracking-wide hover:border-zinc-500 transition-colors"
            >
              Technical Documentation
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-zinc-900">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-[#00F0FF] flex items-center justify-center">
              <span className="font-mono font-bold text-black text-xs">F</span>
            </div>
            <span className="font-mono text-sm text-zinc-500">FREK v0.4 — Open Musical Proof Standard</span>
          </div>
          <div className="flex gap-6">
            <NavLink to="/" className="font-mono text-sm text-zinc-500 hover:text-white">Home</NavLink>
            <NavLink to="/standard" className="font-mono text-sm text-zinc-500 hover:text-white">Standard</NavLink>
            <a href={docsUrl} target="_blank" rel="noopener noreferrer" className="font-mono text-sm text-zinc-500 hover:text-white">Developers</a>
            <NavLink to="/verify" className="font-mono text-sm text-zinc-500 hover:text-white">Verify</NavLink>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Industry;
