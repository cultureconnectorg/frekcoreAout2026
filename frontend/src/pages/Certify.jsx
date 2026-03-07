/**
 * FREK v2 — NODE 11 · EXPERIENCE
 * ================================
 * Interface principale — 1 bouton, 3 secondes, FREK-ID
 * Design bleu FREK #2cc4f5
 */
import { useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { QRCodeSVG } from 'qrcode.react';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

const INVISIBLE_OPERATIONS = [
  "Capture signal audio",
  "Extraction FFT 512 bandes",
  "Calcul RMS + ZCR",
  "Extraction MFCC 13 coefficients",
  "Centroïde spectral",
  "Flux spectral",
  "Construction vecteur 528D",
  "SHA-256 signal",
  "SHA-256 metadata",
  "Hash chaîné",
  "Comparaison vectorielle",
  "Détection similarités",
  "Graphe relationnel",
  "Réseau lucioles",
  "Génération certificat",
  "Archivage distribué",
  "Synchronisation"
];

export function Certify() {
  const [state, setState] = useState('idle');
  const [frekId, setFrekId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [currentOperation, setCurrentOperation] = useState(0);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const simulateProgress = useCallback(() => {
    let op = 0;
    const interval = setInterval(() => {
      op++;
      setCurrentOperation(op);
      setProgress((op / INVISIBLE_OPERATIONS.length) * 100);
      if (op >= INVISIBLE_OPERATIONS.length) {
        clearInterval(interval);
      }
    }, 120);
    return interval;
  }, []);

  const certifyAudio = async (audioBlob) => {
    setState('processing');
    setError(null);
    setCurrentOperation(0);
    setProgress(0);

    const progressInterval = simulateProgress();

    try {
      const reader = new FileReader();
      const base64Promise = new Promise((resolve, reject) => {
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
      });
      reader.readAsDataURL(audioBlob);
      const audioBase64 = await base64Promise;

      const response = await fetch(`${API_URL}/api/frek/certify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          audio_base64: audioBase64,
          artiste_id: `ARTISTE-${Date.now().toString(36).toUpperCase()}`,
        }),
      });

      if (!response.ok) throw new Error(`Erreur ${response.status}`);

      const data = await response.json();
      
      clearInterval(progressInterval);
      setProgress(100);
      setCurrentOperation(INVISIBLE_OPERATIONS.length);
      await new Promise(r => setTimeout(r, 300));

      setFrekId(data.frek_id);
      setResult(data);
      setState('complete');

    } catch (err) {
      clearInterval(progressInterval);
      setError(err.message || 'Erreur certification');
      setState('error');
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) certifyAudio(file);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        certifyAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setState('recording');
    } catch (err) {
      setError('Microphone inaccessible');
      setState('error');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  };

  const reset = () => {
    setState('idle');
    setFrekId(null);
    setResult(null);
    setError(null);
    setCurrentOperation(0);
    setProgress(0);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-dark via-navy to-dark text-white flex flex-col">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-dark/90 backdrop-blur-xl border-b border-frek-500/20">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img src="/frek-logo.png" alt="FREK" className="h-8 w-auto" />
            <span className="font-display text-xl tracking-wider text-frek-500">FREK</span>
          </Link>
          
          <div className="flex items-center gap-4">
            <Link
              to="/generate"
              className="px-4 py-2 font-mono text-xs uppercase tracking-wider text-frek-400 hover:text-frek-300 border border-frek-500/30 hover:border-frek-500/50 rounded transition-all"
              data-testid="generate-link"
            >
              Génerer attestation
            </Link>
            <a
              href="/#spec"
              className="font-mono text-xs uppercase tracking-wider text-mid hover:text-frek-400 transition-colors"
            >
              Spec
            </a>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-6 pt-20 pb-12">
        <div className="w-full max-w-lg">
          <AnimatePresence mode="wait">
            {/* IDLE */}
            {state === 'idle' && (
              <motion.div
                key="idle"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="text-center"
              >
                {/* Titre */}
                <h1 className="font-display text-5xl md:text-6xl tracking-wider text-frek-500 mb-4">
                  CERTIFIER
                </h1>
                <p className="font-mono text-sm text-mid mb-12">
                  1 geste · 17 opérations · 3 secondes
                </p>

                {/* Iceberg */}
                <div className="mb-12 relative">
                  <div className="font-mono text-[10px] text-frek-400 uppercase tracking-[0.5em] mb-2">
                    3% visible
                  </div>
                  <div className="w-32 h-0.5 bg-gradient-to-r from-transparent via-frek-500 to-transparent mx-auto mb-4" />
                  <div className="font-mono text-[10px] text-frek-800 uppercase tracking-[0.3em]">
                    97% invisible
                  </div>
                </div>

                {/* BOUTON PRINCIPAL */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="group relative w-40 h-40 mx-auto mb-8 rounded-full bg-gradient-to-br from-frek-500 to-frek-600 hover:from-frek-400 hover:to-frek-500 transition-all duration-500 hover:scale-105 animate-glow"
                  data-testid="certify-button"
                >
                  <span className="absolute inset-0 flex items-center justify-center">
                    <span className="w-5 h-5 bg-white rounded-full group-hover:scale-110 transition-transform shadow-lg" />
                  </span>
                  <span className="absolute inset-0 rounded-full border-2 border-frek-400/30 animate-ping" style={{ animationDuration: '2s' }} />
                </button>

                <p className="font-mono text-sm text-frek-400 mb-6">
                  Cliquez pour certifier un fichier audio
                </p>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  data-testid="file-input"
                />

                <button
                  onClick={startRecording}
                  className="font-mono text-xs text-frek-600 hover:text-frek-400 uppercase tracking-wider transition-colors flex items-center gap-2 mx-auto"
                  data-testid="record-button"
                >
                  <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  ou enregistrer live
                </button>
              </motion.div>
            )}

            {/* RECORDING */}
            {state === 'recording' && (
              <motion.div
                key="recording"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  className="w-32 h-32 mx-auto mb-8 rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center"
                >
                  <span className="w-6 h-6 bg-red-500 rounded-full animate-pulse" />
                </motion.div>

                <p className="font-mono text-sm text-red-400 mb-8">
                  Enregistrement en cours...
                </p>

                <button
                  onClick={stopRecording}
                  className="px-8 py-3 bg-red-500 text-white font-mono text-xs uppercase tracking-wider rounded hover:bg-red-600 transition-colors"
                  data-testid="stop-recording-button"
                >
                  Arrêter et certifier
                </button>
              </motion.div>
            )}

            {/* PROCESSING */}
            {state === 'processing' && (
              <motion.div
                key="processing"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                <div className="mb-8">
                  <div className="font-mono text-xs text-frek-400 uppercase tracking-wider mb-4 h-5">
                    {INVISIBLE_OPERATIONS[Math.min(currentOperation, INVISIBLE_OPERATIONS.length - 1)]}
                  </div>
                  
                  <div className="w-full h-1.5 bg-frek-900 rounded-full overflow-hidden mb-4">
                    <motion.div
                      className="h-full bg-gradient-to-r from-frek-600 to-frek-400"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.1 }}
                    />
                  </div>

                  <div className="font-mono text-xs text-frek-600">
                    {currentOperation} / {INVISIBLE_OPERATIONS.length}
                  </div>
                </div>

                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                  className="w-16 h-16 mx-auto border-2 border-frek-800 border-t-frek-500 rounded-full"
                />
              </motion.div>
            )}

            {/* COMPLETE */}
            {state === 'complete' && frekId && (
              <motion.div
                key="complete"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", duration: 0.5 }}
                  className="w-20 h-20 mx-auto mb-6 rounded-full bg-frek-500/20 border-2 border-frek-500 flex items-center justify-center"
                >
                  <svg className="w-10 h-10 text-frek-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </motion.div>

                <h2 className="font-display text-2xl text-frek-500 mb-2">CERTIFIÉ</h2>

                <div className="mb-6">
                  <div className="font-mono text-[10px] text-frek-600 uppercase tracking-wider mb-2">
                    FREK-ID
                  </div>
                  <div 
                    className="font-mono text-sm text-frek-400 break-all px-4 py-2 bg-frek-900/50 rounded-lg border border-frek-500/20"
                    data-testid="frek-id"
                  >
                    {frekId}
                  </div>
                </div>

                {/* QR Code */}
                <div className="inline-block p-4 bg-white rounded-xl mb-6 shadow-lg shadow-frek-500/20">
                  <QRCodeSVG
                    value={`${window.location.origin}/verify/${frekId}`}
                    size={140}
                    level="M"
                    fgColor="#0a1520"
                    data-testid="qr-code"
                  />
                </div>

                {/* Détails */}
                <details className="text-left mb-6 bg-frek-900/30 rounded-lg overflow-hidden border border-frek-500/10">
                  <summary className="px-4 py-3 cursor-pointer font-mono text-xs text-frek-500 uppercase tracking-wider hover:bg-frek-900/50 transition-colors">
                    Détails techniques
                  </summary>
                  <div className="px-4 pb-4 space-y-1 font-mono text-[11px] text-frek-600">
                    {result?.extraction && (
                      <div>Vecteur: {result.extraction.vector_dimensions}D</div>
                    )}
                    {result?.identity && (
                      <>
                        <div>SHA-256: {result.identity.sha256_signal?.slice(0, 16)}...</div>
                        <div>Hash chaîné: {result.identity.hash_chaine?.slice(0, 16)}...</div>
                      </>
                    )}
                    {result?.cycle && (
                      <div>Stade: {result.cycle.stade_actif}</div>
                    )}
                    <div>Temps: {result?.processing_time_ms}ms</div>
                  </div>
                </details>

                {/* Actions */}
                <div className="flex gap-4 justify-center">
                  <button
                    onClick={() => navigator.clipboard.writeText(frekId)}
                    className="px-6 py-3 border border-frek-500/30 text-frek-400 font-mono text-xs uppercase tracking-wider hover:border-frek-500/60 hover:text-frek-300 rounded transition-all"
                    data-testid="copy-button"
                  >
                    Copier
                  </button>
                  <button
                    onClick={reset}
                    className="px-6 py-3 bg-frek-500 text-dark font-mono text-xs uppercase tracking-wider hover:bg-frek-400 rounded transition-all font-bold"
                    data-testid="new-certification-button"
                  >
                    Nouvelle certification
                  </button>
                </div>
              </motion.div>
            )}

            {/* ERROR */}
            {state === 'error' && (
              <motion.div
                key="error"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                <div className="w-20 h-20 mx-auto mb-8 rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center">
                  <svg className="w-10 h-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>

                <p className="font-mono text-sm text-red-400 mb-8">{error}</p>

                <button
                  onClick={reset}
                  className="px-8 py-3 border border-red-500/30 text-red-400 font-mono text-xs uppercase tracking-wider hover:border-red-500/50 rounded transition-colors"
                  data-testid="retry-button"
                >
                  Réessayer
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 text-center border-t border-frek-500/10">
        <p className="font-mono text-[10px] text-frek-800 uppercase tracking-[0.3em]">
          Comme une luciole — elle s'allume. C'est tout.
        </p>
      </footer>
    </div>
  );
}

export default Certify;
