/**
 * FREK v2 — Interface Principale
 * Design premium blanc avec effets 3D raffinés
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
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 flex flex-col relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Gradient orbs */}
        <div className="absolute -top-32 -right-32 w-96 h-96 bg-gradient-to-br from-[#2cc4f5]/20 to-[#06b6d4]/10 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '4s' }} />
        <div className="absolute -bottom-32 -left-32 w-[500px] h-[500px] bg-gradient-to-tr from-[#0ea5e9]/10 to-[#2cc4f5]/5 rounded-full blur-3xl" />
        <div className="absolute top-1/3 right-1/4 w-64 h-64 bg-[#2cc4f5]/5 rounded-full blur-2xl" />
        
        {/* Grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage: `
              linear-gradient(to right, #2cc4f5 1px, transparent 1px),
              linear-gradient(to bottom, #2cc4f5 1px, transparent 1px)
            `,
            backgroundSize: '60px 60px'
          }}
        />
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50">
        <div className="mx-4 sm:mx-6 mt-4">
          <div className="max-w-5xl mx-auto bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/50 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 sm:gap-3 group">
              <div className="relative">
                <img src="/frek-logo.png" alt="FREK" className="h-7 sm:h-9 w-auto relative z-10" />
                <div className="absolute inset-0 bg-[#2cc4f5]/20 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <span className="font-display text-xl sm:text-2xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">
                FREK
              </span>
            </Link>
            
            <Link
              to="/generate"
              className="px-4 py-2 font-mono text-[10px] sm:text-xs uppercase tracking-wider text-[#2cc4f5] hover:text-white bg-[#2cc4f5]/5 hover:bg-[#2cc4f5] border border-[#2cc4f5]/20 hover:border-[#2cc4f5] rounded-xl transition-all duration-300 hover:shadow-lg hover:shadow-[#2cc4f5]/25"
            >
              Attestation
            </Link>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 pt-28 sm:pt-32 pb-32 sm:pb-40 relative z-10">
        <div className="w-full max-w-md">
          <AnimatePresence mode="wait">
            {/* IDLE */}
            {state === 'idle' && (
              <motion.div
                key="idle"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="text-center"
              >
                {/* Titre avec effet */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.1, duration: 0.5 }}
                >
                  <h1 className="font-display text-5xl sm:text-6xl md:text-7xl tracking-wide mb-3 sm:mb-4">
                    <span className="bg-gradient-to-r from-[#2cc4f5] via-[#06b6d4] to-[#0ea5e9] bg-clip-text text-transparent drop-shadow-sm">
                      CERTIFIER
                    </span>
                  </h1>
                  <p className="font-mono text-[11px] sm:text-xs text-slate-400 tracking-[0.2em] uppercase mb-10 sm:mb-14">
                    Certification fréquentielle
                  </p>
                </motion.div>

                {/* BOUTON PRINCIPAL 3D PREMIUM */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2, duration: 0.6, type: "spring" }}
                  className="relative mb-8 sm:mb-10"
                >
                  {/* Glow effect behind button */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-40 h-40 sm:w-52 sm:h-52 bg-[#2cc4f5]/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '3s' }} />
                  </div>
                  
                  <motion.button
                    onClick={() => fileInputRef.current?.click()}
                    whileHover={{ scale: 1.08, y: -5 }}
                    whileTap={{ scale: 0.95 }}
                    className="group relative w-40 h-40 sm:w-48 sm:h-48 mx-auto rounded-full cursor-pointer"
                    style={{
                      background: 'linear-gradient(145deg, #3dd6ff 0%, #2cc4f5 30%, #1a9fd4 70%, #0d8bc4 100%)',
                      boxShadow: `
                        0 25px 50px -12px rgba(44, 196, 245, 0.5),
                        0 12px 25px -8px rgba(44, 196, 245, 0.4),
                        inset 0 2px 20px rgba(255,255,255,0.4),
                        inset 0 -8px 25px rgba(0,0,0,0.15)
                      `,
                    }}
                    data-testid="certify-button"
                  >
                    {/* Highlight arc */}
                    <span className="absolute top-2 left-4 right-4 h-16 sm:h-20 rounded-t-full bg-gradient-to-b from-white/40 to-transparent" />
                    
                    {/* Inner ring */}
                    <span className="absolute inset-4 sm:inset-5 rounded-full border border-white/20" />
                    
                    {/* Center dot with pulse */}
                    <span className="absolute inset-0 flex items-center justify-center">
                      <motion.span 
                        animate={{ scale: [1, 1.1, 1] }}
                        transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                        className="w-6 h-6 sm:w-7 sm:h-7 bg-white rounded-full shadow-lg"
                        style={{ boxShadow: '0 4px 20px rgba(255,255,255,0.5), inset 0 -3px 8px rgba(0,0,0,0.1)' }}
                      />
                    </span>

                    {/* Hover ring effect */}
                    <span className="absolute inset-0 rounded-full border-2 border-white/0 group-hover:border-white/30 transition-all duration-500" />
                  </motion.button>
                </motion.div>

                <motion.p 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.4 }}
                  className="font-mono text-sm text-slate-400 mb-6"
                >
                  Sélectionner un fichier audio
                </motion.p>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  data-testid="file-input"
                />

                <motion.button
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  onClick={startRecording}
                  className="group font-mono text-xs text-slate-400 hover:text-red-500 uppercase tracking-wider transition-all duration-300 flex items-center gap-2.5 mx-auto px-4 py-2 rounded-full hover:bg-red-50"
                  data-testid="record-button"
                >
                  <span className="w-2 h-2 bg-red-500 rounded-full shadow-lg shadow-red-500/50 group-hover:animate-pulse" />
                  Enregistrer live
                </motion.button>
              </motion.div>
            )}

            {/* RECORDING */}
            {state === 'recording' && (
              <motion.div
                key="recording"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="text-center"
              >
                <motion.div
                  animate={{ scale: [1, 1.15, 1], opacity: [1, 0.8, 1] }}
                  transition={{ repeat: Infinity, duration: 1.2 }}
                  className="relative w-36 h-36 sm:w-40 sm:h-40 mx-auto mb-8"
                >
                  <div className="absolute inset-0 rounded-full bg-red-100 animate-ping opacity-30" />
                  <div className="absolute inset-0 rounded-full bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-300 shadow-xl shadow-red-200/50 flex items-center justify-center">
                    <span className="w-6 h-6 bg-red-500 rounded-full shadow-lg shadow-red-500/50" />
                  </div>
                </motion.div>

                <p className="font-mono text-sm text-red-500 mb-8 tracking-wider">
                  Enregistrement en cours...
                </p>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={stopRecording}
                  className="px-8 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white font-mono text-xs uppercase tracking-wider rounded-xl hover:from-red-600 hover:to-red-700 transition-all shadow-xl shadow-red-500/30"
                  data-testid="stop-recording-button"
                >
                  Arrêter
                </motion.button>
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
                <div className="mb-10">
                  <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden mb-4 shadow-inner">
                    <motion.div
                      className="h-full rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.1 }}
                      style={{ 
                        background: 'linear-gradient(90deg, #2cc4f5 0%, #06b6d4 50%, #0ea5e9 100%)',
                        boxShadow: '0 0 20px rgba(44, 196, 245, 0.6)' 
                      }}
                    />
                  </div>
                  <div className="font-mono text-lg text-[#2cc4f5] font-semibold">
                    {Math.round(progress)}%
                  </div>
                </div>

                <div className="relative w-20 h-20 mx-auto">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}
                    className="absolute inset-0 rounded-full border-4 border-slate-100 border-t-[#2cc4f5] border-r-[#06b6d4]"
                    style={{ boxShadow: '0 0 30px rgba(44, 196, 245, 0.2)' }}
                  />
                </div>
              </motion.div>
            )}

            {/* COMPLETE */}
            {state === 'complete' && frekId && (
              <motion.div
                key="complete"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: "spring", duration: 0.6 }}
                  className="w-20 h-20 sm:w-24 sm:h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-[#2cc4f5]/20 to-[#06b6d4]/10 border-2 border-[#2cc4f5] flex items-center justify-center shadow-xl shadow-[#2cc4f5]/20"
                >
                  <svg className="w-10 h-10 sm:w-12 sm:h-12 text-[#2cc4f5]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                </motion.div>

                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="mb-6"
                >
                  <div className="font-mono text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-2">
                    FREK-ID
                  </div>
                  <div 
                    className="font-mono text-sm text-[#0ea5e9] break-all px-5 py-3 bg-white rounded-2xl border border-slate-100 shadow-lg shadow-slate-200/50"
                    data-testid="frek-id"
                  >
                    {frekId}
                  </div>
                </motion.div>

                {/* QR Code */}
                <motion.div 
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.3 }}
                  className="inline-block p-5 bg-white rounded-3xl mb-8 shadow-xl shadow-slate-200/50 border border-slate-100"
                >
                  <QRCodeSVG
                    value={`${window.location.origin}/verify/${frekId}`}
                    size={140}
                    level="M"
                    fgColor="#0ea5e9"
                    data-testid="qr-code"
                  />
                </motion.div>

                {/* Actions */}
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="flex gap-4 justify-center"
                >
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => navigator.clipboard.writeText(frekId)}
                    className="px-6 py-3 border border-slate-200 text-slate-500 font-mono text-xs uppercase tracking-wider hover:border-[#2cc4f5] hover:text-[#2cc4f5] rounded-xl transition-all shadow-sm hover:shadow-lg hover:shadow-[#2cc4f5]/10"
                    data-testid="copy-button"
                  >
                    Copier
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={reset}
                    className="px-6 py-3 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white font-mono text-xs uppercase tracking-wider rounded-xl transition-all font-semibold shadow-lg shadow-[#2cc4f5]/30 hover:shadow-xl hover:shadow-[#2cc4f5]/40"
                    data-testid="new-certification-button"
                  >
                    Nouveau
                  </motion.button>
                </motion.div>
              </motion.div>
            )}

            {/* ERROR */}
            {state === 'error' && (
              <motion.div
                key="error"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                <div className="w-20 h-20 mx-auto mb-8 rounded-full bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-300 flex items-center justify-center shadow-xl shadow-red-200/30">
                  <svg className="w-10 h-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>

                <p className="font-mono text-sm text-red-500 mb-8">{error}</p>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={reset}
                  className="px-8 py-3 border-2 border-red-200 text-red-500 font-mono text-xs uppercase tracking-wider hover:border-red-400 hover:bg-red-50 rounded-xl transition-all"
                  data-testid="retry-button"
                >
                  Réessayer
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 bg-white/60 backdrop-blur-xl border-t border-slate-100">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
          {/* Liens principaux */}
          <div className="flex flex-wrap justify-center gap-6 sm:gap-8 mb-5">
            <Link to="/philosophy" className="font-mono text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors duration-300">
              Philosophie
            </Link>
            <Link to="/spec" className="font-mono text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors duration-300">
              Spécifications
            </Link>
            <Link to="/help" className="font-mono text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors duration-300">
              Aide
            </Link>
            <a href="https://frekcore.com" target="_blank" rel="noopener noreferrer" className="font-mono text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors duration-300">
              frekcore.com
            </a>
          </div>

          {/* Séparateur */}
          <div className="w-24 h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent mx-auto mb-5" />

          {/* Liens légaux */}
          <div className="flex flex-wrap justify-center gap-4 sm:gap-6 mb-6">
            <Link to="/legal" className="font-mono text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors">
              Cadre juridique
            </Link>
            <Link to="/privacy" className="font-mono text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors">
              Confidentialité
            </Link>
            <Link to="/cookies" className="font-mono text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors">
              Cookies
            </Link>
            <Link to="/terms" className="font-mono text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors">
              Conditions
            </Link>
            <Link to="/imprint" className="font-mono text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors">
              Mentions légales
            </Link>
          </div>
          
          {/* Copyright */}
          <div className="text-center">
            <p className="font-mono text-[10px] text-slate-300 tracking-wider">
              © 2026 CVLN Group · Standard ouvert CC BY 4.0
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Certify;
