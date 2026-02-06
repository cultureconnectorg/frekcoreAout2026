import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, Shield, Code, Building2, Play } from 'lucide-react';

export function PublicLanding() {
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
            <NavLink to="/docs" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Documentation
            </NavLink>
            <NavLink to="/industry" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Industry
            </NavLink>
            <NavLink 
              to="/app" 
              className="font-mono text-sm px-4 py-2 bg-[#00F0FF] text-black hover:bg-[#00F0FF]/90 transition-colors"
            >
              Verify
            </NavLink>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="min-h-screen flex items-center justify-center px-6 pt-16">
        <div className="max-w-4xl mx-auto text-center">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-zinc-600 mb-6">
            Open Protocol
          </p>
          
          <h1 className="font-serif text-5xl md:text-7xl lg:text-8xl font-light text-white mb-8 tracking-tight leading-[0.9]">
            FREK
          </h1>
          
          <p className="font-serif text-2xl md:text-3xl text-zinc-300 mb-4 font-light">
            Musical Proof Standard
          </p>
          
          <p className="font-sans text-lg md:text-xl text-zinc-500 max-w-2xl mx-auto mb-12">
            An open protocol for verifying DJ mixes and musical performances.
            Cryptographic proof without surveillance.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <NavLink 
              to="/app"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-mono text-sm uppercase tracking-wide hover:bg-zinc-200 transition-colors"
              data-testid="hero-verify-btn"
            >
              <Play className="w-4 h-4" />
              Try Live Demo
            </NavLink>
            <NavLink 
              to="/docs"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border border-zinc-700 text-white font-mono text-sm uppercase tracking-wide hover:border-zinc-500 hover:bg-zinc-900/50 transition-colors"
              data-testid="hero-docs-btn"
            >
              <Code className="w-4 h-4" />
              Developer Docs
            </NavLink>
          </div>
        </div>
      </section>

      {/* What is FREK */}
      <section className="py-32 px-6 border-t border-zinc-900">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-4">
            01 — What is FREK
          </p>
          <h2 className="font-serif text-3xl md:text-4xl text-white mb-8 font-light">
            A standard for musical authenticity
          </h2>
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <p className="text-zinc-400 text-lg leading-relaxed">
                FREK is a cryptographic protocol that creates tamper-proof records of musical performances. 
                It generates unique fingerprints from audio content and binds them to creator signatures.
              </p>
            </div>
            <div>
              <p className="text-zinc-400 text-lg leading-relaxed">
                Unlike traditional content identification systems, FREK operates locally on your device. 
                No cloud processing. No central database. No surveillance infrastructure.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Why it exists */}
      <section className="py-32 px-6 bg-[#050505]">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-4">
            02 — Why it exists
          </p>
          <h2 className="font-serif text-3xl md:text-4xl text-white mb-12 font-light">
            Trust through transparency
          </h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-sm uppercase tracking-wide text-white mb-4">Proof</h3>
              <p className="text-zinc-500">
                Cryptographic evidence that a specific performance existed at a specific time, 
                created by a specific artist.
              </p>
            </div>
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-sm uppercase tracking-wide text-white mb-4">Authorship</h3>
              <p className="text-zinc-500">
                Ed25519 digital signatures bind the audio fingerprint to the creator, 
                establishing undeniable attribution.
              </p>
            </div>
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-sm uppercase tracking-wide text-white mb-4">Neutrality</h3>
              <p className="text-zinc-500">
                FREK does not judge music quality. It does not rank artists. 
                It provides technical proof, nothing more.
              </p>
            </div>
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-sm uppercase tracking-wide text-white mb-4">Privacy</h3>
              <p className="text-zinc-500">
                No personal data required. No tracking. No analytics. 
                The artist controls their proof completely.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-32 px-6 border-t border-zinc-900">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-4">
            03 — Use Cases
          </p>
          <h2 className="font-serif text-3xl md:text-4xl text-white mb-12 font-light">
            Built for the music ecosystem
          </h2>
          
          <div className="space-y-6">
            <div className="flex items-start gap-6 p-6 border-l-2 border-zinc-800 hover:border-[#00F0FF] transition-colors">
              <div className="w-16 text-right">
                <span className="font-mono text-xs text-zinc-600">01</span>
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">DJs & Producers</h3>
                <p className="text-zinc-500">Prove the authenticity of live sets and studio mixes. Protect your creative work.</p>
              </div>
            </div>
            
            <div className="flex items-start gap-6 p-6 border-l-2 border-zinc-800 hover:border-[#00F0FF] transition-colors">
              <div className="w-16 text-right">
                <span className="font-mono text-xs text-zinc-600">02</span>
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">Record Labels</h3>
                <p className="text-zinc-500">Verify master recordings and track provenance across distribution chains.</p>
              </div>
            </div>
            
            <div className="flex items-start gap-6 p-6 border-l-2 border-zinc-800 hover:border-[#00F0FF] transition-colors">
              <div className="w-16 text-right">
                <span className="font-mono text-xs text-zinc-600">03</span>
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">DSPs & Platforms</h3>
                <p className="text-zinc-500">Integrate proof verification into streaming services and content management systems.</p>
              </div>
            </div>
            
            <div className="flex items-start gap-6 p-6 border-l-2 border-zinc-800 hover:border-[#00F0FF] transition-colors">
              <div className="w-16 text-right">
                <span className="font-mono text-xs text-zinc-600">04</span>
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">Festivals & Events</h3>
                <p className="text-zinc-500">Document live performances with cryptographic timestamps for archival purposes.</p>
              </div>
            </div>
            
            <div className="flex items-start gap-6 p-6 border-l-2 border-zinc-800 hover:border-[#00F0FF] transition-colors">
              <div className="w-16 text-right">
                <span className="font-mono text-xs text-zinc-600">05</span>
              </div>
              <div>
                <h3 className="font-mono text-white mb-2">Archives & Institutions</h3>
                <p className="text-zinc-500">Preserve musical heritage with verifiable, tamper-proof records.</p>
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
              <h3 className="font-mono text-lg text-white mb-3">Live Demo</h3>
              <p className="text-zinc-500 text-sm mb-6 flex-1">
                Try the FREK verification tool. Upload a .frek.json file and verify its authenticity locally.
              </p>
              <NavLink 
                to="/app"
                className="inline-flex items-center gap-2 font-mono text-sm text-[#00F0FF] hover:underline"
              >
                Launch App <ArrowRight className="w-4 h-4" />
              </NavLink>
            </div>

            {/* Documentation */}
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A] flex flex-col">
              <div className="w-12 h-12 bg-zinc-800 flex items-center justify-center mb-6">
                <Code className="w-6 h-6 text-zinc-400" />
              </div>
              <h3 className="font-mono text-lg text-white mb-3">Developer Documentation</h3>
              <p className="text-zinc-500 text-sm mb-6 flex-1">
                Technical specification, JSON schema, cryptographic protocol details, and integration guides.
              </p>
              <NavLink 
                to="/docs"
                className="inline-flex items-center gap-2 font-mono text-sm text-zinc-400 hover:text-white hover:underline"
              >
                Read Docs <ArrowRight className="w-4 h-4" />
              </NavLink>
            </div>

            {/* Industry */}
            <div className="p-8 border border-zinc-800 bg-[#0A0A0A] flex flex-col">
              <div className="w-12 h-12 bg-zinc-800 flex items-center justify-center mb-6">
                <Building2 className="w-6 h-6 text-zinc-400" />
              </div>
              <h3 className="font-mono text-lg text-white mb-3">Industry Adoption</h3>
              <p className="text-zinc-500 text-sm mb-6 flex-1">
                Learn how FREK can integrate into your organization. Partnership and implementation information.
              </p>
              <NavLink 
                to="/industry"
                className="inline-flex items-center gap-2 font-mono text-sm text-zinc-400 hover:text-white hover:underline"
              >
                Learn More <ArrowRight className="w-4 h-4" />
              </NavLink>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 px-6 border-t border-zinc-900">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-6 h-6 bg-[#00F0FF] flex items-center justify-center">
                  <span className="font-mono font-bold text-black text-xs">F</span>
                </div>
                <span className="font-mono font-bold text-white">FREK</span>
                <span className="font-mono text-xs text-zinc-600">v0.4</span>
              </div>
              <p className="font-mono text-xs text-zinc-600 max-w-xs">
                Open standard for musical proof. 
                No tracking. No cloud. No platform.
              </p>
            </div>
            
            <div className="flex gap-8">
              <div>
                <p className="font-mono text-xs uppercase tracking-wide text-zinc-600 mb-3">Protocol</p>
                <div className="space-y-2">
                  <NavLink to="/docs" className="block font-mono text-sm text-zinc-500 hover:text-white">Documentation</NavLink>
                  <NavLink to="/docs/spec" className="block font-mono text-sm text-zinc-500 hover:text-white">Specification</NavLink>
                  <NavLink to="/docs/changelog" className="block font-mono text-sm text-zinc-500 hover:text-white">Changelog</NavLink>
                </div>
              </div>
              <div>
                <p className="font-mono text-xs uppercase tracking-wide text-zinc-600 mb-3">Resources</p>
                <div className="space-y-2">
                  <NavLink to="/app" className="block font-mono text-sm text-zinc-500 hover:text-white">Verify Tool</NavLink>
                  <NavLink to="/industry" className="block font-mono text-sm text-zinc-500 hover:text-white">Industry</NavLink>
                  <NavLink to="/docs/governance" className="block font-mono text-sm text-zinc-500 hover:text-white">Governance</NavLink>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default PublicLanding;
