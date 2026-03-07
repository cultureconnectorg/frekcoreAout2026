/**
 * FREK v2 — Interface Principale
 * Design bleu #2cc4f5 - Minimaliste
 */
import { useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { QRCodeSVG } from 'qrcode.react';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

export function Certify() {
  const [state, setState] = useState('idle');
  const [frekId, setFrekId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const certifyAudio = async (audioBlob) => {
    setState('processing');
    setError(null);
    setProgress(0);

    // Animation progression
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 5, 95));
    }, 100);

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
          artiste_id: `FREK-${Date.now().toString(36).toUpperCase()}`,
        }),
      });

      if (!response.ok) throw new Error(`Erreur ${response.status}`);

      const data = await response.json();
      
      clearInterval(progressInterval);
      setProgress(100);
      await new Promise(r => setTimeout(r, 300));

      setFrekId(data.frek_id);
      setResult(data);
      setState('complete');

    } catch (err) {
      clearInterval(progressInterval);
      setError(err.message || 'Erreur');
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
    setProgress(0);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#050a0d] via-[#0a1520] to-[#050a0d] text-white flex flex-col">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#050a0d]/95 backdrop-blur-xl border-b border-[#2cc4f5]/10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 sm:gap-3">
            <img src="/frek-logo.png" alt="FREK" className="h-6 sm:h-8 w-auto" />
            <span className="font-display text-lg sm:text-xl tracking-wider text-[#2cc4f5]">FREK</span>
          </Link>
          
          <nav className="flex items-center gap-2 sm:gap-4">
            <Link
              to="/generate"
              className="px-3 py-1.5 font-mono text-[10px] sm:text-xs uppercase tracking-wider text-[#2cc4f5]/70 hover:text-[#2cc4f5] border border-[#2cc4f5]/20 hover:border-[#2cc4f5]/40 rounded transition-all"
            >
              Attestation
            </Link>
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 pt-20 sm:pt-24 pb-24 sm:pb-32">
        <div className="w-full max-w-md">
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
                <h1 className="font-display text-4xl sm:text-5xl md:text-6xl tracking-wider text-[#2cc4f5] mb-2 sm:mb-4">
                  CERTIFIER
                </h1>
                <p className="font-mono text-[10px] sm:text-xs text-[#8ab4c8]/60 mb-8 sm:mb-12">
                  Certification fréquentielle
                </p>

                {/* BOUTON PRINCIPAL */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="group relative w-32 h-32 sm:w-40 sm:h-40 mx-auto mb-6 sm:mb-8 rounded-full bg-gradient-to-br from-[#2cc4f5] to-[#23a0c8] hover:from-[#33cfff] hover:to-[#2cc4f5] transition-all duration-500 hover:scale-105 shadow-[0_0_30px_rgba(44,196,245,0.3)] hover:shadow-[0_0_50px_rgba(44,196,245,0.5)]"
                  data-testid="certify-button"
                >
                  <span className="absolute inset-0 flex items-center justify-center">
                    <span className="w-4 h-4 sm:w-5 sm:h-5 bg-white rounded-full group-hover:scale-110 transition-transform shadow-lg" />
                  </span>
                </button>

                <p className="font-mono text-xs sm:text-sm text-[#8ab4c8]/50 mb-4 sm:mb-6">
                  Sélectionner un fichier audio
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
                  className="font-mono text-[10px] sm:text-xs text-[#2cc4f5]/40 hover:text-[#2cc4f5]/70 uppercase tracking-wider transition-colors flex items-center gap-2 mx-auto"
                  data-testid="record-button"
                >
                  <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-red-500 rounded-full" />
                  Enregistrer
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
                  className="w-28 h-28 sm:w-32 sm:h-32 mx-auto mb-6 sm:mb-8 rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center"
                >
                  <span className="w-5 h-5 sm:w-6 sm:h-6 bg-red-500 rounded-full animate-pulse" />
                </motion.div>

                <p className="font-mono text-xs sm:text-sm text-red-400/80 mb-6 sm:mb-8">
                  Enregistrement...
                </p>

                <button
                  onClick={stopRecording}
                  className="px-6 sm:px-8 py-2.5 sm:py-3 bg-red-500 text-white font-mono text-[10px] sm:text-xs uppercase tracking-wider rounded hover:bg-red-600 transition-colors"
                  data-testid="stop-recording-button"
                >
                  Arrêter
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
                <div className="mb-6 sm:mb-8">
                  <div className="w-full h-1 sm:h-1.5 bg-[#0a1520] rounded-full overflow-hidden mb-3 sm:mb-4">
                    <motion.div
                      className="h-full bg-gradient-to-r from-[#23a0c8] to-[#2cc4f5]"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.1 }}
                    />
                  </div>
                  <div className="font-mono text-xs sm:text-sm text-[#2cc4f5]/60">
                    {Math.round(progress)}%
                  </div>
                </div>

                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                  className="w-12 h-12 sm:w-16 sm:h-16 mx-auto border-2 border-[#0a1520] border-t-[#2cc4f5] rounded-full"
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
                  className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-4 sm:mb-6 rounded-full bg-[#2cc4f5]/20 border-2 border-[#2cc4f5] flex items-center justify-center"
                >
                  <svg className="w-8 h-8 sm:w-10 sm:h-10 text-[#2cc4f5]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </motion.div>

                <div className="mb-4 sm:mb-6">
                  <div className="font-mono text-[9px] sm:text-[10px] text-[#2cc4f5]/50 uppercase tracking-wider mb-1 sm:mb-2">
                    FREK-ID
                  </div>
                  <div 
                    className="font-mono text-xs sm:text-sm text-[#2cc4f5] break-all px-3 sm:px-4 py-2 bg-[#0a1520]/80 rounded-lg border border-[#2cc4f5]/20"
                    data-testid="frek-id"
                  >
                    {frekId}
                  </div>
                </div>

                {/* QR Code */}
                <div className="inline-block p-3 sm:p-4 bg-white rounded-xl mb-4 sm:mb-6 shadow-lg shadow-[#2cc4f5]/10">
                  <QRCodeSVG
                    value={`${window.location.origin}/verify/${frekId}`}
                    size={120}
                    level="M"
                    fgColor="#0a1520"
                    data-testid="qr-code"
                  />
                </div>

                {/* Actions */}
                <div className="flex gap-3 sm:gap-4 justify-center">
                  <button
                    onClick={() => navigator.clipboard.writeText(frekId)}
                    className="px-4 sm:px-6 py-2 sm:py-2.5 border border-[#2cc4f5]/30 text-[#2cc4f5]/70 font-mono text-[10px] sm:text-xs uppercase tracking-wider hover:border-[#2cc4f5]/50 hover:text-[#2cc4f5] rounded transition-all"
                    data-testid="copy-button"
                  >
                    Copier
                  </button>
                  <button
                    onClick={reset}
                    className="px-4 sm:px-6 py-2 sm:py-2.5 bg-[#2cc4f5] text-[#050a0d] font-mono text-[10px] sm:text-xs uppercase tracking-wider hover:bg-[#33cfff] rounded transition-all font-bold"
                    data-testid="new-certification-button"
                  >
                    Nouveau
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
                <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-6 sm:mb-8 rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center">
                  <svg className="w-8 h-8 sm:w-10 sm:h-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>

                <p className="font-mono text-xs sm:text-sm text-red-400/80 mb-6 sm:mb-8">{error}</p>

                <button
                  onClick={reset}
                  className="px-6 sm:px-8 py-2.5 sm:py-3 border border-red-500/30 text-red-400 font-mono text-[10px] sm:text-xs uppercase tracking-wider hover:border-red-500/50 rounded transition-colors"
                  data-testid="retry-button"
                >
                  Réessayer
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer avec liens */}
      <footer className="border-t border-[#2cc4f5]/10 bg-[#050a0d]/80">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
          {/* Liens */}
          <div className="flex flex-wrap justify-center gap-4 sm:gap-6 mb-4 sm:mb-6">
            <Link to="/philosophy" className="font-mono text-[10px] sm:text-xs text-[#8ab4c8]/40 hover:text-[#2cc4f5]/70 uppercase tracking-wider transition-colors">
              Philosophie
            </Link>
            <Link to="/spec" className="font-mono text-[10px] sm:text-xs text-[#8ab4c8]/40 hover:text-[#2cc4f5]/70 uppercase tracking-wider transition-colors">
              Spécifications
            </Link>
            <Link to="/legal" className="font-mono text-[10px] sm:text-xs text-[#8ab4c8]/40 hover:text-[#2cc4f5]/70 uppercase tracking-wider transition-colors">
              Cadre juridique
            </Link>
            <a href="https://frekcore.com" target="_blank" rel="noopener noreferrer" className="font-mono text-[10px] sm:text-xs text-[#8ab4c8]/40 hover:text-[#2cc4f5]/70 uppercase tracking-wider transition-colors">
              frekcore.com
            </a>
          </div>
          
          {/* Copyright */}
          <div className="text-center">
            <p className="font-mono text-[9px] sm:text-[10px] text-[#8ab4c8]/20 uppercase tracking-wider">
              © 2026 CVLN Group · Standard ouvert
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Certify;
