/** Mode Émission walk-in — création FREK-ID + badge sur le terrain */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { api, tryOrQueue } from './lib';

const TYPES = [
  { code: 'BNV', label: 'Bénévole' },
  { code: 'INT', label: 'Intervenant' },
  { code: 'PRS', label: 'Presse' },
  { code: 'EXP-B', label: 'Exposant Basic' },
  { code: 'EXP-S', label: 'Exposant Standard' },
  { code: 'EXP-G', label: 'Exposant Gold' },
  { code: 'OFF', label: 'Officiel' },
  { code: 'VIP', label: 'VIP' },
  { code: 'STF', label: 'Staff' },
  { code: 'SPO', label: 'Sponsor' },
];

export default function ScanEmit() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', prenom: '', nom: '', type_badge: 'BNV', organisation: '' });
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const update = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.prenom || !form.nom) return;
    setBusy(true);
    setResult(null);
    const payload = { ...form, event: 'CC2026' };
    const res = await tryOrQueue('emit', payload, () => api.emit(payload));
    setBusy(false);
    if (res.ok) {
      setResult({ kind: 'success', data: res.result });
      setForm({ email: '', prenom: '', nom: '', type_badge: 'BNV', organisation: '' });
    } else if (res.queued) {
      setResult({ kind: 'queued', message: 'Mis en file (offline) — sera émis au retour réseau' });
      setForm({ email: '', prenom: '', nom: '', type_badge: 'BNV', organisation: '' });
    } else {
      setResult({ kind: 'error', message: res.error || 'Erreur' });
    }
  };

  return (
    <div className="space-y-5" data-testid="scan-emit">
      <button onClick={() => navigate('/scan')} data-testid="back-btn" className="font-mono text-[11px] text-white/50 uppercase tracking-wider">← Menu</button>
      <h2 className="font-mono text-xl uppercase tracking-widest text-white">Mode Émission</h2>
      <p className="font-mono text-[11px] text-white/50">Walk-in : création FREK-ID + badge à la volée pour participants non pré-inscrits.</p>

      <form onSubmit={submit} className="space-y-3">
        <div>
          <label className="font-mono text-[10px] text-white/40 uppercase tracking-wider block mb-2">Email</label>
          <input
            data-testid="emit-email"
            type="email"
            required
            value={form.email}
            onChange={update('email')}
            className="w-full px-4 py-4 rounded-xl bg-white/5 border border-white/15 text-white font-mono text-base focus:border-[#10B981]/60 focus:outline-none"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="font-mono text-[10px] text-white/40 uppercase tracking-wider block mb-2">Prénom</label>
            <input
              data-testid="emit-prenom"
              required
              value={form.prenom}
              onChange={update('prenom')}
              className="w-full px-4 py-4 rounded-xl bg-white/5 border border-white/15 text-white font-mono text-base focus:border-[#10B981]/60 focus:outline-none"
            />
          </div>
          <div>
            <label className="font-mono text-[10px] text-white/40 uppercase tracking-wider block mb-2">Nom</label>
            <input
              data-testid="emit-nom"
              required
              value={form.nom}
              onChange={update('nom')}
              className="w-full px-4 py-4 rounded-xl bg-white/5 border border-white/15 text-white font-mono text-base focus:border-[#10B981]/60 focus:outline-none"
            />
          </div>
        </div>
        <div>
          <label className="font-mono text-[10px] text-white/40 uppercase tracking-wider block mb-2">Type badge</label>
          <select
            data-testid="emit-type"
            value={form.type_badge}
            onChange={update('type_badge')}
            className="w-full px-4 py-4 rounded-xl bg-white/5 border border-white/15 text-white font-mono text-base focus:border-[#10B981]/60 focus:outline-none"
          >
            {TYPES.map((t) => (
              <option key={t.code} value={t.code}>{t.code} · {t.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="font-mono text-[10px] text-white/40 uppercase tracking-wider block mb-2">Organisation (optionnel)</label>
          <input
            data-testid="emit-organisation"
            value={form.organisation}
            onChange={update('organisation')}
            className="w-full px-4 py-4 rounded-xl bg-white/5 border border-white/15 text-white font-mono text-base focus:border-[#10B981]/60 focus:outline-none"
          />
        </div>

        <button
          data-testid="emit-submit"
          type="submit"
          disabled={busy || !form.email || !form.prenom || !form.nom}
          className="w-full py-5 rounded-2xl bg-[#10B981] text-black font-mono text-base uppercase tracking-widest font-bold disabled:opacity-40"
        >{busy ? 'Création…' : 'Émettre FREK-ID'}</button>
      </form>

      {result?.kind === 'success' && (
        <div data-testid="emit-result-success" className="rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-5 text-center">
          <div className="text-3xl mb-2">✓</div>
          <div className="font-mono text-lg text-emerald-300 uppercase tracking-widest mb-3">
            {result.data.created ? 'Badge créé' : 'Badge existant'}
          </div>
          <div className="font-mono text-base text-white mb-1">{result.data.badge?.badge_id}</div>
          <div className="font-mono text-[11px] text-white/60">{result.data.badge?.frek_id}</div>
          {result.data.qr_token && (
            <div className="mt-4 inline-block p-3 bg-white rounded-xl">
              <QRCodeSVG value={`${window.location.origin}/verify/${result.data.badge.frek_id}`} size={130} level="M" fgColor="#0a1520" />
            </div>
          )}
        </div>
      )}
      {result?.kind === 'queued' && (
        <div data-testid="emit-result-queued" className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-5 text-center font-mono text-sm text-amber-300">⏳ {result.message}</div>
      )}
      {result?.kind === 'error' && (
        <div data-testid="emit-result-error" className="rounded-2xl border border-red-500/40 bg-red-500/10 p-5 text-center font-mono text-sm text-red-300">✕ {result.message}</div>
      )}
    </div>
  );
}
