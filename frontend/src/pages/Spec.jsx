import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, ArrowLeft, Copy, Check } from 'lucide-react';
import { EXAMPLE_FREK_DOC } from '../lib/frek-schema';

export function Spec() {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(EXAMPLE_FREK_DOC, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Documentation
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          Spécification .frek.json
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          Format de fichier FREK v0.4. Structure, règles de validation, et versioning.
        </p>
      </div>

      {/* Content */}
      <div className="space-y-12">
        
        {/* Format */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Structure du Fichier
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
{`{
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
}`}
            </pre>
          </div>
        </section>

        {/* Fields */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Champs Obligatoires
          </h2>
          
          <div className="space-y-4">
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <div className="flex items-start gap-4">
                <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">frek_version</code>
                <div className="text-zinc-400 text-sm">
                  <p>Version du standard FREK utilisée.</p>
                  <p className="text-zinc-600 mt-1">Format: <code className="text-zinc-500">"0.4"</code> (string)</p>
                </div>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <div className="flex items-start gap-4">
                <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">fingerprint</code>
                <div className="text-zinc-400 text-sm">
                  <p>Empreinte SHA-256 globale de l'audio normalisé.</p>
                  <p className="text-zinc-600 mt-1">Format: <code className="text-zinc-500">"sha256:&lt;64 caractères hex&gt;"</code></p>
                </div>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <div className="flex items-start gap-4">
                <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">metadata</code>
                <div className="text-zinc-400 text-sm">
                  <p>Contexte technique du mix.</p>
                  <ul className="text-zinc-600 mt-1 space-y-1 ml-4">
                    <li><code className="text-zinc-500">timestamp</code> — ISO 8601 datetime</li>
                    <li><code className="text-zinc-500">duration</code> — Durée en secondes (number)</li>
                    <li><code className="text-zinc-500">source_type</code> — "live" | "studio" | "rehearsal" | "dispute"</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <div className="flex items-start gap-4">
                <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">signature</code>
                <div className="text-zinc-400 text-sm">
                  <p>Signature Ed25519 du créateur.</p>
                  <p className="text-zinc-600 mt-1">Format: <code className="text-zinc-500">"ed25519:&lt;base64&gt;"</code></p>
                  <p className="text-zinc-600">Message signé: SHA-256(fingerprint + metadata canonicalisée)</p>
                </div>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <div className="flex items-start gap-4">
                <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">public_key</code>
                <div className="text-zinc-400 text-sm">
                  <p>Clé publique Ed25519 pour vérification.</p>
                  <p className="text-zinc-600 mt-1">Format: Base64, 32 bytes décodés</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Optional */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Champs Optionnels
          </h2>
          
          <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
            <div className="flex items-start gap-4">
              <code className="font-mono text-[#00F0FF] text-sm whitespace-nowrap">segments</code>
              <div className="text-zinc-400 text-sm">
                <p>Liste des empreintes par segment temporel. Recommandé pour preuve granulaire.</p>
                <ul className="text-zinc-600 mt-2 space-y-1 ml-4">
                  <li><code className="text-zinc-500">t0</code> — Temps de début (secondes)</li>
                  <li><code className="text-zinc-500">t1</code> — Temps de fin (secondes)</li>
                  <li><code className="text-zinc-500">h</code> — Hash SHA-256 du segment</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Hash Format */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Format du Hash
          </h2>
          <div className="text-zinc-400 space-y-4 text-sm">
            <p>Tous les hashes FREK suivent le format préfixé:</p>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4 font-mono">
              <code className="text-[#00F0FF]">sha256:</code><code className="text-zinc-500">&lt;64 caractères hexadécimaux lowercase&gt;</code>
            </div>
            <p>Exemple:</p>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4 font-mono text-xs break-all">
              sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
            </div>
          </div>
        </section>

        {/* Signature Format */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Format de Signature
          </h2>
          <div className="text-zinc-400 space-y-4 text-sm">
            <p>La signature Ed25519 suit le format préfixé:</p>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4 font-mono">
              <code className="text-[#00F0FF]">ed25519:</code><code className="text-zinc-500">&lt;signature base64, 88 caractères&gt;</code>
            </div>
            <p>Message signé = SHA-256 de:</p>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4 font-mono text-xs">
              fingerprint + JSON.stringify(metadata, sortedKeys)
            </div>
          </div>
        </section>

        {/* Rules */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Règles de Validation
          </h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">1.</span>
              <p><code className="text-zinc-500">frek_version</code> doit être exactement "0.4"</p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">2.</span>
              <p><code className="text-zinc-500">fingerprint</code> doit correspondre au regex <code className="text-zinc-600">^sha256:[a-f0-9]{'{64}'}$</code></p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">3.</span>
              <p><code className="text-zinc-500">metadata.timestamp</code> doit être ISO 8601 valide</p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">4.</span>
              <p><code className="text-zinc-500">metadata.duration</code> doit être un nombre positif</p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">5.</span>
              <p><code className="text-zinc-500">metadata.source_type</code> doit être une valeur enum valide</p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">6.</span>
              <p><code className="text-zinc-500">signature</code> doit correspondre au regex <code className="text-zinc-600">^ed25519:[A-Za-z0-9+/=]+$</code></p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">7.</span>
              <p><code className="text-zinc-500">public_key</code> doit être base64 valide (32 bytes décodés)</p>
            </div>
            <div className="flex items-start gap-3 text-zinc-400 text-sm">
              <span className="text-[#00FF94] font-mono">8.</span>
              <p><code className="text-zinc-500">metadata</code> ne doit PAS contenir de PII obligatoire (nom, email, IP)</p>
            </div>
          </div>
        </section>

        {/* Versioning */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Versioning
          </h2>
          <div className="text-zinc-400 space-y-4 text-sm">
            <p>FREK utilise le versioning sémantique simplifié:</p>
            <ul className="list-none space-y-2 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">MAJEUR.MINEUR</span>
                <span>— Incompatibilités = incrémentation MAJEUR</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">0.x</span>
                <span>— Phase de développement, changements possibles</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">1.0+</span>
                <span>— Standard stabilisé, rétrocompatibilité garantie</span>
              </li>
            </ul>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4 mt-4">
              <p className="font-mono text-xs text-zinc-600">
                Version actuelle: <span className="text-[#00F0FF]">0.4</span><br/>
                Prochaine version prévue: <span className="text-zinc-500">0.5</span>
              </p>
            </div>
          </div>
        </section>

        {/* Navigation */}
        <div className="border-t border-zinc-800 pt-8 flex justify-between items-center">
          <NavLink 
            to="/architecture" 
            className="flex items-center gap-2 text-zinc-500 font-mono text-sm hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            Architecture
          </NavLink>
          <NavLink 
            to="/governance" 
            className="flex items-center gap-2 text-[#00F0FF] font-mono text-sm hover:underline"
          >
            Gouvernance
            <ArrowRight className="w-4 h-4" />
          </NavLink>
        </div>
      </div>
    </div>
  );
}

export default Spec;
