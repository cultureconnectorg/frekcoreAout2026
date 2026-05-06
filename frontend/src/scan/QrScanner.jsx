/**
 * QR Scanner wrapper using html5-qrcode.
 * Plein écran, gros boutons, lisible plein soleil.
 */
import { useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';

export default function QrScanner({ onDetected, onCancel, label = 'Scanner un QR' }) {
  const containerId = 'frek-qr-reader';
  const ref = useRef(null);
  const [error, setError] = useState(null);
  const [manual, setManual] = useState('');
  const [showManual, setShowManual] = useState(false);

  useEffect(() => {
    let scanner;
    let mounted = true;
    (async () => {
      try {
        scanner = new Html5Qrcode(containerId, { verbose: false });
        ref.current = scanner;
        await scanner.start(
          { facingMode: 'environment' },
          { fps: 10, qrbox: { width: 240, height: 240 } },
          (decodedText) => {
            if (!mounted) return;
            try { scanner.pause(true); } catch {}
            onDetected(decodedText);
          },
          () => {}
        );
      } catch (e) {
        setError(e?.message || 'Impossible d\'accéder à la caméra');
      }
    })();
    return () => {
      mounted = false;
      if (ref.current) {
        ref.current.stop().then(() => ref.current.clear()).catch(() => {});
      }
    };
  }, [onDetected]);

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col" data-testid="qr-scanner">
      <div className="absolute top-0 inset-x-0 bg-gradient-to-b from-black/80 to-transparent z-10 p-4 flex items-center justify-between">
        <span className="font-mono text-sm text-white tracking-wider">{label}</span>
        <button
          data-testid="qr-cancel"
          onClick={onCancel}
          className="px-4 py-2 rounded-full bg-white/10 backdrop-blur text-white font-mono text-xs uppercase tracking-wider border border-white/20"
        >
          Annuler
        </button>
      </div>

      <div id={containerId} className="flex-1 w-full" style={{ minHeight: '60vh' }} />

      {error && (
        <div className="absolute inset-0 flex items-center justify-center p-6 z-20 bg-black/95">
          <div className="max-w-sm text-center">
            <p className="font-mono text-sm text-red-400 mb-4">⚠ {error}</p>
            <p className="font-mono text-xs text-white/60 mb-4">Saisis le code badge à la main si nécessaire.</p>
            <button onClick={onCancel} className="px-5 py-3 rounded-full bg-white/10 text-white font-mono text-sm border border-white/20">
              Retour
            </button>
          </div>
        </div>
      )}

      <div className="absolute bottom-0 inset-x-0 z-10 p-4 bg-gradient-to-t from-black/90 to-transparent">
        {showManual ? (
          <div className="flex gap-2">
            <input
              data-testid="qr-manual-input"
              value={manual}
              onChange={(e) => setManual(e.target.value)}
              placeholder="badge_id ou QR token"
              autoFocus
              className="flex-1 px-4 py-3 rounded-xl bg-white text-black font-mono text-base"
            />
            <button
              data-testid="qr-manual-submit"
              onClick={() => manual.trim() && onDetected(manual.trim())}
              className="px-5 py-3 rounded-xl bg-[#f7931a] text-black font-mono text-sm uppercase font-bold tracking-wider"
            >
              OK
            </button>
          </div>
        ) : (
          <button
            data-testid="qr-manual-toggle"
            onClick={() => setShowManual(true)}
            className="w-full px-5 py-3 rounded-xl bg-white/10 backdrop-blur text-white font-mono text-sm uppercase tracking-wider border border-white/20"
          >
            ⌨ Saisie manuelle
          </button>
        )}
      </div>
    </div>
  );
}
