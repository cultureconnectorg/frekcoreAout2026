/**
 * FREK v2 — Interface Principale
 * Design blanc avec effet 3D
 */
import { useState, useRef } from 'react';
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
    <div className="min-h-screen bg-gradient-to-br from-white via-slate-50 to-gray-100 text-slate-800 flex flex-col relative overflow-hidden">
      {/* Background 3D effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-[#2cc4f5]/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-[#2cc4f5]/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-radial from-[#2cc4f5]/5 to-transparent rounded-full blur-2xl" />
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/50 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 sm:gap-3">
            <img src="/frek-logo.png" alt="FREK" className="h-6 sm:h-8 w-auto" />
            <span className="font-display text-lg sm:text-xl tracking-wider text-[#2cc4f5] drop-shadow-sm">FREK</span>
          </Link>
          
          <nav className="flex items-center gap-2 sm:gap-4">
            <Link
              to="/generate"
              className="px-3 py-1.5 font-mono text-[10px] sm:text-xs uppercase tracking-wider text-[#2cc4f5] hover:text-[#1a9fd4] border border-[#2cc4f5]/30 hover:border-[#2cc4f5]/60 rounded-lg transition-all hover:shadow-md hover:shadow-[#2cc4f5]/10"
            >
              Attestation
            </Link>
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 pt-20 sm:pt-24 pb-24 sm:pb-32 relative z-10">
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
                <h1 className="font-display text-4xl sm:text-5xl md:text-6xl tracking-wider text-[#2cc4f5] mb-2 sm:mb-4 drop-shadow-lg">
                  CERTIFIER
                </h1>
                <p className="font-mono text-[10px] sm:text-xs text-slate-500 mb-8 sm:mb-12">
                  Certification fréquentielle
                </p>

                {/* BOUTON PRINCIPAL 3D */}
                <motion.button
                  onClick={() => fileInputRef.current?.click()}
                  whileHover={{ scale: 1.05, rotateX: 5, rotateY: 5 }}
                  whileTap={{ scale: 0.98 }}
                  className="group relative w-36 h-36 sm:w-44 sm:h-44 mx-auto mb-6 sm:mb-8 rounded-full bg-gradient-to-br from-[#2cc4f5] via-[#33cfff] to-[#1a9fd4] transition-all duration-500"
                  style={{
                    boxShadow: '0 20px 60px -10px rgba(44, 196, 245, 0.5), 0 10px 30px -5px rgba(44, 196, 245, 0.3), inset 0 -5px 20px rgba(0,0,0,0.1), inset 0 5px 20px rgba(255,255,255,0.3)',
                    transform: 'perspective(500px) rotateX(5deg)',
                  }}
                  data-testid="certify-button"
                >
                  {/* Inner glow */}
                  <span className="absolute inset-2 rounded-full bg-gradient-to-br from-white/30 to-transparent" />
                  
                  {/* Center dot */}
                  <span className="absolute inset-0 flex items-center justify-center">
                    <span 
                      className="w-5 h-5 sm:w-6 sm:h-6 bg-white rounded-full group-hover:scale-110 transition-transform"
                      style={{ boxShadow: '0 4px 15px rgba(0,0,0,0.2), inset 0 -2px 5px rgba(0,0,0,0.1)' }}
                    />
                  </span>

                  {/* Reflection */}
                  <span className="absolute inset-0 rounded-full overflow-hidden">
                    <span className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-white/40 to-transparent rotate-45" />
                  </span>
                </motion.button>

                <p className="font-mono text-xs sm:text-sm text-slate-400 mb-4 sm:mb-6">
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
                  className="font-mono text-[10px] sm:text-xs text-slate-400 hover:text-red-500 uppercase tracking-wider transition-colors flex items-center gap-2 mx-auto"
                  data-testid="record-button"
                >
                  <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-red-500 rounded-full shadow-lg shadow-red-500/50" />
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
                  className="w-28 h-28 sm:w-32 sm:h-32 mx-auto mb-6 sm:mb-8 rounded-full bg-red-50 border-2 border-red-400 flex items-center justify-center shadow-xl shadow-red-500/20"
                >
                  <span className="w-5 h-5 sm:w-6 sm:h-6 bg-red-500 rounded-full animate-pulse shadow-lg shadow-red-500/50" />
                </motion.div>

                <p className="font-mono text-xs sm:text-sm text-red-500 mb-6 sm:mb-8">
                  Enregistrement...
                </p>

                <button
                  onClick={stopRecording}
                  className="px-6 sm:px-8 py-2.5 sm:py-3 bg-red-500 text-white font-mono text-[10px] sm:text-xs uppercase tracking-wider rounded-lg hover:bg-red-600 transition-colors shadow-lg shadow-red-500/30"
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
                  <div className="w-full h-2 sm:h-3 bg-slate-100 rounded-full overflow-hidden mb-3 sm:mb-4 shadow-inner">
                    <motion.div
                      className="h-full bg-gradient-to-r from-[#2cc4f5] to-[#33cfff] rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.1 }}
                      style={{ boxShadow: '0 0 20px rgba(44, 196, 245, 0.5)' }}
                    />
                  </div>
                  <div className="font-mono text-xs sm:text-sm text-[#2cc4f5]">
                    {Math.round(progress)}%
                  </div>
                </div>

                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                  className="w-12 h-12 sm:w-16 sm:h-16 mx-auto border-3 border-slate-200 border-t-[#2cc4f5] rounded-full shadow-lg"
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
                  className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-4 sm:mb-6 rounded-full bg-gradient-to-br from-[#2cc4f5]/20 to-[#2cc4f5]/5 border-2 border-[#2cc4f5] flex items-center justify-center shadow-xl shadow-[#2cc4f5]/20"
                >
                  <svg className="w-8 h-8 sm:w-10 sm:h-10 text-[#2cc4f5]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </motion.div>

                <div className="mb-4 sm:mb-6">
                  <div className="font-mono text-[9px] sm:text-[10px] text-slate-400 uppercase tracking-wider mb-1 sm:mb-2">
                    FREK-ID
                  </div>
                  <div 
                    className="font-mono text-xs sm:text-sm text-[#2cc4f5] break-all px-3 sm:px-4 py-2 bg-white rounded-xl border border-slate-200 shadow-lg"
                    data-testid="frek-id"
                  >
                    {frekId}
                  </div>
                </div>

                {/* QR Code */}
                <div 
                  className="inline-block p-3 sm:p-4 bg-white rounded-2xl mb-4 sm:mb-6"
                  style={{ boxShadow: '0 20px 40px -10px rgba(0,0,0,0.1), 0 10px 20px -5px rgba(44, 196, 245, 0.1)' }}
                >
                  <QRCodeSVG
                    value={`${window.location.origin}/verify/${frekId}`}
                    size={120}
                    level="M"
                    fgColor="#1a9fd4"
                    data-testid="qr-code"
                  />
                </div>

                {/* Actions */}
                <div className="flex gap-3 sm:gap-4 justify-center">
                  <button
                    onClick={() => navigator.clipboard.writeText(frekId)}
                    className="px-4 sm:px-6 py-2 sm:py-2.5 border border-slate-300 text-slate-600 font-mono text-[10px] sm:text-xs uppercase tracking-wider hover:border-[#2cc4f5] hover:text-[#2cc4f5] rounded-lg transition-all shadow-sm hover:shadow-md"
                    data-testid="copy-button"
                  >
                    Copier
                  </button>
                  <button
                    onClick={reset}
                    className="px-4 sm:px-6 py-2 sm:py-2.5 bg-gradient-to-r from-[#2cc4f5] to-[#1a9fd4] text-white font-mono text-[10px] sm:text-xs uppercase tracking-wider hover:from-[#33cfff] hover:to-[#2cc4f5] rounded-lg transition-all font-bold shadow-lg shadow-[#2cc4f5]/30"
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
                <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-6 sm:mb-8 rounded-full bg-red-50 border-2 border-red-400 flex items-center justify-center shadow-xl shadow-red-500/10">
                  <svg className="w-8 h-8 sm:w-10 sm:h-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>

                <p className="font-mono text-xs sm:text-sm text-red-500 mb-6 sm:mb-8">{error}</p>

                <button
                  onClick={reset}
                  className="px-6 sm:px-8 py-2.5 sm:py-3 border border-red-300 text-red-500 font-mono text-[10px] sm:text-xs uppercase tracking-wider hover:border-red-500 rounded-lg transition-colors shadow-sm"
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
      <footer className="border-t border-slate-200/50 bg-white/50 backdrop-blur-sm relative z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
          {/* Liens principaux */}
          <div className="flex flex-wrap justify-center gap-4 sm:gap-6 mb-4">
            <Link to="/philosophy" className="font-mono text-[10px] sm:text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors">
              Philosophie
            </Link>
            <Link to="/spec" className="font-mono text-[10px] sm:text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors">
              Spécifications
            </Link>
            <Link to="/help" className="font-mono text-[10px] sm:text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors">
              Aide
            </Link>
            <a href="https://frekcore.com" target="_blank" rel="noopener noreferrer" className="font-mono text-[10px] sm:text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors">
              frekcore.com
            </a>
          </div>

          {/* Liens légaux */}
          <div className="flex flex-wrap justify-center gap-3 sm:gap-5 mb-4 sm:mb-6">
            <Link to="/legal" className="font-mono text-[9px] sm:text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors">
              Cadre juridique
            </Link>
            <Link to="/privacy" className="font-mono text-[9px] sm:text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors">
              Confidentialité
            </Link>
            <Link to="/cookies" className="font-mono text-[9px] sm:text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors">
              Cookies
            </Link>
            <Link to="/terms" className="font-mono text-[9px] sm:text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors">
              Conditions
            </Link>
            <Link to="/imprint" className="font-mono text-[9px] sm:text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors">
              Mentions légales
            </Link>
          </div>
          
          {/* Copyright */}
          <div className="text-center">
            <p className="font-mono text-[9px] sm:text-[10px] text-slate-300 uppercase tracking-wider">
              © 2026 CVLN Group · Standard ouvert
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Certify;
