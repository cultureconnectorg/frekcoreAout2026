import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowLeft, Shield } from 'lucide-react';

export function Changelog() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Documentation
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          Changelog
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          Historique des versions du standard FREK.
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
                2024-04-20 — Version actuelle
              </p>
            </div>
            <span className="font-mono text-[10px] uppercase tracking-widest px-2 py-1 bg-[#00F0FF]/10 text-[#00F0FF] border border-[#00F0FF]/30">
              Current
            </span>
          </div>
          
          <div className="space-y-4 text-sm">
            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-[#00FF94] mb-2">
                Ajouts
              </p>
              <ul className="text-zinc-400 space-y-1 ml-4">
                <li>• Spécification complète du format .frek.json</li>
                <li>• Schéma JSON avec validation Zod</li>
                <li>• Support des segments temporels (optionnel)</li>
                <li>• Signature Ed25519 obligatoire</li>
                <li>• Module de vérification web local-first</li>
                <li>• Documentation du manifeste</li>
                <li>• Architecture pipeline documentée</li>
                <li>• Modèle de gouvernance anti-capture</li>
              </ul>
            </div>

            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-[#FFB800] mb-2">
                Modifications
              </p>
              <ul className="text-zinc-400 space-y-1 ml-4">
                <li>• Format de hash standardisé: sha256:&lt;hex&gt;</li>
                <li>• Format de signature standardisé: ed25519:&lt;base64&gt;</li>
                <li>• Métadonnées minimales obligatoires définies</li>
              </ul>
            </div>

            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
                Notes techniques
              </p>
              <ul className="text-zinc-500 space-y-1 ml-4">
                <li>• Algorithme de fingerprint: SHA-256 sur audio normalisé</li>
                <li>• Normalisation: 44.1kHz, mono, PCM</li>
                <li>• Cryptographie: Ed25519 (Curve25519)</li>
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
                Contenu
              </p>
              <ul className="text-zinc-500 space-y-1 ml-4">
                <li>• Prototype initial du format JSON</li>
                <li>• Expérimentation signature ECDSA (abandonné)</li>
                <li>• Premier draft du manifeste</li>
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
              <li>• Recherche sur les algorithmes de fingerprint</li>
              <li>• Études comparatives FFT vs perceptual hashing</li>
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
              <li>• Concept initial FREK</li>
              <li>• Définition des principes fondateurs</li>
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
                  Prévu — Q3 2024
                </p>
              </div>
              <span className="font-mono text-[10px] uppercase tracking-widest px-2 py-1 bg-zinc-900 text-zinc-500 border border-zinc-800">
                Planned
              </span>
            </div>
            
            <div className="text-sm">
              <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
                Objectifs proposés
              </p>
              <ul className="text-zinc-500 space-y-1 ml-4">
                <li>• Support de fingerprint perceptuel avancé</li>
                <li>• Extension métadonnées optionnelles</li>
                <li>• Spécification d'interopérabilité blockchain</li>
                <li>• SDK de référence multi-langage</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Navigation */}
        <div className="border-t border-zinc-800 pt-8 flex justify-between items-center">
          <NavLink 
            to="/governance" 
            className="flex items-center gap-2 text-zinc-500 font-mono text-sm hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            Gouvernance
          </NavLink>
          <NavLink 
            to="/verify" 
            className="flex items-center gap-2 text-[#00F0FF] font-mono text-sm hover:underline"
          >
            <Shield className="w-4 h-4" />
            Vérifier un fichier
          </NavLink>
        </div>
      </div>
    </div>
  );
}

export default Changelog;
