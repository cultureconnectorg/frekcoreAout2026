/**
 * FREK — Pointeuse /scanner (theme clair Certify)
 *
 * 3 modes de saisie supportés pour couvrir tout l'écosystème scanner mondial :
 *  - HID/clavier : pistolets USB/Bluetooth, lecteurs RFID, lecteurs USB-NFC (par défaut)
 *  - Caméra : téléphone QR/DataMatrix (html5-qrcode)
 *  - Web NFC : Android Chrome (NDEFReader natif)
 *
 * Aucun backend touché. Queue locale `frek_offline_queue`.
 * Le replay serveur est délégué au Poste Staff authentifié (/poste).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const QUEUE_KEY = 'frek_offline_queue';

function readQueue() {
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr : [];
  } catch { return []; }
}
function writeQueue(q) {
  try { localStorage.setItem(QUEUE_KEY, JSON.stringify(q)); } catch { /* noop */ }
}
function nowIso() { return new Date().toISOString(); }
function newUuid() {
  // RFC4122 v4 light
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
function fmtTime(iso) {
  try { return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }); }
  catch { return iso; }
}

function BackgroundDecor() {
  return (
    <>
      <div aria-hidden className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl opacity-30" />
      <div aria-hidden className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl opacity-25" />
    </>
  );
}

export default function Scanner() {
  const inputRef = useRef(null);
  const cameraDivRef = useRef(null);
  const html5QrRef = useRef(null);
  const nfcReaderRef = useRef(null);

  const [mode, setMode] = useState('hid'); // 'hid' | 'camera' | 'nfc'
  const [value, setValue] = useState('');
  const [online, setOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [queue, setQueue] = useState(() => readQueue());
  const [sessionCount, setSessionCount] = useState(0);
  const [lastConfirm, setLastConfirm] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [platformTotal, setPlatformTotal] = useState(null);
  const [nfcSupported, setNfcSupported] = useState(false);

  useEffect(() => {
    setNfcSupported(typeof window !== 'undefined' && 'NDEFReader' in window);
  }, []);

  useEffect(() => {
    const onOn = () => setOnline(true);
    const onOff = () => setOnline(false);
    window.addEventListener('online', onOn);
    window.addEventListener('offline', onOff);
    return () => {
      window.removeEventListener('online', onOn);
      window.removeEventListener('offline', onOff);
    };
  }, []);

  // Auto-focus HID input
  useEffect(() => {
    if (mode !== 'hid') return;
    const tick = () => {
      if (document.activeElement !== inputRef.current && inputRef.current) inputRef.current.focus();
    };
    tick();
    const id = setInterval(tick, 1500);
    return () => clearInterval(id);
  }, [mode]);

  const fetchPlatform = useCallback(async () => {
    try {
      const r = await fetch(`${API_URL}/api/core/ecosystem/pulse`);
      if (r.ok) {
        const j = await r.json();
        setPlatformTotal(j.total_events ?? null);
      }
    } catch { /* offline */ }
  }, []);

  useEffect(() => {
    fetchPlatform();
    const id = setInterval(fetchPlatform, 30_000);
    return () => clearInterval(id);
  }, [fetchPlatform]);

  const recordPresence = useCallback((entry) => {
    setQueue((prev) => {
      const next = [...prev, entry];
      writeQueue(next);
      return next;
    });
    setSessionCount((c) => c + 1);
    setLastConfirm(entry);
  }, []);

  const submit = useCallback(async (raw, sourceMode = mode) => {
    const id = (raw ?? value).trim();
    if (!id || busy) return;
    setBusy(true); setError(null);

    let frek_id = null;
    let badge_id = null;
    let detail = null;

    if (/^FREK[-_]/i.test(id)) {
      frek_id = id;
    } else {
      badge_id = id;
      try {
        const r = await fetch(`${API_URL}/api/badges/${encodeURIComponent(id)}`);
        if (r.ok) {
          const b = await r.json();
          frek_id = b.frek_id || null;
          detail = b.type_name || b.type_badge || null;
        } else {
          frek_id = id;
        }
      } catch {
        frek_id = id;
      }
    }

    const entry = {
      client_uuid: newUuid(),
      code: badge_id || frek_id || id, // valeur originale pour replay staff
      frek_id: frek_id || id,
      badge_id,
      detail,
      timestamp: nowIso(),
      origin: 'scanner',
      input_mode: sourceMode,
      online,
    };
    recordPresence(entry);
    setValue('');
    setBusy(false);
  }, [value, busy, online, mode, recordPresence]);

  // ===== Caméra (html5-qrcode) =====
  const startCamera = useCallback(async () => {
    setError(null);
    try {
      const lib = await import('html5-qrcode');
      const { Html5Qrcode } = lib;
      if (!cameraDivRef.current) return;
      // Cleanup previous instance
      if (html5QrRef.current) {
        try { await html5QrRef.current.stop(); } catch { /* noop */ }
        try { await html5QrRef.current.clear(); } catch { /* noop */ }
        html5QrRef.current = null;
      }
      const qr = new Html5Qrcode(cameraDivRef.current.id);
      html5QrRef.current = qr;
      await qr.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 240, height: 240 } },
        (decodedText) => { submit(decodedText, 'camera'); },
        () => { /* silent decode error */ },
      );
    } catch (e) {
      setError("Caméra indisponible — vérifie l'autorisation navigateur.");
      setMode('hid');
    }
  }, [submit]);

  const stopCamera = useCallback(async () => {
    if (html5QrRef.current) {
      try { await html5QrRef.current.stop(); } catch { /* noop */ }
      try { await html5QrRef.current.clear(); } catch { /* noop */ }
      html5QrRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (mode === 'camera') startCamera();
    else stopCamera();
    return () => { stopCamera(); };
  }, [mode, startCamera, stopCamera]);

  // ===== Web NFC =====
  const startNfc = useCallback(async () => {
    setError(null);
    if (!('NDEFReader' in window)) {
      setError('Web NFC non supporté sur ce navigateur (Chrome Android requis).');
      setMode('hid'); return;
    }
    try {
      // eslint-disable-next-line no-undef
      const reader = new NDEFReader();
      nfcReaderRef.current = reader;
      await reader.scan();
      reader.onreading = (event) => {
        let payload = event.serialNumber || '';
        try {
          for (const rec of event.message?.records || []) {
            const td = new TextDecoder();
            const decoded = td.decode(rec.data);
            if (decoded && decoded.length > 0) { payload = decoded; break; }
          }
        } catch { /* noop */ }
        if (payload) submit(payload, 'nfc');
      };
    } catch (e) {
      setError('NFC indisponible — permission refusée ou périphérique absent.');
      setMode('hid');
    }
  }, [submit]);

  useEffect(() => {
    if (mode === 'nfc') startNfc();
    // Pas de stop API NFC fiable cross-browser ; on laisse la page se décharger.
  }, [mode, startNfc]);

  const clearQueue = () => {
    if (!confirm('Vider la file locale ?')) return;
    setQueue([]); writeQueue([]);
  };

  const last10 = useMemo(() => [...queue].slice(-10).reverse(), [queue]);

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 relative overflow-hidden flex flex-col">
      <BackgroundDecor />

      <header className="relative z-10 max-w-5xl w-full mx-auto px-4 sm:px-6 pt-6">
        <div className="bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/60 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between gap-3">
          <Link to="/accueil" data-testid="scanner-home-link" className="flex items-center gap-2 sm:gap-3">
            <span className="font-display text-xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">FREK</span>
          </Link>
          <div className="flex items-center gap-3">
            <span data-testid="scanner-network-status" className={`inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest ${online ? 'text-emerald-600' : 'text-amber-600'}`}>
              <span className={`h-2 w-2 rounded-full ${online ? 'bg-emerald-500' : 'bg-amber-500'}`} />
              {online ? 'En ligne' : 'Hors ligne'}
            </span>
            <span data-testid="scanner-queue-count" className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">file : {queue.length}</span>
          </div>
        </div>
      </header>

      <main className="relative z-10 flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-10">
        {/* Mode selector */}
        <div data-testid="scanner-mode-selector" className="mb-4 inline-flex rounded-xl bg-white/70 backdrop-blur-sm border border-white/60 p-1 shadow-sm">
          {[
            { id: 'hid', label: 'HID / Clavier' },
            { id: 'camera', label: 'Caméra' },
            { id: 'nfc', label: 'NFC', disabled: !nfcSupported },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              disabled={m.disabled}
              data-testid={`scanner-mode-${m.id}`}
              className={`px-3 py-1.5 rounded-lg font-mono text-[10px] sm:text-[11px] uppercase tracking-wider transition-all ${
                mode === m.id
                  ? 'bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white shadow'
                  : 'text-slate-600 hover:text-[#0ea5e9] disabled:opacity-40 disabled:cursor-not-allowed'
              }`}
            >
              {m.label}{m.disabled ? ' (indispo)' : ''}
            </button>
          ))}
        </div>

        {/* Champ principal */}
        <section data-testid="scanner-input-zone" className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl shadow-xl shadow-slate-200/40 p-6 sm:p-8">
          <div className="font-mono text-[10px] sm:text-xs text-[#0ea5e9] uppercase tracking-widest mb-4">
            Pointeuse FREK-P · CC2026
          </div>

          {mode === 'hid' && (
            <form onSubmit={(e) => { e.preventDefault(); submit(); }} className="space-y-4">
              <input
                ref={inputRef}
                data-testid="scanner-input"
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="Scanner ou saisir badge_id / FREK-ID"
                autoComplete="off"
                spellCheck={false}
                autoFocus
                className="w-full bg-transparent border-b-2 border-[#2cc4f5]/30 focus:border-[#2cc4f5] outline-none font-mono text-2xl sm:text-4xl text-[#0ea5e9] placeholder:text-slate-300 py-3 tracking-wider"
              />
              <div className="flex flex-wrap items-center justify-between gap-3">
                <button
                  type="submit"
                  disabled={!value.trim() || busy}
                  data-testid="scanner-submit-btn"
                  className="px-6 py-3 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] disabled:from-slate-300 disabled:to-slate-300 disabled:cursor-not-allowed text-white font-mono text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-[#2cc4f5]/30 hover:shadow-xl transition-all font-semibold"
                >
                  {busy ? 'Enregistrement…' : 'Enregistrer présence'}
                </button>
                <button
                  type="button"
                  onClick={clearQueue}
                  disabled={queue.length === 0}
                  data-testid="scanner-clear-queue-btn"
                  className="font-mono text-[10px] text-slate-400 hover:text-red-500 disabled:opacity-30 disabled:cursor-not-allowed uppercase tracking-widest transition-colors"
                >
                  Vider la file
                </button>
              </div>
            </form>
          )}

          {mode === 'camera' && (
            <div className="space-y-4">
              <div
                id="frek-camera-view"
                ref={cameraDivRef}
                data-testid="scanner-camera-view"
                className="w-full aspect-video bg-slate-900 rounded-xl overflow-hidden border border-slate-200"
              />
              <p className="font-mono text-[11px] text-slate-500">
                Positionnez le QR/DataMatrix dans le cadre. La lecture est automatique.
              </p>
            </div>
          )}

          {mode === 'nfc' && (
            <div data-testid="scanner-nfc-view" className="py-10 text-center">
              <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-[#2cc4f5]/20 to-[#0ea5e9]/20 border-2 border-[#2cc4f5]/40 mb-4 animate-pulse">
                <svg className="w-10 h-10 text-[#0ea5e9]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.288 15.038a5.25 5.25 0 0 1 7.424 0M5.106 11.856a9.75 9.75 0 0 1 13.788 0M1.924 8.674a14.25 14.25 0 0 1 20.152 0M12 20.25h.008v.008H12v-.008Z" />
                </svg>
              </div>
              <div className="font-mono text-sm text-slate-600">Approchez un badge NFC du téléphone</div>
              <div className="font-mono text-[11px] text-slate-400 mt-2">Chrome Android · permission demandée à la première lecture</div>
            </div>
          )}
        </section>

        {/* Dernière confirmation */}
        {lastConfirm && (
          <section data-testid="scanner-last-confirm" className="mt-6 bg-emerald-50/80 backdrop-blur-sm border border-emerald-200 rounded-xl p-4 sm:p-5 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="h-7 w-7 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center shrink-0">
                <svg className="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-mono text-[10px] text-emerald-700 uppercase tracking-widest">Présence enregistrée</div>
                <div className="font-mono text-sm text-slate-800 break-all mt-0.5" data-testid="scanner-last-frek-id">{lastConfirm.frek_id}</div>
                <div className="font-mono text-[11px] text-slate-500 mt-1">
                  {fmtTime(lastConfirm.timestamp)}{lastConfirm.detail ? ` · ${lastConfirm.detail}` : ''} · mode {lastConfirm.input_mode}{lastConfirm.online ? '' : ' · queue locale'}
                </div>
              </div>
            </div>
          </section>
        )}

        {error && (
          <div className="mt-4 rounded-lg p-3 bg-red-50 border border-red-200 font-mono text-[11px] text-red-600" data-testid="scanner-error">{error}</div>
        )}

        {/* Compteurs */}
        <section data-testid="scanner-counters" className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-5 shadow-sm">
            <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Session en cours</div>
            <div data-testid="scanner-session-count" className="font-display text-4xl sm:text-5xl text-slate-800 tabular-nums mt-1">{sessionCount}</div>
            <div className="font-mono text-[10px] text-slate-400 mt-1">scans depuis l'ouverture de cette page</div>
          </div>
          <div className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-5 shadow-sm">
            <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Plateforme (CVLN)</div>
            <div data-testid="scanner-platform-total" className="font-display text-4xl sm:text-5xl text-slate-800 tabular-nums mt-1">
              {platformTotal !== null ? platformTotal.toLocaleString('fr-FR') : '—'}
            </div>
            <div className="font-mono text-[10px] text-slate-400 mt-1">total présences plateforme · indicatif</div>
          </div>
        </section>

        {last10.length > 0 && (
          <section data-testid="scanner-queue-preview" className="mt-8">
            <div className="flex items-center justify-between mb-3">
              <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">File locale — 10 derniers</div>
              <Link to="/poste" data-testid="scanner-link-poste" className="font-mono text-[10px] text-slate-500 hover:text-[#0ea5e9] uppercase tracking-widest">
                Rejouer via /poste →
              </Link>
            </div>
            <div className="space-y-1.5">
              {last10.map((q, i) => (
                <div key={`${q.timestamp}-${i}`} className="flex items-center justify-between gap-3 bg-white/70 backdrop-blur-sm border border-white/60 rounded-md px-3 py-2 shadow-sm">
                  <span className="font-mono text-xs text-slate-700 truncate">{q.frek_id}</span>
                  <span className="font-mono text-[10px] text-slate-400 shrink-0">
                    {fmtTime(q.timestamp)} · {q.input_mode}{q.online ? '' : ' · offline'}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      <footer className="relative z-10 border-t border-slate-200/70">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-slate-400 uppercase tracking-widest">
          <span>Pointeuse · données locales d'abord</span>
          <span>file persistée dans <code className="text-[#0ea5e9]">frek_offline_queue</code></span>
        </div>
      </footer>
    </div>
  );
}
