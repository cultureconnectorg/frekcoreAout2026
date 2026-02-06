import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, Shield, Music, Lock, Eye, FileCheck } from 'lucide-react';

export function Standard() {
  return (
    <div className="min-h-screen bg-[#030303]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#030303]/90 backdrop-blur-sm border-b border-zinc-900">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#00F0FF] flex items-center justify-center">
              <span className="font-mono font-bold text-black text-sm">F</span>
            </div>
            <span className="font-mono font-bold text-lg tracking-tight text-white">FREK</span>
          </NavLink>
          
          <div className="hidden md:flex items-center gap-8">
            <span className="font-mono text-sm text-white">Standard</span>
            <NavLink to="/industry" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Industry
            </NavLink>
            <NavLink to="/docs" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Docs
            </NavLink>
            <NavLink 
              to="/verify" 
              className="font-mono text-sm px-4 py-2 bg-[#00F0FF] text-black hover:bg-[#00F0FF]/90 transition-colors"
            >
              Verify
            </NavLink>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00F0FF] mb-6">
            The Standard
          </p>
          <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl text-white mb-6 font-light leading-tight">
            What is FREK?
          </h1>
          <p className="text-xl text-zinc-400 max-w-2xl mx-auto">
            FREK is a way to prove that a musical performance happened, 
            when it happened, and who created it — without tracking or surveillance.
          </p>
        </div>
      </section>

      {/* Simple Explanation */}
      <section className="py-24 px-6 border-t border-zinc-900">
        <div className="max-w-3xl mx-auto">
          <h2 className="font-serif text-3xl text-white mb-8 font-light text-center">
            In Simple Terms
          </h2>
          
          <div className="space-y-8 text-lg text-zinc-400 leading-relaxed">
            <p>
              Imagine you could create a unique "fingerprint" of your DJ set or music performance. 
              This fingerprint is like a digital seal that proves your work is authentic.
            </p>
            
            <p>
              FREK does exactly this. It analyzes your audio and creates a mathematical signature 
              that can never be faked or altered. This signature is stored in a small file that 
              you control completely.
            </p>
            
            <p>
              Anyone can verify your work later — checking that the audio hasn't been modified 
              and that you are indeed the creator. All of this happens on their own device, 
              without sending your music anywhere.
            </p>

            <div className="bg-[#0A0A0A] border border-zinc-800 p-6 my-8">
              <p className="text-zinc-300 font-medium mb-2">The key difference:</p>
              <p className="text-zinc-500">
                Unlike platforms that track and monitor your music, FREK gives you proof 
                without surveillance. You own your attestation. No company controls it.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6 bg-[#050505]">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-serif text-3xl text-white mb-12 font-light text-center">
            How It Works
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-6">
                <Music className="w-8 h-8 text-zinc-600" />
              </div>
              <h3 className="font-mono text-white mb-3">1. Create</h3>
              <p className="text-zinc-500 text-sm">
                Record your performance or mix. FREK analyzes the audio locally 
                and creates a unique fingerprint.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-6">
                <Lock className="w-8 h-8 text-zinc-600" />
              </div>
              <h3 className="font-mono text-white mb-3">2. Sign</h3>
              <p className="text-zinc-500 text-sm">
                Your private key signs the fingerprint, binding it to your identity. 
                Only you can create this signature.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-6">
                <FileCheck className="w-8 h-8 text-zinc-600" />
              </div>
              <h3 className="font-mono text-white mb-3">3. Verify</h3>
              <p className="text-zinc-500 text-sm">
                Anyone can check your attestation. They verify the signature and 
                compare the fingerprint — all locally.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* What FREK Is Not */}
      <section className="py-24 px-6 border-t border-zinc-900">
        <div className="max-w-3xl mx-auto">
          <h2 className="font-serif text-3xl text-white mb-12 font-light text-center">
            What FREK Is Not
          </h2>
          
          <div className="space-y-6">
            <div className="flex gap-4 items-start">
              <div className="w-8 h-8 bg-[#FF3333]/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-[#FF3333] font-mono text-sm">✕</span>
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">Not a Platform</h3>
                <p className="text-zinc-500">
                  FREK is a standard, not a service. There's no website where your music lives. 
                  You keep your files wherever you want.
                </p>
              </div>
            </div>
            
            <div className="flex gap-4 items-start">
              <div className="w-8 h-8 bg-[#FF3333]/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-[#FF3333] font-mono text-sm">✕</span>
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">Not a Tracking System</h3>
                <p className="text-zinc-500">
                  FREK doesn't monitor plays, collect analytics, or track who listens to what. 
                  It only proves authenticity when you choose to verify.
                </p>
              </div>
            </div>
            
            <div className="flex gap-4 items-start">
              <div className="w-8 h-8 bg-[#FF3333]/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-[#FF3333] font-mono text-sm">✕</span>
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">Not a Music Recognition Service</h3>
                <p className="text-zinc-500">
                  Unlike Shazam or similar services, FREK doesn't identify songs or match 
                  against a database. It only verifies what you choose to attest.
                </p>
              </div>
            </div>
            
            <div className="flex gap-4 items-start">
              <div className="w-8 h-8 bg-[#FF3333]/10 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-[#FF3333] font-mono text-sm">✕</span>
              </div>
              <div>
                <h3 className="text-white font-medium mb-1">Not a Ranking or Rating System</h3>
                <p className="text-zinc-500">
                  FREK doesn't judge quality or popularity. It doesn't score artists. 
                  It simply proves technical facts.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Who Uses FREK */}
      <section className="py-24 px-6 bg-[#050505]">
        <div className="max-w-3xl mx-auto">
          <h2 className="font-serif text-3xl text-white mb-12 font-light text-center">
            Who Uses FREK
          </h2>
          
          <div className="space-y-6">
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-white mb-2">DJs & Live Performers</h3>
              <p className="text-zinc-500">
                Prove that your live set happened on a specific date, protecting your creative work 
                from disputes or unauthorized copies.
              </p>
            </div>
            
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-white mb-2">Music Producers</h3>
              <p className="text-zinc-500">
                Create verifiable timestamps for your productions, establishing clear provenance 
                for your work.
              </p>
            </div>
            
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-white mb-2">Labels & Distributors</h3>
              <p className="text-zinc-500">
                Verify master recordings and track authenticity throughout the distribution chain.
              </p>
            </div>
            
            <div className="p-6 border border-zinc-800 bg-[#0A0A0A]">
              <h3 className="font-mono text-white mb-2">Event Organizers</h3>
              <p className="text-zinc-500">
                Document performances with cryptographic proof for archival and legal purposes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-zinc-900">
        <div className="max-w-xl mx-auto text-center">
          <h2 className="font-serif text-3xl text-white mb-6 font-light">
            Try It Yourself
          </h2>
          <p className="text-zinc-500 mb-8">
            Verify an audio file right now. No account needed. 
            Everything runs in your browser.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <NavLink 
              to="/verify"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-black font-mono text-sm uppercase tracking-wide hover:bg-zinc-200 transition-colors"
            >
              <Shield className="w-4 h-4" />
              Verify Audio
            </NavLink>
            <NavLink 
              to="/manifesto"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border border-zinc-700 text-white font-mono text-sm uppercase tracking-wide hover:border-zinc-500 transition-colors"
            >
              Read Manifesto
              <ArrowRight className="w-4 h-4" />
            </NavLink>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-zinc-900">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-[#00F0FF] flex items-center justify-center">
              <span className="font-mono font-bold text-black text-xs">F</span>
            </div>
            <span className="font-mono text-sm text-zinc-500">FREK — Open Musical Proof Standard</span>
          </div>
          <div className="flex gap-6">
            <NavLink to="/" className="font-mono text-sm text-zinc-500 hover:text-white">Home</NavLink>
            <NavLink to="/docs" className="font-mono text-sm text-zinc-500 hover:text-white">Docs</NavLink>
            <NavLink to="/verify" className="font-mono text-sm text-zinc-500 hover:text-white">Verify</NavLink>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Standard;
