import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, Shield } from 'lucide-react';
import { DOMAINS } from '../lib/domains';

export function Manifesto() {
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
            <NavLink to="/industry" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Industry
            </NavLink>
            <NavLink to="/docs" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Docs
            </NavLink>
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
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-6">
            Manifesto
          </p>
          <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl text-white mb-6 font-light leading-tight">
            The FREK Vision
          </h1>
          <p className="text-xl text-zinc-500">
            A declaration of principles for musical authenticity in the digital age.
          </p>
        </div>
      </section>

      {/* Content */}
      <section className="py-16 px-6">
        <div className="max-w-2xl mx-auto">
          <article className="prose prose-invert prose-lg">
            
            {/* Section 1 */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                On the DJ Gesture
              </h2>
              <p className="text-zinc-400 leading-relaxed mb-4">
                The DJ mix is an act of creation. Each selection, each transition, each effect 
                is a decision that shapes a unique sonic journey. This creative act deserves 
                recognition and protection.
              </p>
              <p className="text-zinc-400 leading-relaxed">
                FREK exists to honor this creative gesture — not by judging it, not by ranking it, 
                but by providing irrefutable proof that it happened, exactly as it happened.
              </p>
            </div>

            {/* Section 2 */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                On Artistic Sovereignty
              </h2>
              <p className="text-zinc-400 leading-relaxed mb-4">
                We believe that artists should control their own proofs. No corporation, 
                no platform, no government should have the power to grant or revoke 
                recognition of creative work.
              </p>
              <p className="text-zinc-400 leading-relaxed">
                In the FREK model, your private key is your authority. Your attestation 
                belongs to you. It cannot be deleted, modified, or controlled by anyone else.
              </p>
            </div>

            {/* Section 3 */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                On Proof Without Surveillance
              </h2>
              <p className="text-zinc-400 leading-relaxed mb-4">
                The surveillance economy has taught us that "free" services come at the cost 
                of our privacy. Music recognition platforms track what we listen to, when, 
                and where. Content ID systems monitor every upload.
              </p>
              <p className="text-zinc-400 leading-relaxed">
                FREK rejects this bargain. We believe it is possible to have proof without 
                surveillance. Your music can be authenticated without being monitored. 
                Your identity can be verified without being tracked.
              </p>
            </div>

            {/* Section 4 */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                On Open Standards
              </h2>
              <p className="text-zinc-400 leading-relaxed mb-4">
                FREK is not a product. It is not a platform. It is a standard — like HTTP 
                for the web or MIDI for music hardware. Anyone can implement it. 
                Anyone can verify it.
              </p>
              <p className="text-zinc-400 leading-relaxed">
                We publish our specifications openly. We welcome implementations by others. 
                We resist capture by any single entity. The standard belongs to everyone 
                who uses it.
              </p>
            </div>

            {/* Section 5 */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                Our Commitments
              </h2>
              <div className="bg-[#0A0A0A] border border-zinc-800 p-8 not-prose">
                <ul className="space-y-4">
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">FREK will never judge the quality of music</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">FREK will never rank or score artists</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">FREK will never require personal data</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">FREK will never become a platform</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">FREK will always work offline</span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span className="w-2 h-2 bg-[#00F0FF] mt-2 flex-shrink-0"></span>
                    <span className="text-zinc-300">FREK will always remain open</span>
                  </li>
                </ul>
              </div>
            </div>

            {/* Closing */}
            <div className="mb-16">
              <h2 className="font-serif text-2xl text-white mb-6 font-light">
                The Future
              </h2>
              <p className="text-zinc-400 leading-relaxed mb-4">
                We envision a future where every DJ set, every live performance, 
                every musical creation can be authenticated without compromise. 
                Where proof is abundant but surveillance is absent.
              </p>
              <p className="text-zinc-400 leading-relaxed">
                This is not just a technical project. It is a statement about how technology 
                should serve artists and creators. It is a choice to build tools that 
                empower rather than exploit.
              </p>
              <p className="text-zinc-400 leading-relaxed italic mt-8">
                FREK recognizes a technical fact, in a precise context. 
                The human remains the interpreter. The legal remains the arbiter.
              </p>
            </div>
          </article>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-zinc-900">
        <div className="max-w-xl mx-auto text-center">
          <h2 className="font-serif text-2xl text-white mb-6 font-light">
            Join the Movement
          </h2>
          <p className="text-zinc-500 mb-8">
            Try FREK today. Verify your first audio file. 
            Be part of a new standard for musical authenticity.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <NavLink 
              to="/verify"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-mono text-sm uppercase tracking-wide hover:bg-zinc-200 transition-colors"
            >
              <Shield className="w-4 h-4" />
              Verify Now
            </NavLink>
            <NavLink 
              to="/docs"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border border-zinc-700 text-white font-mono text-sm uppercase tracking-wide hover:border-zinc-500 transition-colors"
            >
              Developer Docs
              <ArrowRight className="w-4 h-4" />
            </NavLink>
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
            <span className="font-mono text-sm text-zinc-500">FREK — Open Musical Proof Standard</span>
          </div>
          <div className="flex gap-6">
            <NavLink to="/" className="font-mono text-sm text-zinc-500 hover:text-white">Home</NavLink>
            <NavLink to="/standard" className="font-mono text-sm text-zinc-500 hover:text-white">Standard</NavLink>
            <NavLink to="/docs" className="font-mono text-sm text-zinc-500 hover:text-white">Docs</NavLink>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Manifesto;
