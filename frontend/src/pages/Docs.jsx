import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

export function Docs() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Documentation
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          Manifeste FREK
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          Document fondateur du standard FREK. Version 0.4.
        </p>
      </div>

      {/* Content */}
      <div className="space-y-12">
        
        {/* Section 1 */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            1. Reconnaissance du Geste DJ
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              Le DJ mix est un acte de création technique. Sélection, séquence, transitions, 
              effets : chaque décision constitue une signature artistique unique.
            </p>
            <p>
              FREK existe pour prouver qu'un mix a eu lieu, tel qu'il a eu lieu, 
              au moment où il a eu lieu. Rien de plus.
            </p>
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <p className="font-mono text-sm text-zinc-500">
                FREK ne reconnaît pas la musique.<br/>
                FREK reconnaît un fait technique, dans un contexte précis.
              </p>
            </div>
          </div>
        </section>

        {/* Section 2 */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            2. Souveraineté Artistique
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              L'artiste contrôle ses preuves. Aucune autorité centrale ne peut :
            </p>
            <ul className="list-none space-y-2 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">—</span>
                Révoquer une attestation valide
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">—</span>
                Modifier une empreinte publiée
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">—</span>
                Imposer une reconnaissance ou un score
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">—</span>
                Collecter des métadonnées personnelles
              </li>
            </ul>
            <p>
              La clé privée de l'artiste est la seule autorité.
            </p>
          </div>
        </section>

        {/* Section 3 */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            3. Preuve Sans Surveillance
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              FREK n'a pas besoin de savoir qui vous êtes pour prouver ce que vous avez créé.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-[#00FF94] mb-2">
                  Ce que FREK fait
                </p>
                <ul className="text-sm space-y-1">
                  <li>• Calcul d'empreinte audio locale</li>
                  <li>• Signature cryptographique</li>
                  <li>• Horodatage technique</li>
                  <li>• Vérification hors-ligne</li>
                </ul>
              </div>
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-[#FF3333] mb-2">
                  Ce que FREK ne fait pas
                </p>
                <ul className="text-sm space-y-1">
                  <li>• Tracking d'écoutes</li>
                  <li>• Reconnaissance musicale cloud</li>
                  <li>• Collecte de données personnelles</li>
                  <li>• Scoring ou classement</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Section 4 */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            4. Standard Ouvert, Protégé
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              Le format <code className="bg-zinc-900 px-1 text-[#00F0FF]">.frek.json</code> est public. 
              N'importe qui peut :
            </p>
            <ul className="list-none space-y-2 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">→</span>
                Implémenter un générateur FREK
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">→</span>
                Créer un vérificateur FREK
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">→</span>
                Intégrer FREK dans un DAW
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#00F0FF] font-mono">→</span>
                Auditer le code de vérification
              </li>
            </ul>
            <p>
              Le standard est protégé contre la capture commerciale par sa gouvernance décentralisée.
            </p>
          </div>
        </section>

        {/* Section 5 */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            5. Principes Non Négociables
          </h2>
          <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
            <ul className="font-mono text-sm space-y-3">
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-[#00F0FF]"></span>
                FREK ne juge pas la musique
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-[#00F0FF]"></span>
                FREK ne classe pas les artistes
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-[#00F0FF]"></span>
                FREK ne collecte pas de données personnelles
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-[#00F0FF]"></span>
                FREK ne devient jamais une plateforme
              </li>
              <li className="flex items-center gap-3">
                <span className="w-2 h-2 bg-[#00F0FF]"></span>
                FREK fonctionne hors-ligne par défaut
              </li>
            </ul>
          </div>
        </section>

        {/* Navigation */}
        <div className="border-t border-zinc-800 pt-8 flex justify-between items-center">
          <div></div>
          <NavLink 
            to="/architecture" 
            className="flex items-center gap-2 text-[#00F0FF] font-mono text-sm hover:underline"
          >
            Architecture technique
            <ArrowRight className="w-4 h-4" />
          </NavLink>
        </div>
      </div>
    </div>
  );
}

export default Docs;
