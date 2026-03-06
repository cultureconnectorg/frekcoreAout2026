import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useAudioFingerprint } from '../../hooks/useAudioFingerprint';

export function Step3Fingerprint({ state, setFingerprint, setAudioFile }) {
  const [mode, setMode] = useState('audio');
  const [manualHash, setManualHash] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  
  const { analyzeAudio, isProcessing, progress, result, error, reset } = useAudioFingerprint();

  const handleFileDrop = useCallback(async (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer?.files[0];
    if (file && file.type.startsWith('audio/')) {
      await processAudioFile(file);
    }
  }, []);

  const handleFileSelect = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (file) {
      await processAudioFile(file);
    }
  }, []);

  const processAudioFile = async (file) => {
    setAudioFile(file);
    try {
      const analysisResult = await analyzeAudio(file);
      if (analysisResult) {
        setFingerprint({
          method: 'sha256-fft-rms-zcr',
          value: analysisResult.fingerprint.replace('frek:fp:', ''),
          algorithm: 'Web Audio API FFT-2048 + RMS + ZCR → SHA-256',
          sample_rate: analysisResult.sampleRate,
          fft_size: 2048,
          duration: analysisResult.duration,
        });
      }
    } catch (err) {
      console.error('Audio analysis failed:', err);
    }
  };

  const handleManualSubmit = () => {
    if (manualHash.trim().length === 64) {
      setFingerprint({
        method: 'sha256-raw',
        value: manualHash.trim(),
        algorithm: 'Manual entry',
        sample_rate: 44100,
        fft_size: 2048,
        duration: 0,
      });
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-display text-2xl text-fwhite mb-2">Empreinte audio</h3>
        <p className="font-body text-mid text-sm">
          L&apos;empreinte audio est le cœur de l&apos;attestation FREK. Elle permet de vérifier l&apos;authenticité du mix.
        </p>
      </div>

      {/* Mode Tabs */}
      <div className="flex border-b border-[#333]">
        <button
          onClick={() => setMode('audio')}
          className={`px-6 py-3 font-mono text-sm transition-colors ${
            mode === 'audio'
              ? 'text-terra border-b-2 border-terra bg-terra/5'
              : 'text-dim hover:text-mid'
          }`}
        >
          🎵 Fichier audio
        </button>
        <button
          onClick={() => setMode('manual')}
          className={`px-6 py-3 font-mono text-sm transition-colors ${
            mode === 'manual'
              ? 'text-terra border-b-2 border-terra bg-terra/5'
              : 'text-dim hover:text-mid'
          }`}
        >
          ✏️ Saisie manuelle
        </button>
      </div>

      {/* Audio Mode */}
      {mode === 'audio' && (
        <div className="space-y-6">
          {/* Drop Zone */}
          <label
            className={`
              block p-12 border-2 border-dashed cursor-pointer transition-all text-center
              ${isDragging
                ? 'border-terra bg-terra/10'
                : 'border-terra/30 hover:border-terra/50 hover:bg-terra/5'
              }
            `}
            onDrop={handleFileDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <input
              type="file"
              accept="audio/*,.mp3,.wav,.flac,.aac,.ogg,.m4a"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div>
              <p className="font-display text-2xl text-fwhite mb-2">
                Déposer votre fichier audio
              </p>
              <p className="font-mono text-xs text-dim">
                MP3, WAV, FLAC, AAC, OGG — Max 500MB — Analyse FFT locale
              </p>
            </div>
          </label>

          {/* Processing Progress */}
          {isProcessing && (
            <div className="p-6 bg-[#0a0a0a] border border-terra/20">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs text-mid">Analyse en cours...</span>
                <span className="font-mono text-xs text-terra">{progress}%</span>
              </div>
              <div className="h-2 bg-dark rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-terra to-gold"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>
          )}

          {/* Analysis Result */}
          {result && !isProcessing && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="border border-fgreen/30 bg-fgreen/5"
            >
              <div className="px-6 py-3 bg-fgreen/20 border-b border-fgreen/30">
                <span className="font-mono text-sm text-[#5DC882]">
                  ✓ EMPREINTE GÉNÉRÉE
                </span>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="font-mono text-xs text-dim">Fichier</p>
                    <p className="font-body text-sm text-light truncate">{result.filename}</p>
                  </div>
                  <div>
                    <p className="font-mono text-xs text-dim">Durée</p>
                    <p className="font-body text-sm text-light">{result.duration.toFixed(2)}s</p>
                  </div>
                  <div>
                    <p className="font-mono text-xs text-dim">Segments</p>
                    <p className="font-body text-sm text-light">{result.segments}</p>
                  </div>
                  <div>
                    <p className="font-mono text-xs text-dim">Sample Rate</p>
                    <p className="font-body text-sm text-light">{result.sampleRate} Hz</p>
                  </div>
                </div>
                <div>
                  <p className="font-mono text-xs text-dim mb-2">Fingerprint</p>
                  <p className="font-mono text-xs text-terra bg-dark p-4 break-all">
                    {result.fingerprint}
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Error */}
          {error && (
            <div className="p-4 border border-red-500/30 bg-red-500/5">
              <p className="font-mono text-sm text-red-400">{error}</p>
            </div>
          )}
        </div>
      )}

      {/* Manual Mode */}
      {mode === 'manual' && (
        <div className="space-y-6">
          {/* Warning */}
          <div className="p-4 bg-gold/10 border border-gold/30">
            <p className="font-mono text-sm text-gold">
              ⚠️ Sans fichier audio, la valeur probatoire est réduite. Vous pouvez compléter cette attestation plus tard.
            </p>
          </div>

          <div>
            <label className="block font-mono text-xs text-mid mb-2">
              Hash SHA-256 existant
            </label>
            <input
              type="text"
              value={manualHash}
              onChange={(e) => setManualHash(e.target.value)}
              placeholder="a3f8c2d1e4b7f9a0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4"
              className="w-full px-4 py-3 bg-[#111] border border-[#333] font-mono text-light text-sm focus:outline-none focus:border-terra transition-colors"
            />
            <p className="mt-2 font-mono text-xs text-dim">
              64 caractères hexadécimaux (a-f, 0-9)
            </p>
          </div>

          <button
            onClick={handleManualSubmit}
            disabled={manualHash.trim().length !== 64}
            className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Valider l&apos;empreinte manuelle
          </button>

          {/* Manual fingerprint confirmed */}
          {state.audioFingerprint.method === 'sha256-raw' && state.audioFingerprint.value && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="p-4 border border-gold/30 bg-gold/5"
            >
              <p className="font-mono text-xs text-gold mb-2">✓ Empreinte manuelle enregistrée</p>
              <p className="font-mono text-xs text-mid break-all">
                {state.audioFingerprint.value}
              </p>
            </motion.div>
          )}
        </div>
      )}

      {/* Current State Display */}
      {state.audioFingerprint.value && state.audioFingerprint.method === 'sha256-fft-rms-zcr' && (
        <div className="p-4 bg-fgreen/10 border border-fgreen/30">
          <p className="font-mono text-xs text-[#5DC882]">
            ✓ Empreinte audio prête — Méthode: {state.audioFingerprint.method}
          </p>
        </div>
      )}
    </div>
  );
}

export default Step3Fingerprint;
