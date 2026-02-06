import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, Shield, FileText } from 'lucide-react';

export function Home() {
  return (
    <div className="min-h-screen flex flex-col justify-center px-6 md:px-12 lg:px-24">
      <div className="max-w-3xl">
        {/* Pre-title */}
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-4">
          Infrastructure de Preuve Audio
        </p>
        
        {/* Title */}
        <h1 className="font-mono text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white mb-6">
          FREK
          <span className="text-[#00F0FF] ml-3 text-xl md:text-2xl align-top">v0.4</span>
        </h1>
        
        {/* Tagline */}
        <p className="font-mono text-lg md:text-xl text-zinc-400 mb-2 leading-relaxed max-w-2xl">
          Certifier qu'un mix DJ est authentique, non altéré, traçable, 
          et attribuable à son créateur.
        </p>
        
        {/* Principles */}
        <p className="text-zinc-600 text-sm mb-8 font-mono">
          Sans surveillance. Sans plateforme. Sans cloud obligatoire.
        </p>
        
        {/* Actions */}
        <div className="flex flex-wrap gap-4 mb-12">
          <NavLink 
            to="/docs"
            className="inline-flex items-center gap-2 px-6 py-3 bg-zinc-100 text-black font-mono text-sm uppercase tracking-wide hover:bg-zinc-300 transition-colors"
            data-testid="docs-link"
          >
            <FileText className="w-4 h-4" strokeWidth={1.5} />
            Documentation
            <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
          </NavLink>
          
          <NavLink 
            to="/verify"
            className="inline-flex items-center gap-2 px-6 py-3 border border-[#00F0FF] text-[#00F0FF] font-mono text-sm uppercase tracking-wide hover:bg-[#00F0FF]/10 transition-colors"
            data-testid="verify-link"
          >
            <Shield className="w-4 h-4" strokeWidth={1.5} />
            Vérifier un fichier
            <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
          </NavLink>
        </div>
        
        {/* Key principles */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 border-t border-zinc-800 pt-8">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-600 mb-2">
              Preuve
            </p>
            <p className="text-zinc-400 text-sm">
              Empreinte cryptographique Ed25519 irréversible
            </p>
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-600 mb-2">
              Local-First
            </p>
            <p className="text-zinc-400 text-sm">
              Tout fonctionne hors-ligne, sur votre machine
            </p>
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-600 mb-2">
              Standard Ouvert
            </p>
            <p className="text-zinc-400 text-sm">
              Spécification publique, implémentations libres
            </p>
          </div>
        </div>
        
        {/* Footer note */}
        <p className="font-mono text-[10px] text-zinc-700 mt-12 max-w-xl">
          FREK ne juge pas la musique. FREK ne classe pas les artistes. 
          FREK reconnaît un fait technique, dans un contexte précis.
        </p>
      </div>
    </div>
  );
}

export default Home;
