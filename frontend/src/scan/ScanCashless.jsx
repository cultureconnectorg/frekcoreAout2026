/** Mode Cashless — sélection marchand + scan badge + saisie montant + débit jetons */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import QrScanner from './QrScanner';
import { api, tryOrQueue } from './lib';

export default function ScanCashless({ online }) {
  const navigate = useNavigate();
  const [marchands, setMarchands] = useState([]);
  const [marchandId, setMarchandId] = useState('');
  const [montant, setMontant] = useState('');
  const [code, setCode] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [badgeInfo, setBadgeInfo] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.marchands().then((r) => setMarchands(r.marchands || [])).catch(() => {});
  }, []);

  const handleDetected = async (c) => {
    setScanning(false);
    setCode(c);
    setBadgeInfo(null);
    try {
      const b = await api.badge(c);
      setBadgeInfo(b);
    } catch (e) {
      setResult({ kind: 'error', message: e.message });
    }
  };

  const handlePay = async () => {
    if (!code || !marchandId || !montant) return;
    const m = parseInt(montant, 10);
    if (!m || m <= 0) return;
    setBusy(true);
    setResult(null);
    const payload = { code, marchand_id: marchandId, montant_jetons: m };
    const res = await tryOrQueue('cashless', payload, () => api.cashless(payload));
    setBusy(false);
    if (res.ok) {
      setResult({ kind: 'success', data: res.result });
      setMontant(''); setCode(null); setBadgeInfo(null);
    } else if (res.queued) {
      setResult({ kind: 'queued', message: 'Mis en file (offline) — sera rejoué' });
      setMontant(''); setCode(null); setBadgeInfo(null);
    } else {
      setResult({ kind: 'error', message: res.error || 'Erreur' });
    }
  };

  const incomplete = !code || !marchandId || !montant || parseInt(montant, 10) <= 0;

  return (
    <div className="space-y-5" data-testid="scan-cashless">
      <button onClick={() => navigate('/scan')} data-testid="back-btn" className="font-mono text-[11px] text-white/50 uppercase tracking-wider">← Menu</button>
      <h2 className="font-mono text-xl uppercase tracking-widest text-white">Mode Cashless</h2>

      <div>
        <div className="font-mono text-[10px] text-white/40 uppercase tracking-wider mb-2">Marchand</div>
        <select
          data-testid="marchand-select"
          value={marchandId}
          onChange={(e) => setMarchandId(e.target.value)}
          className="w-full px-4 py-4 rounded-xl bg-white/5 border border-white/15 text-white font-mono text-base focus:border-[#f7931a]/60 focus:outline-none"
        >
          <option value="">— Choisir —</option>
          {marchands.map((m) => (
            <option key={m.marchand_id} value={m.marchand_id}>{m.nom} {m.stand ? `· ${m.stand}` : ''}</option>
          ))}
        </select>
      </div>

      <div>
        <div className="font-mono text-[10px] text-white/40 uppercase tracking-wider mb-2">Badge</div>
        {!code ? (
          <button
            data-testid="open-scanner-btn"
            onClick={() => setScanning(true)}
            className="w-full py-5 rounded-2xl bg-[#f7931a] text-black font-mono text-base uppercase tracking-widest font-bold"
          >📷 Scanner badge</button>
        ) : (
          <div data-testid="badge-info" className="rounded-2xl border border-white/15 bg-white/5 p-4">
            {badgeInfo ? (
              <div className="space-y-1">
                <div className="font-mono text-base text-white">{badgeInfo.prenom} {badgeInfo.nom}</div>
                <div className="font-mono text-[11px] text-white/60">{badgeInfo.type_name}</div>
                <div className="flex items-center gap-2 mt-2">
                  <span className="font-mono text-[10px] text-white/40 uppercase tracking-wider">Solde</span>
                  <span data-testid="badge-solde" className="font-mono text-xl text-[#f7931a] font-bold">{badgeInfo.jetons_solde} J</span>
                </div>
              </div>
            ) : (
              <div className="font-mono text-xs text-white/50">Code: {code}</div>
            )}
            <button
              onClick={() => { setCode(null); setBadgeInfo(null); }}
              className="mt-3 font-mono text-[10px] text-white/50 uppercase tracking-wider"
            >Changer de badge</button>
          </div>
        )}
      </div>

      <div>
        <div className="font-mono text-[10px] text-white/40 uppercase tracking-wider mb-2">Montant (jetons)</div>
        <input
          data-testid="montant-input"
          type="number"
          inputMode="numeric"
          min="1"
          value={montant}
          onChange={(e) => setMontant(e.target.value)}
          placeholder="0"
          className="w-full px-5 py-4 rounded-xl bg-white/5 border border-white/15 text-white font-mono text-2xl text-center focus:border-[#f7931a]/60 focus:outline-none"
        />
        <div className="grid grid-cols-4 gap-2 mt-2">
          {[1, 2, 5, 10].map((q) => (
            <button
              key={q}
              data-testid={`quick-${q}`}
              onClick={() => setMontant(String(q))}
              className="py-3 rounded-xl bg-white/5 border border-white/10 text-white font-mono text-sm active:bg-white/10"
            >{q} J</button>
          ))}
        </div>
        {montant && badgeInfo && parseInt(montant, 10) > badgeInfo.jetons_solde && (
          <div className="mt-2 font-mono text-[11px] text-red-400">⚠ Solde insuffisant</div>
        )}
      </div>

      <button
        data-testid="pay-btn"
        onClick={handlePay}
        disabled={incomplete || busy}
        className="w-full py-5 rounded-2xl bg-[#f7931a] text-black font-mono text-base uppercase tracking-widest font-bold disabled:opacity-40"
      >
        {busy ? 'Traitement…' : `Débiter ${montant || '—'} J`}
      </button>

      {result?.kind === 'success' && (
        <div data-testid="cashless-result-success" className="rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-5 text-center">
          <div className="text-3xl mb-2">✓</div>
          <div className="font-mono text-lg text-emerald-300 uppercase tracking-widest mb-2">Paiement OK</div>
          <div className="font-mono text-sm text-white">−{result.data.transaction?.montant_jetons} J → {result.data.marchand}</div>
          <div className="font-mono text-[11px] text-white/60 mt-1">Solde restant : {result.data.new_solde} J</div>
        </div>
      )}
      {result?.kind === 'queued' && (
        <div data-testid="cashless-result-queued" className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-5 text-center font-mono text-sm text-amber-300">⏳ {result.message}</div>
      )}
      {result?.kind === 'error' && (
        <div data-testid="cashless-result-error" className="rounded-2xl border border-red-500/40 bg-red-500/10 p-5 text-center font-mono text-sm text-red-300">✕ {result.message}</div>
      )}

      {scanning && <QrScanner label="Cashless — scan badge" onDetected={handleDetected} onCancel={() => setScanning(false)} />}
    </div>
  );
}
