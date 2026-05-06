/** Login PIN — pavé numérique 4-8 chiffres */
import { useState } from 'react';
import { api } from './lib';

export default function ScanLogin({ onLogin }) {
  const [agentId, setAgentId] = useState('');
  const [pin, setPin] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const submit = async (e) => {
    e?.preventDefault();
    if (!agentId || pin.length < 4) return;
    setBusy(true); setErr(null);
    try {
      const r = await api.login(agentId.trim().toUpperCase(), pin);
      onLogin(r.access_token, {
        agent_id: r.agent_id, nom: r.nom, role: r.role, permissions: r.permissions,
      });
    } catch (e) {
      setErr(e.message || 'Identifiants invalides');
      setPin('');
    } finally {
      setBusy(false);
    }
  };

  const padDigit = (d) => {
    if (pin.length >= 8) return;
    setPin(pin + d);
  };

  return (
    <div className="min-h-[80vh] flex flex-col justify-center" data-testid="scan-login">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#f7931a]/15 border border-[#f7931a]/30 mb-3">
          <span className="text-[#f7931a] text-2xl font-bold">₿</span>
        </div>
        <h1 className="font-mono text-2xl uppercase tracking-widest text-white mb-1">Scanner Staff</h1>
        <p className="font-mono text-[11px] text-white/40 tracking-wider uppercase">CC2026 · Fort-de-France</p>
      </div>

      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="font-mono text-[10px] text-white/50 uppercase tracking-wider block mb-2">Agent</label>
          <input
            data-testid="login-agent-input"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            placeholder="ACCES-01"
            autoFocus
            autoCapitalize="characters"
            className="w-full px-5 py-4 rounded-xl bg-white/5 border border-white/15 text-white font-mono text-lg uppercase tracking-wider focus:border-[#f7931a]/60 focus:outline-none"
          />
        </div>
        <div>
          <label className="font-mono text-[10px] text-white/50 uppercase tracking-wider block mb-2">PIN</label>
          <div data-testid="login-pin-display" className="flex justify-center gap-2 mb-3 py-3 rounded-xl bg-white/5 border border-white/15">
            {Array.from({ length: 8 }).map((_, i) => (
              <span
                key={i}
                className={`w-3 h-3 rounded-full transition ${
                  i < pin.length ? 'bg-[#f7931a]' : 'bg-white/10'
                }`}
              />
            ))}
          </div>
          <div className="grid grid-cols-3 gap-2">
            {['1','2','3','4','5','6','7','8','9'].map((d) => (
              <button
                type="button"
                key={d}
                data-testid={`pin-${d}`}
                onClick={() => padDigit(d)}
                className="py-5 rounded-xl bg-white/5 border border-white/10 text-white text-2xl font-mono active:bg-white/10"
              >{d}</button>
            ))}
            <button
              type="button"
              data-testid="pin-clear"
              onClick={() => setPin('')}
              className="py-5 rounded-xl bg-white/5 border border-white/10 text-white/60 text-sm font-mono active:bg-white/10"
            >C</button>
            <button
              type="button"
              data-testid="pin-0"
              onClick={() => padDigit('0')}
              className="py-5 rounded-xl bg-white/5 border border-white/10 text-white text-2xl font-mono active:bg-white/10"
            >0</button>
            <button
              type="button"
              data-testid="pin-back"
              onClick={() => setPin(pin.slice(0, -1))}
              className="py-5 rounded-xl bg-white/5 border border-white/10 text-white/60 text-sm font-mono active:bg-white/10"
            >←</button>
          </div>
        </div>
        {err && <div data-testid="login-error" className="font-mono text-xs text-red-400 text-center">{err}</div>}
        <button
          data-testid="login-submit"
          type="submit"
          disabled={busy || !agentId || pin.length < 4}
          className="w-full py-4 rounded-xl bg-[#f7931a] text-black font-mono text-sm uppercase tracking-widest font-bold disabled:opacity-40"
        >
          {busy ? 'Connexion…' : 'Connexion'}
        </button>
      </form>
    </div>
  );
}
