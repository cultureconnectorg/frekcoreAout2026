import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, ArrowLeft } from 'lucide-react';

export function Architecture() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Documentation
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          Architecture FREK v0.4
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          Pipeline de preuve audio locale. Preuve {'>'} Service. Local-First. Anti-Surveillance.
        </p>
      </div>

      {/* Pipeline Overview */}
      <div className="mb-12">
        <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-6">
          Pipeline de Preuve
        </h2>
        
        {/* Flow diagram */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {/* Stage 1 */}
          <div className="bg-[#0A0A0A] border border-red-900/50 p-4">
            <p className="font-mono text-xs uppercase tracking-widest text-red-500 mb-3">
              1. Source & Capture
            </p>
            <div className="space-y-2 text-sm text-zinc-400">
              <p className="font-mono text-zinc-300">Réalité Audio</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• DJ Mix / Live</li>
                <li>• Performance</li>
                <li>• Répétition</li>
                <li>• Diffusion contestée</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">Capture Volontaire</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Recorder / DAW</li>
                <li>• WAV Brut</li>
                <li>• Pas de cloud</li>
              </ul>
            </div>
          </div>

          {/* Stage 2 */}
          <div className="bg-[#0A0A0A] border border-blue-900/50 p-4">
            <p className="font-mono text-xs uppercase tracking-widest text-blue-500 mb-3">
              2. Noeud Souverain
            </p>
            <div className="space-y-2 text-sm text-zinc-400">
              <p className="font-mono text-zinc-300">Machine Locale</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Hors réseau</li>
                <li>• Contrôle total</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">Normalisation</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Mono - 44.1 kHz</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">Segmentation</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• 2-5 sec segments</li>
                <li>• Horodaté</li>
              </ul>
            </div>
          </div>

          {/* Stage 3 */}
          <div className="bg-[#0A0A0A] border border-green-900/50 p-4">
            <p className="font-mono text-xs uppercase tracking-widest text-green-500 mb-3">
              3. Analyse & Preuve
            </p>
            <div className="space-y-2 text-sm text-zinc-400">
              <p className="font-mono text-zinc-300">Analyse Spectrale</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• FFT / Spectrogramme</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">Fingerprint FREK</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Hash SHA-256</li>
                <li>• Non réversible</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">Attestation FREK</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Signature Ed25519</li>
                <li>• Preuve technique</li>
              </ul>
            </div>
          </div>

          {/* Stage 4 */}
          <div className="bg-[#0A0A0A] border border-yellow-900/50 p-4">
            <p className="font-mono text-xs uppercase tracking-widest text-yellow-500 mb-3">
              4. Matching Assisté
            </p>
            <div className="space-y-2 text-sm text-zinc-400">
              <p className="font-mono text-zinc-300">Matching Local</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Comparaison locale</li>
                <li>• Seuil contrôlé</li>
              </ul>
              <p className="font-mono text-zinc-300 mt-3">Match Claim</p>
              <ul className="text-xs space-y-1 ml-2">
                <li>• Segment + Score</li>
                <li>• Interprétation humaine</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Arrow indicators */}
        <div className="hidden md:flex justify-center gap-8 text-zinc-700 font-mono text-xs mb-8">
          <span>CAPTURE → NORMALISATION → FINGERPRINT → VÉRIFICATION</span>
        </div>
      </div>

      {/* Couches */}
      <div className="space-y-8 mb-12">
        <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2">
          Couches du Standard
        </h2>

        {/* Layer 1 */}
        <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <h3 className="font-mono text-sm uppercase tracking-widest text-[#00F0FF] mb-3">
            Couche Fingerprint Audio
          </h3>
          <div className="text-zinc-400 space-y-2 text-sm">
            <p>Transformation irréversible de l'audio en empreinte unique.</p>
            <ul className="list-none space-y-1 ml-4">
              <li><span className="text-zinc-600 font-mono">Entrée:</span> Flux audio normalisé (44.1kHz, mono)</li>
              <li><span className="text-zinc-600 font-mono">Traitement:</span> Analyse spectrale FFT par segments</li>
              <li><span className="text-zinc-600 font-mono">Sortie:</span> Hash SHA-256 global + hashes par segment</li>
            </ul>
          </div>
        </div>

        {/* Layer 2 */}
        <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <h3 className="font-mono text-sm uppercase tracking-widest text-[#00F0FF] mb-3">
            Couche Signature Cryptographique
          </h3>
          <div className="text-zinc-400 space-y-2 text-sm">
            <p>Authentification du créateur par signature Ed25519.</p>
            <ul className="list-none space-y-1 ml-4">
              <li><span className="text-zinc-600 font-mono">Algorithme:</span> Ed25519 (Curve25519)</li>
              <li><span className="text-zinc-600 font-mono">Message signé:</span> Hash(fingerprint + metadata canonicalisée)</li>
              <li><span className="text-zinc-600 font-mono">Clé:</span> Paire publique/privée contrôlée par l'artiste</li>
            </ul>
          </div>
        </div>

        {/* Layer 3 */}
        <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <h3 className="font-mono text-sm uppercase tracking-widest text-[#00F0FF] mb-3">
            Couche Attestation
          </h3>
          <div className="text-zinc-400 space-y-2 text-sm">
            <p>Déclaration formelle liant l'empreinte à un contexte.</p>
            <ul className="list-none space-y-1 ml-4">
              <li><span className="text-zinc-600 font-mono">Contenu:</span> Fingerprint + Signature + Métadonnées</li>
              <li><span className="text-zinc-600 font-mono">Format:</span> .frek.json (JSON structuré)</li>
              <li><span className="text-zinc-600 font-mono">Portabilité:</span> Fichier autonome, vérifiable hors-ligne</li>
            </ul>
          </div>
        </div>

        {/* Layer 4 */}
        <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <h3 className="font-mono text-sm uppercase tracking-widest text-[#00F0FF] mb-3">
            Couche Métadonnées
          </h3>
          <div className="text-zinc-400 space-y-2 text-sm">
            <p>Contexte technique minimal, sans données personnelles obligatoires.</p>
            <ul className="list-none space-y-1 ml-4">
              <li><span className="text-zinc-600 font-mono">Obligatoire:</span> timestamp, duration, source_type</li>
              <li><span className="text-zinc-600 font-mono">Optionnel:</span> Champs additionnels non-PII</li>
              <li><span className="text-zinc-600 font-mono">Interdit:</span> Nom réel, email, localisation, IP</li>
            </ul>
          </div>
        </div>

        {/* Layer 5 */}
        <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
          <h3 className="font-mono text-sm uppercase tracking-widest text-[#00F0FF] mb-3">
            Couche Export
          </h3>
          <div className="text-zinc-400 space-y-2 text-sm">
            <p>Distribution et archivage des attestations.</p>
            <ul className="list-none space-y-1 ml-4">
              <li><span className="text-zinc-600 font-mono">Format principal:</span> .frek.json</li>
              <li><span className="text-zinc-600 font-mono">Stockage:</span> Local, cloud optionnel, blockchain optionnelle</li>
              <li><span className="text-zinc-600 font-mono">Vérification:</span> Tout vérificateur compatible peut valider</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Responsabilités */}
      <div className="mb-12">
        <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-6">
          Séparation des Responsabilités
        </h2>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-center">
          <div className="bg-[#0A0A0A] border border-zinc-800 p-3">
            <p className="font-mono text-[10px] uppercase tracking-widest text-blue-500">Capture</p>
            <p className="text-xs text-zinc-500 mt-1">Opérateur</p>
          </div>
          <div className="bg-[#0A0A0A] border border-zinc-800 p-3">
            <p className="font-mono text-[10px] uppercase tracking-widest text-green-500">Analyse</p>
            <p className="text-xs text-zinc-500 mt-1">Opérateur</p>
          </div>
          <div className="bg-[#0A0A0A] border border-zinc-800 p-3">
            <p className="font-mono text-[10px] uppercase tracking-widest text-yellow-500">Matching</p>
            <p className="text-xs text-zinc-500 mt-1">Opérateur</p>
          </div>
          <div className="bg-[#0A0A0A] border border-zinc-800 p-3">
            <p className="font-mono text-[10px] uppercase tracking-widest text-orange-500">Interprétation</p>
            <p className="text-xs text-zinc-500 mt-1">Humain</p>
          </div>
          <div className="bg-[#0A0A0A] border border-zinc-800 p-3">
            <p className="font-mono text-[10px] uppercase tracking-widest text-red-500">Décision</p>
            <p className="text-xs text-zinc-500 mt-1">Légale / Humain</p>
          </div>
        </div>

        <p className="font-mono text-xs text-zinc-600 mt-4 text-center">
          FREK = Preuve technique → Humain = Interprétation → Juridique = Décision
        </p>
      </div>

      {/* Navigation */}
      <div className="border-t border-zinc-800 pt-8 flex justify-between items-center">
        <NavLink 
          to="/docs" 
          className="flex items-center gap-2 text-zinc-500 font-mono text-sm hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" />
          Manifeste
        </NavLink>
        <NavLink 
          to="/spec" 
          className="flex items-center gap-2 text-[#00F0FF] font-mono text-sm hover:underline"
        >
          Spécification .frek.json
          <ArrowRight className="w-4 h-4" />
        </NavLink>
      </div>
    </div>
  );
}

export default Architecture;
