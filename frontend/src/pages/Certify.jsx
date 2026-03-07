/**
 * FREK v2 — NODE 11 · EXPERIENCE
 * ================================
 * 3% visible. 97% invisible. Une seule action.
 * 
 * La confiance ne vient pas de ce qu'on montre.
 * Elle vient de ce qu'on ne montre pas.
 * 
 * Comme une luciole — elle ne sait pas comment
 * fonctionne la luciferase. Elle s'allume. C'est tout.
 */
import { useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { QRCodeSVG } from 'qrcode.react';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

// Les 17 opérations invisibles
const INVISIBLE_OPERATIONS = [
  "Capture du signal audio brut",
  "Extraction FFT 512 bandes fréquentielles",
  "Calcul RMS + ZCR",
  "Extraction MFCC 13 coefficients",
  "Calcul centroïde spectral",
  "Calcul flux spectral",
  "Construction vecteur 528D",
  "SHA-256 signal",
  "SHA-256 metadata",
  "Hash chaîné avec FREK-ID précédent",
  "Comparaison base vectorielle",
  "Détection similarités",
  "Positionnement graphe relationnel",
  "Mise à jour réseau lucioles",
  "Génération certificat",
  "Archivage distribué",
  "Synchronisation observatoire"
];

export function Certify() {
  const [state, setState] = useState('idle'); // idle, recording, processing, complete, error
  const [audioFile, setAudioFile] = useState(null);
  const [frekId, setFrekId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [currentOperation, setCurrentOperation] = useState(0);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Simuler la progression des 17 opérations
  const simulateProgress = useCallback(() => {
    let op = 0;
    const interval = setInterval(() => {
      op++;
      setCurrentOperation(op);
      setProgress((op / INVISIBLE_OPERATIONS.length) * 100);
      if (op >= INVISIBLE_OPERATIONS.length) {
        clearInterval(interval);
      }
    }, 150);
    return interval;
  }, []);

  // Certifier via l'API backend
  const certifyAudio = async (audioBlob) => {
    setState('processing');
    setError(null);
    setCurrentOperation(0);
    setProgress(0);

    // Démarrer la simulation de progression
    const progressInterval = simulateProgress();

    try {
      // Convertir en base64
      const reader = new FileReader();
      const base64Promise = new Promise((resolve, reject) => {
        reader.onload = () => {
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        };
        reader.onerror = reject;
      });
      reader.readAsDataURL(audioBlob);
      const audioBase64 = await base64Promise;

      // Appeler l'API FREK
      const response = await fetch(`${API_URL}/api/frek/certify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          audio_base64: audioBase64,
          artiste_id: `ARTISTE-${Date.now().toString(36).toUpperCase()}`,
        }),
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Attendre que la progression soit complète
      clearInterval(progressInterval);
      setProgress(100);
      setCurrentOperation(INVISIBLE_OPERATIONS.length);

      // Petit délai pour montrer 100%
      await new Promise(r => setTimeout(r, 300));

      setFrekId(data.frek_id);
      setResult(data);
      setState('complete');

    } catch (err) {
      clearInterval(progressInterval);
      console.error('Certification error:', err);
      setError(err.message || 'Erreur lors de la certification');
      setState('error');
    }
  };

  // Gestion du fichier uploadé
  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioFile(file);
      certifyAudio(file);
    }
  };

  // Démarrer l'enregistrement
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
        setAudioFile(audioBlob);
        certifyAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setState('recording');
    } catch (err) {
      console.error('Recording error:', err);
      setError('Impossible d\'accéder au microphone');
      setState('error');
    }
  };

  // Arrêter l'enregistrement
  const stopRecording = () => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  };

  // Reset
  const reset = () => {
    setState('idle');
    setAudioFile(null);
    setFrekId(null);
    setResult(null);
    setError(null);
    setCurrentOperation(0);
    setProgress(0);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col">
      {/* Header minimal */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/95 backdrop-blur-md border-b border-[#c26e3f]/10">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <img src="/frek-logo.png" alt="FREK" className="h-6 w-auto opacity-80" />
          </Link>
          <span className="font-mono text-[10px] text-white/30 uppercase tracking-[0.3em]">
            NODE 11 · EXPERIENCE
          </span>
        </div>
      </header>

      {/* Contenu principal */}
      <main className="flex-1 flex items-center justify-center px-6 pt-14">
        <div className="w-full max-w-md">
          <AnimatePresence mode="wait">
            {/* État IDLE - Bouton principal */}
            {state === 'idle' && (
              <motion.div
                key="idle"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="text-center"
              >
                {/* Iceberg visuel */}
                <div className="mb-16">
                  <div className="font-mono text-[10px] text-white/20 uppercase tracking-[0.5em] mb-2">
                    3% visible
                  </div>
                  <div className="w-24 h-1 bg-[#c26e3f] mx-auto mb-4" />
                  <div className="font-mono text-[10px] text-white/10 uppercase tracking-[0.3em]">
                    97% invisible
                  </div>
                </div>

                {/* LE BOUTON - L'unique action */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="group relative w-32 h-32 mx-auto mb-8 rounded-full bg-[#c26e3f] hover:bg-[#d47f4f] transition-all duration-500 hover:scale-105 hover:shadow-[0_0_60px_rgba(194,110,63,0.4)]"
                  data-testid="certify-button"
                >
                  <span className="absolute inset-0 flex items-center justify-center">
                    <span className="w-4 h-4 bg-white rounded-full group-hover:scale-110 transition-transform" />
                  </span>
                </button>

                <p className="font-mono text-xs text-white/40 mb-4">
                  Appuyez pour certifier
                </p>

                {/* Input fichier caché */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  data-testid="file-input"
                />

                {/* Alternative : enregistrer */}
                <button
                  onClick={startRecording}
                  className="font-mono text-[10px] text-white/20 hover:text-white/40 uppercase tracking-wider transition-colors"
                  data-testid="record-button"
                >
                  ou enregistrer →
                </button>
              </motion.div>
            )}

            {/* État RECORDING */}
            {state === 'recording' && (
              <motion.div
                key="recording"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                <div className="mb-8">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                    className="w-24 h-24 mx-auto rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center"
                  >
                    <span className="w-4 h-4 bg-red-500 rounded-full animate-pulse" />
                  </motion.div>
                </div>

                <p className="font-mono text-xs text-white/60 mb-8">
                  Enregistrement en cours...
                </p>

                <button
                  onClick={stopRecording}
                  className="px-8 py-3 bg-red-500 text-white font-mono text-xs uppercase tracking-wider hover:bg-red-600 transition-colors"
                  data-testid="stop-recording-button"
                >
                  Arrêter et certifier
                </button>
              </motion.div>
            )}

            {/* État PROCESSING - Barre de progression */}
            {state === 'processing' && (
              <motion.div
                key="processing"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                <div className="mb-8">
                  <div className="font-mono text-[10px] text-white/30 uppercase tracking-[0.3em] mb-4">
                    {INVISIBLE_OPERATIONS[Math.min(currentOperation, INVISIBLE_OPERATIONS.length - 1)]}
                  </div>
                  
                  {/* Barre de progression */}
                  <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden mb-4">
                    <motion.div
                      className="h-full bg-[#c26e3f]"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.1 }}
                    />
                  </div>

                  <div className="font-mono text-xs text-white/40">
                    {currentOperation} / {INVISIBLE_OPERATIONS.length}
                  </div>
                </div>

                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                  className="w-16 h-16 mx-auto border-2 border-[#c26e3f]/30 border-t-[#c26e3f] rounded-full"
                />
              </motion.div>
            )}

            {/* État COMPLETE - FREK-ID + QR */}
            {state === 'complete' && frekId && (
              <motion.div
                key="complete"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                {/* Animation de succès */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", duration: 0.5 }}
                  className="w-20 h-20 mx-auto mb-8 rounded-full bg-green-500/20 border-2 border-green-500 flex items-center justify-center"
                >
                  <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </motion.div>

                <div className="mb-6">
                  <div className="font-mono text-[10px] text-white/30 uppercase tracking-[0.3em] mb-2">
                    FREK-ID
                  </div>
                  <div 
                    className="font-mono text-sm text-[#c26e3f] break-all px-4"
                    data-testid="frek-id"
                  >
                    {frekId}
                  </div>
                </div>

                {/* QR Code */}
                <div className="inline-block p-4 bg-white rounded-lg mb-8">
                  <QRCodeSVG
                    value={`${window.location.origin}/verify/${frekId}`}
                    size={160}
                    level="M"
                    data-testid="qr-code"
                  />
                </div>

                {/* Détails (accordéon collapsed) */}
                <details className="text-left mb-8 bg-white/5 rounded-lg overflow-hidden">
                  <summary className="px-4 py-3 cursor-pointer font-mono text-[10px] text-white/40 uppercase tracking-wider hover:text-white/60 transition-colors">
                    Voir les détails techniques
                  </summary>
                  <div className="px-4 pb-4 space-y-2 font-mono text-[10px] text-white/30">
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
                    {result?.resonance && (
                      <div>Matches: {result.resonance.match_count}</div>
                    )}
                    <div>Temps: {result?.processing_time_ms}ms</div>
                  </div>
                </details>

                {/* Actions */}
                <div className="flex gap-4 justify-center">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(frekId);
                    }}
                    className="px-6 py-3 border border-white/20 text-white/60 font-mono text-[10px] uppercase tracking-wider hover:border-white/40 hover:text-white/80 transition-colors"
                    data-testid="copy-button"
                  >
                    Copier
                  </button>
                  <button
                    onClick={reset}
                    className="px-6 py-3 bg-[#c26e3f] text-white font-mono text-[10px] uppercase tracking-wider hover:bg-[#d47f4f] transition-colors"
                    data-testid="new-certification-button"
                  >
                    Nouvelle certification
                  </button>
                </div>
              </motion.div>
            )}

            {/* État ERROR */}
            {state === 'error' && (
              <motion.div
                key="error"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                <div className="w-20 h-20 mx-auto mb-8 rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center">
                  <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>

                <p className="font-mono text-xs text-red-400 mb-8">
                  {error}
                </p>

                <button
                  onClick={reset}
                  className="px-8 py-3 border border-red-500/30 text-red-400 font-mono text-[10px] uppercase tracking-wider hover:border-red-500/50 transition-colors"
                  data-testid="retry-button"
                >
                  Réessayer
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer minimal */}
      <footer className="py-8 text-center">
        <p className="font-mono text-[10px] text-white/10 uppercase tracking-[0.3em]">
          Comme une luciole — elle s'allume. C'est tout.
        </p>
      </footer>
    </div>
  );
}

export default Certify;
