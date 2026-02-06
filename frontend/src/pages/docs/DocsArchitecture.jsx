import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, ArrowLeft } from 'lucide-react';

export function DocsArchitecture() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Developer Documentation
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          FREK Architecture v0.4
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          Local audio proof pipeline. Proof &gt; Service. Local-First. Anti-Surveillance.
        </p>
      </div>

      {/* Pipeline Overview */}
      <div className="mb-12">
        <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-6">
          Proof Pipeline
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {/* Stage 1 */}
          <div className="bg-[#0A0A0A] border border-red-900/50 p-4">
            <p className="font-mono text-xs uppercase tracking-widest text-red-500 mb-3">
              1. Source & Capture
            </p>
            <div className="space-y-2 text-sm text-zinc-400">
              <p className="font-mono text-zinc-300">Audio Reality</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• DJ Mix / Live</li>
                <li>• Performance</li>
                <li>• Rehearsal</li>
                <li>• Contested broadcast</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">Voluntary Capture</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Recorder / DAW</li>
                <li>• Raw WAV</li>
                <li>• No cloud</li>
              </ul>
            </div>
          </div>

          {/* Stage 2 */}
          <div className="bg-[#0A0A0A] border border-blue-900/50 p-4">
            <p className="font-mono text-xs uppercase tracking-widest text-blue-500 mb-3">
              2. Sovereign Node
            </p>
            <div className="space-y-2 text-sm text-zinc-400">
              <p className="font-mono text-zinc-300">Local Machine</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Offline capable</li>
                <li>• Full control</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">Normalization</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Mono - 44.1 kHz</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">Segmentation</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• 2-5 sec segments</li>
                <li>• Timestamped</li>
              </ul>
            </div>
          </div>

          {/* Stage 3 */}
          <div className="bg-[#0A0A0A] border border-green-900/50 p-4">
            <p className="font-mono text-xs uppercase tracking-widest text-green-500 mb-3">
              3. Analysis & Proof
            </p>
            <div className="space-y-2 text-sm text-zinc-400">
              <p className="font-mono text-zinc-300">Spectral Analysis</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• FFT / Spectrogram</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">FREK Fingerprint</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• SHA-256 Hash</li>
                <li>• Non-reversible</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">FREK Attestation</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Ed25519 Signature</li>
                <li>• Technical proof</li>
              </ul>
            </div>
          </div>

          {/* Stage 4 */}
          <div className="bg-[#0A0A0A] border border-yellow-900/50 p-4">
            <p className="font-mono text-xs uppercase tracking-widest text-yellow-500 mb-3">
              4. Assisted Matching
            </p>
            <div className="space-y-2 text-sm text-zinc-400">
              <p className="font-mono text-zinc-300">Local Matching</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Local comparison</li>
                <li>• Controlled threshold</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">Match Claim</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Segment + Score</li>
                <li>• Human interpretation</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="hidden md:flex justify-center gap-8 text-zinc-700 font-mono text-xs mb-8">
          <span>CAPTURE → NORMALIZATION → FINGERPRINT → VERIFICATION</span>
        </div>
      </div>

      {/* Layers */}
      <div className="space-y-8 mb-12">
        <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2">
          Standard Layers
        </h2>

        <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <h3 className="font-mono text-sm uppercase tracking-widest text-[#00F0FF] mb-3">
            Audio Fingerprint Layer
          </h3>
          <div className="text-zinc-400 space-y-2 text-sm">
            <p>Irreversible transformation of audio into unique fingerprint.</p>
            <ul className="list-none space-y-1 ml-4">
              <li><span className="text-zinc-600 font-mono">Input:</span> Normalized audio stream (44.1kHz, mono)</li>
              <li><span className="text-zinc-600 font-mono">Process:</span> FFT spectral analysis by segments</li>
              <li><span className="text-zinc-600 font-mono">Output:</span> Global SHA-256 hash + per-segment hashes</li>
            </ul>
          </div>
        </div>

        <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <h3 className="font-mono text-sm uppercase tracking-widest text-[#00F0FF] mb-3">
            Cryptographic Signature Layer
          </h3>
          <div className="text-zinc-400 space-y-2 text-sm">
            <p>Creator authentication via Ed25519 signature.</p>
            <ul className="list-none space-y-1 ml-4">
              <li><span className="text-zinc-600 font-mono">Algorithm:</span> Ed25519 (Curve25519)</li>
              <li><span className="text-zinc-600 font-mono">Signed message:</span> Hash(fingerprint + canonical metadata)</li>
              <li><span className="text-zinc-600 font-mono">Key:</span> Public/private pair controlled by artist</li>
            </ul>
          </div>
        </div>

        <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <h3 className="font-mono text-sm uppercase tracking-widest text-[#00F0FF] mb-3">
            Attestation Layer
          </h3>
          <div className="text-zinc-400 space-y-2 text-sm">
            <p>Formal declaration binding fingerprint to context.</p>
            <ul className="list-none space-y-1 ml-4">
              <li><span className="text-zinc-600 font-mono">Content:</span> Fingerprint + Signature + Metadata</li>
              <li><span className="text-zinc-600 font-mono">Format:</span> .frek.json (structured JSON)</li>
              <li><span className="text-zinc-600 font-mono">Portability:</span> Self-contained file, offline verifiable</li>
            </ul>
          </div>
        </div>

        <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <h3 className="font-mono text-sm uppercase tracking-widest text-[#00F0FF] mb-3">
            Metadata Layer
          </h3>
          <div className="text-zinc-400 space-y-2 text-sm">
            <p>Minimal technical context, no required personal data.</p>
            <ul className="list-none space-y-1 ml-4">
              <li><span className="text-zinc-600 font-mono">Required:</span> timestamp, duration, source_type</li>
              <li><span className="text-zinc-600 font-mono">Optional:</span> Additional non-PII fields</li>
              <li><span className="text-zinc-600 font-mono">Forbidden:</span> Real name, email, location, IP</li>
            </ul>
          </div>
        </div>

        <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <h3 className="font-mono text-sm uppercase tracking-widest text-[#00F0FF] mb-3">
            Export Layer
          </h3>
          <div className="text-zinc-400 space-y-2 text-sm">
            <p>Distribution and archival of attestations.</p>
            <ul className="list-none space-y-1 ml-4">
              <li><span className="text-zinc-600 font-mono">Primary format:</span> .frek.json</li>
              <li><span className="text-zinc-600 font-mono">Storage:</span> Local, optional cloud, optional blockchain</li>
              <li><span className="text-zinc-600 font-mono">Verification:</span> Any compatible verifier can validate</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Responsibilities */}
      <div className="mb-12">
        <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-6">
          Separation of Responsibilities
        </h2>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-center">
          <div className="bg-[#0A0A0A] border border-zinc-800 p-3">
            <p className="font-mono text-[10px] uppercase tracking-widest text-blue-500">Capture</p>
            <p className="text-xs text-zinc-500 mt-1">Operator</p>
          </div>
          <div className="bg-[#0A0A0A] border border-zinc-800 p-3">
            <p className="font-mono text-[10px] uppercase tracking-widest text-green-500">Analysis</p>
            <p className="text-xs text-zinc-500 mt-1">Operator</p>
          </div>
          <div className="bg-[#0A0A0A] border border-zinc-800 p-3">
            <p className="font-mono text-[10px] uppercase tracking-widest text-yellow-500">Matching</p>
            <p className="text-xs text-zinc-500 mt-1">Operator</p>
          </div>
          <div className="bg-[#0A0A0A] border border-zinc-800 p-3">
            <p className="font-mono text-[10px] uppercase tracking-widest text-orange-500">Interpretation</p>
            <p className="text-xs text-zinc-500 mt-1">Human</p>
          </div>
          <div className="bg-[#0A0A0A] border border-zinc-800 p-3">
            <p className="font-mono text-[10px] uppercase tracking-widest text-red-500">Decision</p>
            <p className="text-xs text-zinc-500 mt-1">Legal / Human</p>
          </div>
        </div>

        <p className="font-mono text-xs text-zinc-600 mt-4 text-center">
          FREK = Technical Proof → Human = Interpretation → Legal = Decision
        </p>
      </div>

      {/* Navigation */}
      <div className="border-t border-zinc-800 pt-8 flex justify-between items-center">
        <NavLink 
          to="/docs" 
          className="flex items-center gap-2 text-zinc-500 font-mono text-sm hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" />
          Manifesto
        </NavLink>
        <NavLink 
          to="/docs/spec" 
          className="flex items-center gap-2 text-[#00F0FF] font-mono text-sm hover:underline"
        >
          .frek.json Specification
          <ArrowRight className="w-4 h-4" />
        </NavLink>
      </div>
    </div>
  );
}

export default DocsArchitecture;
