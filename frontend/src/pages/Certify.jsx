/**
 * FREK v2 — Interface Principale
 * Design premium avec expérience psychologique immersive
 */
import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence, useMotionValue, useTransform, useSpring } from 'framer-motion';
import { QRCodeSVG } from 'qrcode.react';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

// Messages de progression engageants
const progressMessages = [
  { threshold: 0, text: "Initialisation..." },
  { threshold: 20, text: "Analyse du signal..." },
  { threshold: 40, text: "Extraction fréquentielle..." },
  { threshold: 60, text: "Calcul de l'empreinte..." },
  { threshold: 80, text: "Génération de l'identifiant..." },
  { threshold: 95, text: "Finalisation..." },
];

export function Certify() {
  const [state, setState] = useState('idle');
  const [frekId, setFrekId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [isHovering, setIsHovering] = useState(false);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Mouse tracking for parallax
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const smoothMouseX = useSpring(mouseX, { stiffness: 50, damping: 20 });
  const smoothMouseY = useSpring(mouseY, { stiffness: 50, damping: 20 });
  
  const backgroundX = useTransform(smoothMouseX, [0, window.innerWidth], [-20, 20]);
  const backgroundY = useTransform(smoothMouseY, [0, window.innerHeight], [-20, 20]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [mouseX, mouseY]);

  const getProgressMessage = () => {
    for (let i = progressMessages.length - 1; i >= 0; i--) {
      if (progress >= progressMessages[i].threshold) {
        return progressMessages[i].text;
      }
    }
    return progressMessages[0].text;
  };

  const certifyAudio = async (audioBlob) => {
    setState('processing');
    setError(null);
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 3, 95));
    }, 150);

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
      
      // Smooth completion animation
      for (let i = progress; i <= 100; i += 2) {
        await new Promise(r => setTimeout(r, 20));
        setProgress(i);
      }
      
      await new Promise(r => setTimeout(r, 500));

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
      {/* Animated Background with Parallax */}
      <motion.div 
        className="absolute inset-0 overflow-hidden pointer-events-none"
        style={{ x: backgroundX, y: backgroundY }}
      >
        {/* Breathing orbs */}
        <motion.div 
          animate={{ 
            scale: [1, 1.2, 1],
            opacity: [0.15, 0.25, 0.15]
          }}
          transition={{ repeat: Infinity, duration: 8, ease: "easeInOut" }}
          className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl"
        />
        <motion.div 
          animate={{ 
            scale: [1, 1.15, 1],
            opacity: [0.1, 0.2, 0.1]
          }}
          transition={{ repeat: Infinity, duration: 10, ease: "easeInOut", delay: 2 }}
          className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl"
        />
        <motion.div 
          animate={{ 
            scale: [1, 1.1, 1],
            x: [0, 30, 0],
            y: [0, -20, 0]
          }}
          transition={{ repeat: Infinity, duration: 12, ease: "easeInOut" }}
          className="absolute top-1/3 right-1/4 w-72 h-72 bg-[#2cc4f5]/10 rounded-full blur-2xl"
        />
        
        {/* Subtle grid */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `
              linear-gradient(to right, #2cc4f5 1px, transparent 1px),
              linear-gradient(to bottom, #2cc4f5 1px, transparent 1px)
            `,
            backgroundSize: '80px 80px'
          }}
        />
      </motion.div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50">
        <motion.div 
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="mx-4 sm:mx-6 mt-4"
        >
          <div className="max-w-5xl mx-auto bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/50 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 sm:gap-3 group">
              <motion.div 
                className="relative"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <img src="/frek-logo.png" alt="FREK" className="h-7 sm:h-9 w-auto relative z-10" />
                <motion.div 
                  className="absolute inset-0 bg-[#2cc4f5]/30 blur-xl rounded-full"
                  initial={{ opacity: 0 }}
                  whileHover={{ opacity: 1 }}
                />
              </motion.div>
              <span className="font-display text-xl sm:text-2xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">
                FREK
              </span>
            </Link>
            
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                to="/generate"
                className="px-4 py-2 font-mono text-[10px] sm:text-xs uppercase tracking-wider text-[#2cc4f5] hover:text-white bg-[#2cc4f5]/5 hover:bg-[#2cc4f5] border border-[#2cc4f5]/20 hover:border-[#2cc4f5] rounded-xl transition-all duration-300 hover:shadow-lg hover:shadow-[#2cc4f5]/25"
              >
                Attestation
              </Link>
            </motion.div>
          </div>
        </motion.div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 pt-28 sm:pt-32 pb-32 sm:pb-40 relative z-10">
        <div className="w-full max-w-md">
          <AnimatePresence mode="wait">
            {/* IDLE */}
            {state === 'idle' && (
              <motion.div
                key="idle"
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -40, scale: 0.95 }}
                transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                className="text-center"
              >
                {/* Titre avec reveal */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1, duration: 0.6 }}
                >
                  <h1 className="font-display text-5xl sm:text-6xl md:text-7xl tracking-wide mb-3 sm:mb-4 relative">
                    <motion.span 
                      className="bg-gradient-to-r from-[#2cc4f5] via-[#06b6d4] to-[#0ea5e9] bg-clip-text text-transparent inline-block"
                      animate={{ 
                        backgroundPosition: ['0% 50%', '100% 50%', '0% 50%']
                      }}
                      transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
                      style={{ backgroundSize: '200% 200%' }}
                    >
                      CERTIFIER
                    </motion.span>
                  </h1>
                  <motion.p 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="font-mono text-[11px] sm:text-xs text-slate-400 tracking-[0.25em] uppercase mb-12 sm:mb-16"
                  >
                    Preuve d'existence fréquentielle
                  </motion.p>
                </motion.div>

                {/* BOUTON PRINCIPAL */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2, duration: 0.8, type: "spring", bounce: 0.3 }}
                  className="relative mb-10"
                  onHoverStart={() => setIsHovering(true)}
                  onHoverEnd={() => setIsHovering(false)}
                >
                  {/* Outer glow ring */}
                  <motion.div 
                    className="absolute inset-0 flex items-center justify-center"
                    animate={{ 
                      scale: isHovering ? 1.15 : 1,
                      opacity: isHovering ? 0.4 : 0.2
                    }}
                  >
                    <div className="w-48 h-48 sm:w-56 sm:h-56 bg-[#2cc4f5]/30 rounded-full blur-3xl" />
                  </motion.div>

                  {/* Ripple effect on hover */}
                  <AnimatePresence>
                    {isHovering && (
                      <motion.div
                        initial={{ scale: 0.8, opacity: 0.5 }}
                        animate={{ scale: 1.5, opacity: 0 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 1, repeat: Infinity }}
                        className="absolute inset-0 flex items-center justify-center pointer-events-none"
                      >
                        <div className="w-40 h-40 sm:w-48 sm:h-48 border-2 border-[#2cc4f5]/30 rounded-full" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  <motion.button
                    onClick={() => fileInputRef.current?.click()}
                    whileHover={{ scale: 1.08, y: -8 }}
                    whileTap={{ scale: 0.95 }}
                    className="group relative w-40 h-40 sm:w-48 sm:h-48 mx-auto rounded-full cursor-pointer"
                    style={{
                      background: 'linear-gradient(145deg, #4dd9ff 0%, #2cc4f5 25%, #1ab3e8 50%, #0d9ed4 75%, #0889bf 100%)',
                      boxShadow: `
                        0 30px 60px -15px rgba(44, 196, 245, 0.5),
                        0 15px 30px -10px rgba(44, 196, 245, 0.4),
                        inset 0 2px 30px rgba(255,255,255,0.4),
                        inset 0 -10px 30px rgba(0,0,0,0.15)
                      `,
                    }}
                    data-testid="certify-button"
                  >
                    {/* Highlight arc */}
                    <span className="absolute top-2 left-6 right-6 h-16 sm:h-20 rounded-t-full bg-gradient-to-b from-white/50 to-transparent" />
                    
                    {/* Inner ring */}
                    <motion.span 
                      className="absolute inset-5 sm:inset-6 rounded-full border border-white/20"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                    />
                    
                    {/* Center dot with breathing */}
                    <span className="absolute inset-0 flex items-center justify-center">
                      <motion.span 
                        animate={{ 
                          scale: [1, 1.15, 1],
                          boxShadow: [
                            '0 0 20px rgba(255,255,255,0.5)',
                            '0 0 40px rgba(255,255,255,0.8)',
                            '0 0 20px rgba(255,255,255,0.5)'
                          ]
                        }}
                        transition={{ repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
                        className="w-6 h-6 sm:w-8 sm:h-8 bg-white rounded-full"
                      />
                    </span>

                    {/* Hover ring */}
                    <motion.span 
                      className="absolute inset-0 rounded-full border-2 border-white/0"
                      animate={{ borderColor: isHovering ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0)' }}
                      transition={{ duration: 0.3 }}
                    />
                  </motion.button>

                  {/* Floating particles */}
                  {isHovering && [...Array(6)].map((_, i) => (
                    <motion.div
                      key={i}
                      initial={{ 
                        opacity: 0, 
                        scale: 0,
                        x: 0,
                        y: 0
                      }}
                      animate={{ 
                        opacity: [0, 1, 0],
                        scale: [0, 1, 0.5],
                        x: Math.cos(i * 60 * Math.PI / 180) * 100,
                        y: Math.sin(i * 60 * Math.PI / 180) * 100 - 50
                      }}
                      transition={{ duration: 1.5, delay: i * 0.1, repeat: Infinity }}
                      className="absolute top-1/2 left-1/2 w-2 h-2 bg-[#2cc4f5] rounded-full pointer-events-none"
                      style={{ marginLeft: -4, marginTop: -4 }}
                    />
                  ))}
                </motion.div>

                <motion.p 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  className="font-mono text-sm text-slate-400 mb-8"
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
                  transition={{ delay: 0.6 }}
                  whileHover={{ scale: 1.05, backgroundColor: 'rgba(239, 68, 68, 0.1)' }}
                  whileTap={{ scale: 0.95 }}
                  onClick={startRecording}
                  className="group font-mono text-xs text-slate-400 hover:text-red-500 uppercase tracking-wider transition-all duration-300 flex items-center gap-3 mx-auto px-5 py-2.5 rounded-full border border-transparent hover:border-red-200"
                  data-testid="record-button"
                >
                  <motion.span 
                    animate={{ scale: [1, 1.3, 1] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                    className="w-2.5 h-2.5 bg-red-500 rounded-full shadow-lg shadow-red-500/50"
                  />
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
                <motion.div className="relative w-40 h-40 sm:w-44 sm:h-44 mx-auto mb-10">
                  {/* Multiple ripples */}
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      className="absolute inset-0 rounded-full border-2 border-red-400"
                      animate={{ scale: [1, 2], opacity: [0.5, 0] }}
                      transition={{ 
                        duration: 2, 
                        repeat: Infinity, 
                        delay: i * 0.6,
                        ease: "easeOut"
                      }}
                    />
                  ))}
                  
                  <motion.div
                    animate={{ scale: [1, 1.05, 1] }}
                    transition={{ repeat: Infinity, duration: 0.8 }}
                    className="absolute inset-0 rounded-full bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-300 shadow-2xl shadow-red-200/50 flex items-center justify-center"
                  >
                    <motion.span 
                      animate={{ scale: [1, 1.2, 1], opacity: [1, 0.7, 1] }}
                      transition={{ repeat: Infinity, duration: 0.5 }}
                      className="w-8 h-8 bg-red-500 rounded-full shadow-lg shadow-red-500/50"
                    />
                  </motion.div>
                </motion.div>

                <motion.p 
                  animate={{ opacity: [1, 0.5, 1] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  className="font-mono text-sm text-red-500 mb-8 tracking-wider"
                >
                  Capture en cours...
                </motion.p>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={stopRecording}
                  className="px-10 py-3.5 bg-gradient-to-r from-red-500 to-red-600 text-white font-mono text-xs uppercase tracking-wider rounded-xl hover:from-red-600 hover:to-red-700 transition-all shadow-xl shadow-red-500/30"
                  data-testid="stop-recording-button"
                >
                  Terminer
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
                {/* Status message */}
                <motion.p
                  key={getProgressMessage()}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="font-mono text-sm text-[#2cc4f5] mb-8 tracking-wider"
                >
                  {getProgressMessage()}
                </motion.p>

                {/* Progress bar */}
                <div className="relative mb-6">
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden shadow-inner">
                    <motion.div
                      className="h-full rounded-full relative overflow-hidden"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.3, ease: "easeOut" }}
                      style={{ 
                        background: 'linear-gradient(90deg, #2cc4f5 0%, #06b6d4 50%, #0ea5e9 100%)',
                      }}
                    >
                      {/* Shimmer effect */}
                      <motion.div
                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent"
                        animate={{ x: ['-100%', '100%'] }}
                        transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                      />
                    </motion.div>
                  </div>
                  
                  {/* Glow under progress */}
                  <motion.div 
                    className="absolute -bottom-2 left-0 h-4 bg-[#2cc4f5]/30 blur-xl rounded-full"
                    animate={{ width: `${progress}%` }}
                  />
                </div>

                <motion.div 
                  className="font-mono text-2xl text-[#2cc4f5] font-bold mb-10"
                  key={Math.round(progress)}
                  initial={{ scale: 1.2 }}
                  animate={{ scale: 1 }}
                >
                  {Math.round(progress)}%
                </motion.div>

                {/* Spinner */}
                <div className="relative w-16 h-16 mx-auto">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                    className="absolute inset-0 rounded-full border-3 border-slate-100 border-t-[#2cc4f5]"
                  />
                  <motion.div
                    animate={{ rotate: -360 }}
                    transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                    className="absolute inset-2 rounded-full border-2 border-slate-50 border-b-[#06b6d4]"
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
                {/* Success animation */}
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: "spring", duration: 0.8, bounce: 0.4 }}
                  className="relative w-24 h-24 mx-auto mb-8"
                >
                  {/* Success rings */}
                  <motion.div
                    initial={{ scale: 0, opacity: 1 }}
                    animate={{ scale: 2, opacity: 0 }}
                    transition={{ duration: 1, delay: 0.3 }}
                    className="absolute inset-0 rounded-full border-2 border-[#2cc4f5]"
                  />
                  
                  <div className="absolute inset-0 rounded-full bg-gradient-to-br from-[#2cc4f5]/20 to-[#06b6d4]/10 border-2 border-[#2cc4f5] flex items-center justify-center shadow-xl shadow-[#2cc4f5]/20">
                    <motion.svg 
                      className="w-12 h-12 text-[#2cc4f5]" 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                      initial={{ pathLength: 0 }}
                      animate={{ pathLength: 1 }}
                      transition={{ duration: 0.5, delay: 0.3 }}
                    >
                      <motion.path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2.5} 
                        d="M5 13l4 4L19 7"
                        initial={{ pathLength: 0 }}
                        animate={{ pathLength: 1 }}
                        transition={{ duration: 0.5, delay: 0.3 }}
                      />
                    </motion.svg>
                  </div>
                </motion.div>

                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  className="font-mono text-sm text-slate-500 mb-6"
                >
                  Certification réussie
                </motion.p>

                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                  className="mb-6"
                >
                  <div className="font-mono text-[10px] text-slate-400 uppercase tracking-[0.2em] mb-3">
                    Votre FREK-ID
                  </div>
                  <motion.div 
                    className="font-mono text-sm text-[#0ea5e9] break-all px-6 py-4 bg-white rounded-2xl border border-slate-100 shadow-lg shadow-slate-200/50"
                    data-testid="frek-id"
                    whileHover={{ scale: 1.02 }}
                  >
                    {frekId}
                  </motion.div>
                </motion.div>

                {/* QR Code */}
                <motion.div 
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.7, type: "spring" }}
                  className="inline-block p-6 bg-white rounded-3xl mb-10 shadow-xl shadow-slate-200/50 border border-slate-100"
                  whileHover={{ scale: 1.03, boxShadow: '0 25px 50px -12px rgba(0,0,0,0.15)' }}
                >
                  <QRCodeSVG
                    value={`${window.location.origin}/verify/${frekId}`}
                    size={160}
                    level="M"
                    fgColor="#0ea5e9"
                    data-testid="qr-code"
                  />
                </motion.div>

                {/* Actions */}
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.8 }}
                  className="flex gap-4 justify-center"
                >
                  <motion.button
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => {
                      navigator.clipboard.writeText(frekId);
                    }}
                    className="px-6 py-3 border border-slate-200 text-slate-500 font-mono text-xs uppercase tracking-wider hover:border-[#2cc4f5] hover:text-[#2cc4f5] rounded-xl transition-all shadow-sm hover:shadow-lg hover:shadow-[#2cc4f5]/10"
                    data-testid="copy-button"
                  >
                    Copier l'ID
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={reset}
                    className="px-6 py-3 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white font-mono text-xs uppercase tracking-wider rounded-xl transition-all font-semibold shadow-lg shadow-[#2cc4f5]/30 hover:shadow-xl hover:shadow-[#2cc4f5]/40"
                    data-testid="new-certification-button"
                  >
                    Nouvelle certification
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
                <motion.div
                  animate={{ x: [-5, 5, -5, 5, 0] }}
                  transition={{ duration: 0.5 }}
                  className="w-24 h-24 mx-auto mb-8 rounded-full bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-300 flex items-center justify-center shadow-xl shadow-red-200/30"
                >
                  <svg className="w-12 h-12 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </motion.div>

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
          <div className="flex flex-wrap justify-center gap-6 sm:gap-8 mb-5">
            <motion.div whileHover={{ y: -2 }}>
              <Link to="/philosophy" className="font-mono text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors duration-300">
                Philosophie
              </Link>
            </motion.div>
            <motion.div whileHover={{ y: -2 }}>
              <Link to="/spec" className="font-mono text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors duration-300">
                Spécifications
              </Link>
            </motion.div>
            <motion.div whileHover={{ y: -2 }}>
              <Link to="/help" className="font-mono text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors duration-300">
                Aide
              </Link>
            </motion.div>
            <motion.div whileHover={{ y: -2 }}>
              <a href="https://frekcore.com" target="_blank" rel="noopener noreferrer" className="font-mono text-xs text-slate-400 hover:text-[#2cc4f5] uppercase tracking-wider transition-colors duration-300">
                frekcore.com
              </a>
            </motion.div>
          </div>

          <div className="w-24 h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent mx-auto mb-5" />

          <div className="flex flex-wrap justify-center gap-4 sm:gap-6 mb-6">
            {[
              { label: 'Cadre juridique', path: '/legal' },
              { label: 'Confidentialité', path: '/privacy' },
              { label: 'Cookies', path: '/cookies' },
              { label: 'Conditions', path: '/terms' },
              { label: 'Mentions légales', path: '/imprint' },
            ].map((item) => (
              <Link 
                key={item.path}
                to={item.path} 
                className="font-mono text-[10px] text-slate-300 hover:text-[#2cc4f5] transition-colors"
              >
                {item.label}
              </Link>
            ))}
          </div>
          
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
