import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowLeft, Shield } from 'lucide-react';

export function DocsChangelog() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Developer Documentation
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          Changelog
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          Version history of the FREK standard.
        </p>
      </div>

      {/* Content */}
      <div className="space-y-8">
        
        {/* v0.4 */}
        <section className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="font-mono text-xl font-semibold text-[#00F0FF]">
                v0.4
              </h2>
              <p className="font-mono text-xs text-zinc-600 mt-1">
                2024-04-20 — Current version
              </p>
            </div>
            <span className="font-mono text-[10px] uppercase tracking-widest px-2 py-1 bg-[#00F0FF]/10 text-[#00F0FF] border border-[#00F0FF]/30">
              Current
            </span>
          </div>
          
          <div className="space-y-4 text-sm">
            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-[#00FF94] mb-2">
                Added
              </p>
              <ul className="text-zinc-400 space-y-1 ml-4">
                <li>• Complete .frek.json format specification</li>
                <li>• JSON schema with Zod validation</li>
                <li>• Temporal segments support (optional)</li>
                <li>• Mandatory Ed25519 signature</li>
                <li>• Local-first web verification module</li>
                <li>• Manifesto documentation</li>
                <li>• Pipeline architecture documented</li>
                <li>• Anti-capture governance model</li>
              </ul>
            </div>

            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-[#FFB800] mb-2">
                Changed
              </p>
              <ul className="text-zinc-400 space-y-1 ml-4">
                <li>• Standardized hash format: sha256:&lt;hex&gt;</li>
                <li>• Standardized signature format: ed25519:&lt;base64&gt;</li>
                <li>• Defined mandatory minimal metadata</li>
              </ul>
            </div>

            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
                Technical Notes
              </p>
              <ul className="text-zinc-500 space-y-1 ml-4">
                <li>• Fingerprint algorithm: SHA-256 on normalized audio</li>
                <li>• Normalization: 44.1kHz, mono, PCM</li>
                <li>• Cryptography: Ed25519 (Curve25519)</li>
              </ul>
            </div>
          </div>
        </section>

        {/* v0.3 */}
        <section className="bg-[#0A0A0A] border border-zinc-800 p-6 opacity-75">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="font-mono text-xl font-semibold text-zinc-400">
                v0.3
              </h2>
              <p className="font-mono text-xs text-zinc-600 mt-1">
                2024-02-15
              </p>
            </div>
            <span className="font-mono text-[10px] uppercase tracking-widest px-2 py-1 bg-zinc-900 text-zinc-600 border border-zinc-800">
              Legacy
            </span>
          </div>
          
          <div className="space-y-4 text-sm">
            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
                Content
              </p>
              <ul className="text-zinc-500 space-y-1 ml-4">
                <li>• Initial JSON format prototype</li>
                <li>• ECDSA signature experimentation (abandoned)</li>
                <li>• First manifesto draft</li>
              </ul>
            </div>
          </div>
        </section>

        {/* v0.2 */}
        <section className="bg-[#0A0A0A] border border-zinc-800 p-6 opacity-50">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="font-mono text-xl font-semibold text-zinc-500">
                v0.2
              </h2>
              <p className="font-mono text-xs text-zinc-700 mt-1">
                2024-01-10
              </p>
            </div>
            <span className="font-mono text-[10px] uppercase tracking-widest px-2 py-1 bg-zinc-900 text-zinc-700 border border-zinc-800">
              Deprecated
            </span>
          </div>
          
          <div className="text-sm">
            <ul className="text-zinc-600 space-y-1 ml-4">
              <li>• Fingerprint algorithm research</li>
              <li>• FFT vs perceptual hashing comparative studies</li>
            </ul>
          </div>
        </section>

        {/* v0.1 */}
        <section className="bg-[#0A0A0A] border border-zinc-800 p-6 opacity-50">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="font-mono text-xl font-semibold text-zinc-500">
                v0.1
              </h2>
              <p className="font-mono text-xs text-zinc-700 mt-1">
                2023-12-01
              </p>
            </div>
            <span className="font-mono text-[10px] uppercase tracking-widest px-2 py-1 bg-zinc-900 text-zinc-700 border border-zinc-800">
              Deprecated
            </span>
          </div>
          
          <div className="text-sm">
            <ul className="text-zinc-600 space-y-1 ml-4">
              <li>• Initial FREK concept</li>
              <li>• Founding principles definition</li>
            </ul>
          </div>
        </section>

        {/* Roadmap */}
        <section className="border-t border-zinc-800 pt-8">
          <h2 className="font-mono text-xl font-semibold text-white mb-4">
            Roadmap
          </h2>
          
          <div className="bg-[#0A0A0A] border border-dashed border-zinc-700 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-mono text-lg text-zinc-400">
                  v0.5
                </h3>
                <p className="font-mono text-xs text-zinc-600 mt-1">
                  Planned — Q3 2024
                </p>
              </div>
              <span className="font-mono text-[10px] uppercase tracking-widest px-2 py-1 bg-zinc-900 text-zinc-500 border border-zinc-800">
                Planned
              </span>
            </div>
            
            <div className="text-sm">
              <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
                Proposed Goals
              </p>
              <ul className="text-zinc-500 space-y-1 ml-4">
                <li>• Advanced perceptual fingerprint support</li>
                <li>• Optional metadata extensions</li>
                <li>• Blockchain interoperability specification</li>
                <li>• Multi-language reference SDK</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Navigation */}
        <div className="border-t border-zinc-800 pt-8 flex justify-between items-center">
          <NavLink 
            to="/docs/governance" 
            className="flex items-center gap-2 text-zinc-500 font-mono text-sm hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            Governance
          </NavLink>
          <NavLink 
            to="/app" 
            className="flex items-center gap-2 text-[#00F0FF] font-mono text-sm hover:underline"
          >
            <Shield className="w-4 h-4" />
            Try Verification Tool
          </NavLink>
        </div>
      </div>
    </div>
  );
}

export default DocsChangelog;
