import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

export function DocsManifesto() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Developer Documentation
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          FREK Manifesto
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          Founding document of the FREK standard. Version 0.4.
        </p>
      </div>

      {/* Content */}
      <div className="space-y-12">
        
        {/* Section 1 */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            1. Recognition of the DJ Gesture
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              The DJ mix is an act of technical creation. Selection, sequence, transitions, 
              effects: each decision constitutes a unique artistic signature.
            </p>
            <p>
              FREK exists to prove that a mix happened, as it happened, 
              when it happened. Nothing more.
            </p>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <p className="font-mono text-sm text-zinc-500">
                FREK does not recognize the music.<br/>
                FREK recognizes a technical fact, in a precise context.
              </p>
            </div>
          </div>
        </section>

        {/* Section 2 */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            2. Artistic Sovereignty
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              The artist controls their proofs. No central authority can:
            </p>
            <ul className="list-none space-y-2 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">—</span>
                Revoke a valid attestation
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">—</span>
                Modify a published fingerprint
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">—</span>
                Impose recognition or scoring
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">—</span>
                Collect personal metadata
              </li>
            </ul>
            <p>
              The artist's private key is the sole authority.
            </p>
          </div>
        </section>

        {/* Section 3 */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            3. Proof Without Surveillance
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              FREK does not need to know who you are to prove what you created.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-[#00FF94] mb-2">
                  What FREK does
                </p>
                <ul className="text-sm space-y-1">
                  <li>• Local audio fingerprinting</li>
                  <li>• Cryptographic signature</li>
                  <li>• Technical timestamping</li>
                  <li>• Offline verification</li>
                </ul>
              </div>
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-[#FF3333] mb-2">
                  What FREK does NOT do
                </p>
                <ul className="text-sm space-y-1">
                  <li>• Listen tracking</li>
                  <li>• Cloud music recognition</li>
                  <li>• Personal data collection</li>
                  <li>• Scoring or ranking</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Section 4 */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            4. Open but Protected Standard
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              The <code className="bg-zinc-900 px-1 text-[#00F0FF]">.frek.json</code> format is public. 
              Anyone can:
            </p>
            <ul className="list-none space-y-2 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">→</span>
                Implement a FREK generator
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">→</span>
                Create a FREK verifier
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">→</span>
                Integrate FREK into a DAW
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">→</span>
                Audit verification code
              </li>
            </ul>
            <p>
              The standard is protected against commercial capture by its decentralized governance.
            </p>
          </div>
        </section>

        {/* Section 5 */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            5. Non-Negotiable Principles
          </h2>
          <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
            <ul className="font-mono text-sm space-y-3">
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-[#00F0FF]"></span>
                FREK does not judge music
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-[#00F0FF]"></span>
                FREK does not rank artists
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-[#00F0FF]"></span>
                FREK does not collect personal data
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-[#00F0FF]"></span>
                FREK never becomes a platform
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-[#00F0FF]"></span>
                FREK works offline by default
              </li>
            </ul>
          </div>
        </section>

        {/* Navigation */}
        <div className="border-t border-zinc-800 pt-8 flex justify-between items-center">
          <div></div>
          <NavLink 
            to="/docs/architecture" 
            className="flex items-center gap-2 text-[#00F0FF] font-mono text-sm hover:underline"
          >
            Technical Architecture
            <ArrowRight className="w-4 h-4" />
          </NavLink>
        </div>
      </div>
    </div>
  );
}

export default DocsManifesto;
