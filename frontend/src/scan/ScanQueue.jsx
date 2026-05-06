/** Queue offline — visualisation, sync manuel, log récent */
import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { queueAll, queueClear, flushQueue, logRecent } from './lib';

const KIND_LABEL = { access: 'Accès', cashless: 'Cashless', emit: 'Émission' };

export default function ScanQueue({ online }) {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [logs, setLogs] = useState([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  const refresh = useCallback(async () => {
    setItems(await queueAll());
    setLogs(await logRecent(30));
  }, []);

  useEffect(() => {
    refresh();
    const i = setInterval(refresh, 4000);
    return () => clearInterval(i);
  }, [refresh]);

  const handleFlush = async () => {
    if (!online) { setMsg({ kind: 'error', text: 'Hors ligne — impossible de synchroniser' }); return; }
    setBusy(true); setMsg(null);
    try {
      const res = await flushQueue();
      setMsg({ kind: 'ok', text: `Sync : ${res.success}/${res.total} OK` });
    } catch (e) {
      setMsg({ kind: 'error', text: e.message });
    } finally {
      setBusy(false);
      await refresh();
    }
  };

  const handleClear = async () => {
    if (!confirm('Vider la file ? Les actions non synchronisées seront perdues.')) return;
    await queueClear();
    await refresh();
  };

  return (
    <div className="space-y-5" data-testid="scan-queue">
      <button onClick={() => navigate('/scan')} data-testid="back-btn" className="font-mono text-[11px] text-white/50 uppercase tracking-wider">← Menu</button>
      <h2 className="font-mono text-xl uppercase tracking-widest text-white">File hors-ligne</h2>

      <div className="flex gap-2">
        <button
          data-testid="flush-btn"
          onClick={handleFlush}
          disabled={!items.length || !online || busy}
          className="flex-1 py-4 rounded-xl bg-[#f7931a] text-black font-mono text-sm uppercase tracking-wider font-bold disabled:opacity-40"
        >{busy ? 'Sync…' : `Synchroniser (${items.length})`}</button>
        <button
          data-testid="clear-btn"
          onClick={handleClear}
          disabled={!items.length}
          className="px-4 py-4 rounded-xl bg-white/5 border border-white/15 text-white/70 font-mono text-sm uppercase tracking-wider disabled:opacity-40"
        >Vider</button>
      </div>

      {msg && (
        <div data-testid="queue-msg" className={`rounded-xl p-3 font-mono text-xs text-center ${
          msg.kind === 'ok' ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300' : 'bg-red-500/10 border border-red-500/30 text-red-300'
        }`}>{msg.text}</div>
      )}

      <div data-testid="queue-list" className="space-y-2">
        {items.length === 0 ? (
          <div className="font-mono text-xs text-white/40 text-center py-8">File vide — toutes les actions sont synchronisées.</div>
        ) : (
          items.map((it) => (
            <div key={it.client_uuid} data-testid={`queue-item-${it.kind}`} className="rounded-xl border border-white/15 bg-white/5 p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-xs text-[#f7931a] uppercase tracking-wider">{KIND_LABEL[it.kind] || it.kind}</span>
                <span className="font-mono text-[10px] text-white/40">{it.queued_at?.slice(11, 19)}</span>
              </div>
              <div className="font-mono text-[11px] text-white/60 break-all">
                {it.kind === 'access' && `${it.payload?.zone} · ${it.payload?.code}`}
                {it.kind === 'cashless' && `${it.payload?.montant_jetons} J · ${it.payload?.marchand_id}`}
                {it.kind === 'emit' && `${it.payload?.prenom} ${it.payload?.nom} · ${it.payload?.type_badge}`}
              </div>
            </div>
          ))
        )}
      </div>

      <div>
        <div className="font-mono text-[10px] text-white/40 uppercase tracking-wider mb-2">Journal récent</div>
        <div data-testid="queue-log" className="space-y-1 max-h-72 overflow-auto">
          {logs.map((l) => (
            <div key={l.id} className="rounded-lg bg-white/[0.03] border border-white/5 px-3 py-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] text-white/60 uppercase tracking-wider">
                  {KIND_LABEL[l.kind] || l.kind} · <span className={
                    l.status === 'success' ? 'text-emerald-400'
                    : l.status?.startsWith('queued') ? 'text-amber-400'
                    : l.status === 'flushed' ? 'text-[#f7931a]'
                    : 'text-red-400'
                  }>{l.status}</span>
                </span>
                <span className="font-mono text-[9px] text-white/30">{l.ts?.slice(11, 19)}</span>
              </div>
              {l.summary && <div className="font-mono text-[10px] text-white/50 mt-0.5">{l.summary}</div>}
              {l.error && <div className="font-mono text-[10px] text-red-400/80 mt-0.5">{l.error}</div>}
            </div>
          ))}
          {logs.length === 0 && <div className="font-mono text-[10px] text-white/30 text-center py-4">Aucune activité</div>}
        </div>
      </div>
    </div>
  );
}
