import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, ArrowLeft } from 'lucide-react';

export function Governance() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Documentation
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          Gouvernance FREK
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          Modèle de gouvernance anti-capture. Règles de mise à jour et séparation vision/implémentation.
        </p>
      </div>

      {/* Content */}
      <div className="space-y-12">
        
        {/* Organisme Gardien */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Organisme Gardien du Standard
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              Le standard FREK est maintenu par un organisme indépendant dont le rôle est strictement limité à:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-[#00FF94] mb-2">
                  Responsabilités
                </p>
                <ul className="text-sm space-y-1">
                  <li>• Publication des spécifications</li>
                  <li>• Validation des changements de version</li>
                  <li>• Maintenance des outils de référence</li>
                  <li>• Arbitrage technique (non commercial)</li>
                </ul>
              </div>
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-[#FF3333] mb-2">
                  Interdictions
                </p>
                <ul className="text-sm space-y-1">
                  <li>• Commercialiser le standard</li>
                  <li>• Créer une plateforme FREK officielle</li>
                  <li>• Collecter des données utilisateurs</li>
                  <li>• Certifier des implémentations contre paiement</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Règles de mise à jour */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Règles de Mise à Jour
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>Toute modification du standard FREK suit un processus strict:</p>
            
            <div className="space-y-3">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-[#00F0FF] text-sm">01</span>
                  <div>
                    <p className="font-mono text-zinc-300 text-sm">Proposition publique (FIP)</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      Toute modification doit être proposée publiquement via un FREK Improvement Proposal (FIP).
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-[#00F0FF] text-sm">02</span>
                  <div>
                    <p className="font-mono text-zinc-300 text-sm">Période de commentaires (30 jours minimum)</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      La communauté peut commenter, critiquer, ou proposer des alternatives.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-[#00F0FF] text-sm">03</span>
                  <div>
                    <p className="font-mono text-zinc-300 text-sm">Implémentation de référence</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      Une implémentation de référence doit accompagner chaque FIP accepté.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-[#00F0FF] text-sm">04</span>
                  <div>
                    <p className="font-mono text-zinc-300 text-sm">Vote de ratification</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      Majorité qualifiée (2/3) des mainteneurs actifs requise.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-[#00F0FF] text-sm">05</span>
                  <div>
                    <p className="font-mono text-zinc-300 text-sm">Publication et changelog</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      Nouvelle version publiée avec documentation complète des changements.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Anti-capture */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Mécanismes Anti-Capture
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              Le standard FREK est protégé contre la capture commerciale ou politique par les mécanismes suivants:
            </p>
            
            <div className="space-y-4">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-[#00F0FF] mb-2">Licence Copyleft</p>
                <p className="text-sm">
                  Le standard et les outils de référence sont sous licence copyleft. 
                  Toute modification doit rester open source.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-[#00F0FF] mb-2">Interdiction de Marque Exclusive</p>
                <p className="text-sm">
                  Aucune entité ne peut revendiquer l'exclusivité sur le nom "FREK" pour des produits commerciaux.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-[#00F0FF] mb-2">Rotation des Mainteneurs</p>
                <p className="text-sm">
                  Les mainteneurs sont renouvelés par tiers tous les 2 ans. 
                  Aucun mainteneur ne peut avoir de conflit d'intérêt commercial.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-[#00F0FF] mb-2">Fork Autorisé</p>
                <p className="text-sm">
                  En cas de dérive, la communauté peut forker le standard. 
                  La légitimité vient de l'adoption, pas de l'autorité.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-[#00F0FF] mb-2">Veto Communautaire</p>
                <p className="text-sm">
                  Tout changement peut être bloqué par un veto de 1/3 des utilisateurs actifs vérifiés.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Séparation Vision / Implémentation */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Séparation Vision / Implémentation
          </h2>
          <div className="text-zinc-400 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-3">
                  Vision (Standard)
                </p>
                <ul className="text-sm space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Définit le "quoi" et le "pourquoi"
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Spécifie les formats et règles
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Reste stable et prévisible
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Gouverné par consensus
                  </li>
                </ul>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-3">
                  Implémentation (Outils)
                </p>
                <ul className="text-sm space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Définit le "comment"
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Plugins, apps, APIs
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Peut évoluer librement
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Gouverné par les développeurs
                  </li>
                </ul>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-[#00F0FF]/30 p-4 mt-4">
              <p className="font-mono text-sm text-zinc-300">
                Règle fondamentale: Le standard ne dicte jamais l'implémentation. 
                L'implémentation ne modifie jamais le standard.
              </p>
            </div>
          </div>
        </section>

        {/* Implémentations Autorisées */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Implémentations Autorisées
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>Tout développeur peut créer une implémentation FREK, notamment:</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-zinc-300 mb-2">Plugin DAW Offline</p>
                <p className="text-xs text-zinc-600">
                  Intégration dans Ableton, Logic, Traktor. 
                  Génération d'attestation pendant le mix.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-zinc-300 mb-2">Application Mobile</p>
                <p className="text-xs text-zinc-600">
                  Capture audio locale. 
                  Génération d'attestation sans connexion.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-zinc-300 mb-2">API Volontaire</p>
                <p className="text-xs text-zinc-600">
                  Services de vérification opt-in. 
                  Archivage décentralisé optionnel.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-zinc-300 mb-2">Outils de Vérification</p>
                <p className="text-xs text-zinc-600">
                  Validateurs CLI, web, ou intégrés. 
                  Comparaison d'empreintes.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Navigation */}
        <div className="border-t border-zinc-800 pt-8 flex justify-between items-center">
          <NavLink 
            to="/spec" 
            className="flex items-center gap-2 text-zinc-500 font-mono text-sm hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            Spécification
          </NavLink>
          <NavLink 
            to="/changelog" 
            className="flex items-center gap-2 text-[#00F0FF] font-mono text-sm hover:underline"
          >
            Changelog
            <ArrowRight className="w-4 h-4" />
          </NavLink>
        </div>
      </div>
    </div>
  );
}

export default Governance;
