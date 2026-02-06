import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, ArrowLeft } from 'lucide-react';

export function DocsGovernance() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Developer Documentation
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          FREK Governance
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          Anti-capture governance model. Update rules and vision/implementation separation.
        </p>
      </div>

      {/* Content */}
      <div className="space-y-12">
        
        {/* Guardian Organization */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Standard Guardian Organization
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              The FREK standard is maintained by an independent body whose role is strictly limited to:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-[#00FF94] mb-2">
                  Responsibilities
                </p>
                <ul className="text-sm space-y-1">
                  <li>• Publish specifications</li>
                  <li>• Validate version changes</li>
                  <li>• Maintain reference tools</li>
                  <li>• Technical arbitration (non-commercial)</li>
                </ul>
              </div>
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-[#FF3333] mb-2">
                  Prohibitions
                </p>
                <ul className="text-sm space-y-1">
                  <li>• Commercialize the standard</li>
                  <li>• Create an official FREK platform</li>
                  <li>• Collect user data</li>
                  <li>• Certify implementations for payment</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Update Rules */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Update Rules
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>Any modification to the FREK standard follows a strict process:</p>
            
            <div className="space-y-3">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-[#00F0FF] text-sm">01</span>
                  <div>
                    <p className="font-mono text-zinc-300 text-sm">Public Proposal (FIP)</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      Any modification must be publicly proposed via a FREK Improvement Proposal (FIP).
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-[#00F0FF] text-sm">02</span>
                  <div>
                    <p className="font-mono text-zinc-300 text-sm">Comment Period (30 days minimum)</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      The community can comment, critique, or propose alternatives.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-[#00F0FF] text-sm">03</span>
                  <div>
                    <p className="font-mono text-zinc-300 text-sm">Reference Implementation</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      A reference implementation must accompany each accepted FIP.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-[#00F0FF] text-sm">04</span>
                  <div>
                    <p className="font-mono text-zinc-300 text-sm">Ratification Vote</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      Qualified majority (2/3) of active maintainers required.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-[#00F0FF] text-sm">05</span>
                  <div>
                    <p className="font-mono text-zinc-300 text-sm">Publication and Changelog</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      New version published with complete documentation of changes.
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
            Anti-Capture Mechanisms
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>
              The FREK standard is protected against commercial or political capture by these mechanisms:
            </p>
            
            <div className="space-y-4">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-[#00F0FF] mb-2">Copyleft License</p>
                <p className="text-sm">
                  The standard and reference tools are under copyleft license. 
                  Any modification must remain open source.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-[#00F0FF] mb-2">Trademark Exclusivity Ban</p>
                <p className="text-sm">
                  No entity can claim exclusivity on the &quot;FREK&quot; name for commercial products.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-[#00F0FF] mb-2">Maintainer Rotation</p>
                <p className="text-sm">
                  Maintainers are renewed by thirds every 2 years. 
                  No maintainer can have commercial conflict of interest.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-[#00F0FF] mb-2">Authorized Fork</p>
                <p className="text-sm">
                  In case of drift, the community can fork the standard. 
                  Legitimacy comes from adoption, not authority.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-[#00F0FF] mb-2">Community Veto</p>
                <p className="text-sm">
                  Any change can be blocked by a veto from 1/3 of verified active users.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Vision / Implementation Separation */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Vision / Implementation Separation
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
                    Defines &quot;what&quot; and &quot;why&quot;
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Specifies formats and rules
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Remains stable and predictable
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Governed by consensus
                  </li>
                </ul>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-3">
                  Implementation (Tools)
                </p>
                <ul className="text-sm space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Defines &quot;how&quot;
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Plugins, apps, APIs
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Can evolve freely
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#00F0FF]">→</span>
                    Governed by developers
                  </li>
                </ul>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-[#00F0FF]/30 p-4 mt-4">
              <p className="font-mono text-sm text-zinc-300">
                Fundamental rule: The standard never dictates implementation. 
                Implementation never modifies the standard.
              </p>
            </div>
          </div>
        </section>

        {/* Authorized Implementations */}
        <section>
          <h2 className="font-mono text-xl font-semibold text-white border-b border-zinc-800 pb-2 mb-4">
            Authorized Implementations
          </h2>
          <div className="text-zinc-400 space-y-4">
            <p>Any developer can create a FREK implementation, including:</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-zinc-300 mb-2">Offline DAW Plugin</p>
                <p className="text-xs text-zinc-600">
                  Integration into Ableton, Logic, Traktor. 
                  Attestation generation during mixing.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-zinc-300 mb-2">Mobile Application</p>
                <p className="text-xs text-zinc-600">
                  Local audio capture. 
                  Attestation generation without connection.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-zinc-300 mb-2">Voluntary API</p>
                <p className="text-xs text-zinc-600">
                  Opt-in verification services. 
                  Optional decentralized archival.
                </p>
              </div>

              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <p className="font-mono text-sm text-zinc-300 mb-2">Verification Tools</p>
                <p className="text-xs text-zinc-600">
                  CLI, web, or integrated validators. 
                  Fingerprint comparison.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Navigation */}
        <div className="border-t border-zinc-800 pt-8 flex justify-between items-center">
          <NavLink 
            to="/docs/spec" 
            className="flex items-center gap-2 text-zinc-500 font-mono text-sm hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            Specification
          </NavLink>
          <NavLink 
            to="/docs/changelog" 
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

export default DocsGovernance;
