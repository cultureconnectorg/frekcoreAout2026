import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, ArrowLeft, Copy, Check } from 'lucide-react';

export function DocsSpec() {
  const [copied, setCopied] = React.useState(false);

  const exampleJson = `{
  "frek_version": "0.4",
  "fingerprint": "sha256:<hex64>",
  "segments": [
    {"t0": 0, "t1": 5, "h": "sha256:<hex64>"},
    {"t0": 5, "t1": 10, "h": "sha256:<hex64>"}
  ],
  "metadata": {
    "timestamp": "2024-04-20T15:30:00Z",
    "duration": 3600,
    "source_type": "live|studio|rehearsal|dispute"
  },
  "signature": "ed25519:<base64>",
  "public_key": "<base64>"
}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(exampleJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Developer Documentation
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          .frek.json Specification
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          FREK file format v0.4. Structure, validation rules, and versioning.
        </p>
      </div>

      {/* Content */}
      <div className="space-y-12">
        
        {/* Format */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            File Structure
          </h2>
          
          <div className="relative">
            <button
              onClick={handleCopy}
              className="absolute top-3 right-3 p-2 text-zinc-500 hover:text-white transition-colors"
              data-testid="copy-example-btn"
            >
              {copied ? <Check className="w-4 h-4 text-[#00FF94]" /> : <Copy className="w-4 h-4" />}
            </button>
            <pre className="bg-[#0A0A0A] border border-zinc-800 p-6 overflow-x-auto font-mono text-sm text-zinc-300">
              {exampleJson}
            </pre>
          </div>
        </section>

        {/* Fields */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Required Fields
          </h2>
          
          <div className="space-y-4">
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <div className="flex items-start gap-4">
                <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">frek_version</code>
                <div className="text-zinc-400 text-sm">
                  <p>FREK standard version used.</p>
                  <p className="text-zinc-600 mt-1">Format: <code className="text-zinc-500">&quot;0.4&quot;</code> (string)</p>
                </div>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <div className="flex items-start gap-4">
                <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">fingerprint</code>
                <div className="text-zinc-400 text-sm">
                  <p>Global SHA-256 fingerprint of normalized audio.</p>
                  <p className="text-zinc-600 mt-1">Format: <code className="text-zinc-500">&quot;sha256:&lt;64 hex chars&gt;&quot;</code></p>
                </div>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <div className="flex items-start gap-4">
                <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">metadata</code>
                <div className="text-zinc-400 text-sm">
                  <p>Technical context of the mix.</p>
                  <ul className="text-zinc-600 mt-1 space-y-1 ml-4">
                    <li><code className="text-zinc-500">timestamp</code> — ISO 8601 datetime</li>
                    <li><code className="text-zinc-500">duration</code> — Duration in seconds (number)</li>
                    <li><code className="text-zinc-500">source_type</code> — &quot;live&quot; | &quot;studio&quot; | &quot;rehearsal&quot; | &quot;dispute&quot;</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <div className="flex items-start gap-4">
                <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">signature</code>
                <div className="text-zinc-400 text-sm">
                  <p>Ed25519 signature from the creator.</p>
                  <p className="text-zinc-600 mt-1">Format: <code className="text-zinc-500">&quot;ed25519:&lt;base64&gt;&quot;</code></p>
                  <p className="text-zinc-600">Signed message: SHA-256(fingerprint + canonical metadata)</p>
                </div>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <div className="flex items-start gap-4">
                <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">public_key</code>
                <div className="text-zinc-400 text-sm">
                  <p>Ed25519 public key for verification.</p>
                  <p className="text-zinc-600 mt-1">Format: Base64, 32 bytes decoded</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Optional */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Optional Fields
          </h2>
          
          <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
            <div className="flex items-start gap-4">
              <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">segments</code>
              <div className="text-zinc-400 text-sm">
                <p>List of per-segment fingerprints. Recommended for granular proof.</p>
                <ul className="text-zinc-600 mt-2 space-y-1 ml-4">
                  <li><code className="text-zinc-500">t0</code> — Start time (seconds)</li>
                  <li><code className="text-zinc-500">t1</code> — End time (seconds)</li>
                  <li><code className="text-zinc-500">h</code> — SHA-256 hash of segment</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Hash Format */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Hash Format
          </h2>
          <div className="text-zinc-400 space-y-4 text-sm">
            <p>All FREK hashes follow the prefixed format:</p>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4 font-mono">
              <code className="text-[#00F0FF]">sha256:</code><code className="text-zinc-500">&lt;64 lowercase hexadecimal characters&gt;</code>
            </div>
            <p>Example:</p>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4 font-mono text-xs break-all">
              sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
            </div>
          </div>
        </section>

        {/* Validation Rules */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Validation Rules
          </h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">1.</span>
              <p><code className="text-zinc-500">frek_version</code> must be exactly &quot;0.4&quot;</p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">2.</span>
              <p><code className="text-zinc-500">fingerprint</code> must match regex <code className="text-zinc-600">^sha256:[a-f0-9]&#123;64&#125;$</code></p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">3.</span>
              <p><code className="text-zinc-500">metadata.timestamp</code> must be valid ISO 8601</p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">4.</span>
              <p><code className="text-zinc-500">metadata.duration</code> must be a positive number</p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">5.</span>
              <p><code className="text-zinc-500">metadata.source_type</code> must be a valid enum value</p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">6.</span>
              <p><code className="text-zinc-500">signature</code> must match regex <code className="text-zinc-600">^ed25519:[A-Za-z0-9+/=]+$</code></p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">7.</span>
              <p><code className="text-zinc-500">public_key</code> must be valid base64 (32 bytes decoded)</p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">8.</span>
              <p><code className="text-zinc-500">metadata</code> must NOT contain required PII (name, email, IP)</p>
            </div>
          </div>
        </section>

        {/* Versioning */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Versioning
          </h2>
          <div className="text-zinc-400 space-y-4 text-sm">
            <p>FREK uses simplified semantic versioning:</p>
            <ul className="list-none space-y-2 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">MAJOR.MINOR</span>
                <span>— Breaking changes = MAJOR increment</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">0.x</span>
                <span>— Development phase, changes possible</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">1.0+</span>
                <span>— Stabilized standard, backward compatibility guaranteed</span>
              </li>
            </ul>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4 mt-4">
              <p className="font-mono text-xs text-zinc-600">
                Current version: <span className="text-[#00F0FF]">0.4</span><br/>
                Next planned version: <span className="text-zinc-500">0.5</span>
              </p>
            </div>
          </div>
        </section>

        {/* Navigation */}
        <div className="border-t border-zinc-800 pt-8 flex justify-between items-center">
          <NavLink 
            to="/docs/architecture" 
            className="flex items-center gap-2 text-zinc-500 font-mono text-sm hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            Architecture
          </NavLink>
          <NavLink 
            to="/docs/governance" 
            className="flex items-center gap-2 text-[#00F0FF] font-mono text-sm hover:underline"
          >
            Governance
            <ArrowRight className="w-4 h-4" />
          </NavLink>
        </div>
      </div>
    </div>
  );
}

export default DocsSpec;
