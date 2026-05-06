/** Mode Accès — sélection zone, scan QR badge, validation */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import QrScanner from './QrScanner';
import { api, tryOrQueue } from './lib';

export default function ScanAccess({ staff, online }) {
  const navigate = useNavigate();
  const [zones, setZones] = useState([]);
  const [allowedForAgent, setAllowedForAgent] = useState([]);
  const [zone, setZone] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.zones().then((r) => {
      setZones(Object.keys(r.zones));
      setAllowedForAgent(r.allowed_for_agent || Object.keys(r.zones));
    }).catch(() => {});
  }, []);

  const handleDetected = async (code) => {
    setScanning(false);
    setError(null);
    if (!zone) { setError('Choisis une zone'); return; }
    const res = await tryOrQueue('access', { code, zone }, () => api.access({ code, zone }));
    if (res.ok) setResult({ kind: 'success', data: res.result });
    else if (res.queued) setResult({ kind: 'queued', message: 'Action mise en file (offline)' });
    else setResult({ kind: 'error', message: res.error || 'Erreur' });
  };

  return (
    <div className="space-y-5" data-testid="scan-access">
      <button
        onClick={() => navigate('/scan')}
        data-testid="back-btn"
        className="font-mono text-[11px] text-white/50 uppercase tracking-wider"
      >← Menu</button>
      <h2 className="font-mono text-xl uppercase tracking-widest text-white">Mode Accès</h2>

      <div>
        <div className="font-mono text-[10px] text-white/40 uppercase tracking-wider mb-2">Zone à contrôler</div>
        <div className="grid grid-cols-3 gap-2">
          {zones.map((z) => {
            const allowed = allowedForAgent.length === 0 || allowedForAgent.includes(z);
            return (
              <button
                key={z}
                data-testid={`zone-${z}`}
                disabled={!allowed}
                onClick={() => { setZone(z); setResult(null); }}
                className={`py-3 px-2 rounded-xl border font-mono text-[11px] uppercase tracking-wider transition ${
                  zone === z
                    ? 'bg-[#2cc4f5]/20 border-[#2cc4f5] text-[#2cc4f5]'
                    : allowed
                      ? 'bg-white/5 border-white/15 text-white/80 active:bg-white/10'
                      : 'bg-white/[0.02] border-white/5 text-white/30'
                }`}
              >{z}</button>
            );
          })}
        </div>
      </div>

      {zone && (
        <button
          data-testid="open-scanner-btn"
          onClick={() => { setResult(null); setScanning(true); }}
          className="w-full py-5 rounded-2xl bg-[#2cc4f5] text-black font-mono text-base uppercase tracking-widest font-bold"
        >
          {online ? '📷 Scanner badge' : '📷 Scanner (offline OK)'}
        </button>
      )}

      {error && <div className="font-mono text-xs text-red-400 text-center">{error}</div>}

      {result?.kind === 'success' && (
        <div data-testid="scan-result-success" className="rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-5">
          <div className="text-3xl text-center mb-2">✓</div>
          <div className="text-center font-mono text-lg text-emerald-300 uppercase tracking-widest mb-3">
            {result.data.access}
          </div>
          <div className="space-y-1 text-center">
            <div className="font-mono text-base text-white">{result.data.badge?.prenom} {result.data.badge?.nom}</div>
            <div className="font-mono text-[11px] text-white/60">{result.data.badge?.type_name}</div>
            <div className="font-mono text-[10px] text-white/40">{result.data.badge?.badge_id}</div>
            {result.data.badge?.jetons_solde > 0 && (
              <div className="mt-3 inline-block px-3 py-1 rounded-full bg-[#f7931a]/15 border border-[#f7931a]/30 text-[#f7931a] font-mono text-[11px]">
                Solde : {result.data.badge.jetons_solde} J
              </div>
            )}
          </div>
        </div>
      )}
      {result?.kind === 'queued' && (
        <div data-testid="scan-result-queued" className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-5 text-center">
          <div className="text-2xl mb-1">⏳</div>
          <div className="font-mono text-sm text-amber-300">{result.message}</div>
        </div>
      )}
      {result?.kind === 'error' && (
        <div data-testid="scan-result-error" className="rounded-2xl border border-red-500/40 bg-red-500/10 p-5 text-center">
          <div className="text-2xl mb-1">✕</div>
          <div className="font-mono text-sm text-red-300">{result.message}</div>
        </div>
      )}

      {scanning && <QrScanner label={`Accès ${zone}`} onDetected={handleDetected} onCancel={() => setScanning(false)} />}
    </div>
  );
}
