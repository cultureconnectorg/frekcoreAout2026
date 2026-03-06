import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RevealWrapper } from '../ui/RevealWrapper';
import { SectionTag } from '../ui/SectionTag';
import { useAudioFingerprint } from '../../hooks/useAudioFingerprint';
import { useJsonVerify } from '../../hooks/useJsonVerify';

export function Verifier() {
  const [activeTab, setActiveTab] = useState('audio');
  const [isDragging, setIsDragging] = useState(false);
  const [jsonText, setJsonText] = useState('');

  const { analyzeAudio, isProcessing, progress, result: audioResult, error: audioError, reset: resetAudio } = useAudioFingerprint();
  const { verifyJson, isVerifying, result: jsonResult, error: jsonError, reset: resetJson } = useJsonVerify();

  // Audio drop handlers
  const handleAudioDrop = useCallback(
    async (e) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer?.files[0];
      if (file && file.type.startsWith('audio/')) {
        await analyzeAudio(file);
      }
    },
    [analyzeAudio]
  );

  const handleAudioFileSelect = useCallback(
    async (e) => {
      const file = e.target.files?.[0];
      if (file) {
        await analyzeAudio(file);
      }
    },
    [analyzeAudio]
  );

  // JSON drop handlers
  const handleJsonDrop = useCallback(
    async (e) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer?.files[0];
      if (file && file.name.endsWith('.json')) {
        const text = await file.text();
        setJsonText(text);
        await verifyJson(text);
      }
    },
    [verifyJson]
  );

  const handleJsonFileSelect = useCallback(
    async (e) => {
      const file = e.target.files?.[0];
      if (file) {
        const text = await file.text();
        setJsonText(text);
        await verifyJson(text);
      }
    },
    [verifyJson]
  );

  const handleJsonTextVerify = useCallback(async () => {
    if (jsonText.trim()) {
      await verifyJson(jsonText);
    }
  }, [jsonText, verifyJson]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <section id="verifier" className="py-24 px-6 bg-navy/30">
      <div className="max-w-4xl mx-auto">
        <RevealWrapper>
          <SectionTag>Vérification publique · 100% locale</SectionTag>
          <h2 className="font-display text-5xl md:text-6xl text-fwhite mb-4">
            Vérifier une attestation
          </h2>
          <p className="font-body text-lg text-mid mb-12">
            Aucune donnée envoyée. Vérification cryptographique dans votre navigateur.
            Zéro compte requis.
          </p>
        </RevealWrapper>

        {/* Tabs */}
        <RevealWrapper delay={0.1}>
          <div className="flex border-b border-terra/20 mb-8">
            <button
              onClick={() => {
                setActiveTab('audio');
                resetJson();
              }}
              className={`px-6 py-4 font-mono text-sm transition-all ${
                activeTab === 'audio'
                  ? 'text-fwhite border-b-2 border-terra bg-terra/5'
                  : 'text-dim hover:text-mid'
              }`}
            >
              🎵 Fichier Audio
            </button>
            <button
              onClick={() => {
                setActiveTab('json');
                resetAudio();
              }}
              className={`px-6 py-4 font-mono text-sm transition-all ${
                activeTab === 'json'
                  ? 'text-fwhite border-b-2 border-terra bg-terra/5'
                  : 'text-dim hover:text-mid'
              }`}
            >
              📄 Attestation JSON
            </button>
          </div>
        </RevealWrapper>

        <AnimatePresence mode="wait">
          {/* Audio Panel */}
          {activeTab === 'audio' && (
            <motion.div
              key="audio"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {/* Drop Zone */}
              <label
                className={`block p-16 border-2 border-dashed cursor-pointer transition-all ${
                  isDragging
                    ? 'border-terra bg-terra/10'
                    : 'border-terra/30 hover:border-terra/50 hover:bg-terra/5'
                }`}
                onDrop={handleAudioDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                <input
                  type="file"
                  accept="audio/*"
                  onChange={handleAudioFileSelect}
                  className="hidden"
                />
                <div className="text-center">
                  <p className="font-display text-2xl text-fwhite mb-2">
                    Déposer votre fichier audio
                  </p>
                  <p className="font-mono text-xs text-dim">
                    MP3, WAV, FLAC, AIFF — Analyse FFT locale
                  </p>
                </div>
              </label>

              {/* Progress Bar */}
              {isProcessing && (
                <div className="mt-6">
                  <div className="h-2 bg-dark rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-terra to-gold"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  <p className="font-mono text-xs text-dim mt-2 text-center">
                    Analyse en cours... {progress}%
                  </p>
                </div>
              )}

              {/* Audio Result */}
              {audioResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 border border-fgreen/30 bg-fgreen/5"
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
                        <p className="font-body text-sm text-light truncate">{audioResult.filename}</p>
                      </div>
                      <div>
                        <p className="font-mono text-xs text-dim">Durée</p>
                        <p className="font-body text-sm text-light">{audioResult.duration.toFixed(2)}s</p>
                      </div>
                      <div>
                        <p className="font-mono text-xs text-dim">Segments</p>
                        <p className="font-body text-sm text-light">{audioResult.segments}</p>
                      </div>
                      <div>
                        <p className="font-mono text-xs text-dim">Sample Rate</p>
                        <p className="font-body text-sm text-light">{audioResult.sampleRate} Hz</p>
                      </div>
                    </div>
                    <div>
                      <p className="font-mono text-xs text-dim mb-1">Fingerprint</p>
                      <p className="font-mono text-xs text-terra break-all bg-dark p-3">
                        {audioResult.fingerprint}
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}

              {audioError && (
                <div className="mt-6 p-4 border border-red-500/30 bg-red-500/5">
                  <p className="font-mono text-sm text-red-400">{audioError}</p>
                </div>
              )}
            </motion.div>
          )}

          {/* JSON Panel */}
          {activeTab === 'json' && (
            <motion.div
              key="json"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {/* Drop Zone */}
              <label
                className={`block p-12 border-2 border-dashed cursor-pointer transition-all mb-4 ${
                  isDragging
                    ? 'border-terra bg-terra/10'
                    : 'border-terra/30 hover:border-terra/50 hover:bg-terra/5'
                }`}
                onDrop={handleJsonDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                <input
                  type="file"
                  accept=".json"
                  onChange={handleJsonFileSelect}
                  className="hidden"
                />
                <div className="text-center">
                  <p className="font-display text-xl text-fwhite mb-2">
                    Déposer votre .frek.json
                  </p>
                  <p className="font-mono text-xs text-dim">
                    Vérification de la signature Ed25519
                  </p>
                </div>
              </label>

              {/* Or paste */}
              <div className="mb-4">
                <p className="font-mono text-xs text-dim mb-2">Ou collez le contenu JSON :</p>
                <textarea
                  value={jsonText}
                  onChange={(e) => setJsonText(e.target.value)}
                  placeholder='{"frek_version":"0.4","mix_id":"FREK-2026-MQ-001",...}'
                  className="w-full h-32 p-4 bg-dark border border-terra/20 font-mono text-xs text-light resize-none focus:outline-none focus:border-terra"
                />
              </div>

              <button
                onClick={handleJsonTextVerify}
                disabled={isVerifying || !jsonText.trim()}
                className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isVerifying ? 'Vérification...' : "Vérifier l'attestation"}
              </button>

              {/* JSON Result */}
              {jsonResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`mt-6 border ${
                    jsonResult.isValid
                      ? 'border-fgreen/30 bg-fgreen/5'
                      : 'border-red-500/30 bg-red-500/5'
                  }`}
                >
                  <div
                    className={`px-6 py-3 border-b ${
                      jsonResult.isValid
                        ? 'bg-fgreen/20 border-fgreen/30'
                        : 'bg-red-500/20 border-red-500/30'
                    }`}
                  >
                    <span
                      className={`font-mono text-sm ${
                        jsonResult.isValid ? 'text-[#5DC882]' : 'text-red-400'
                      }`}
                    >
                      {jsonResult.isValid ? '✓ ATTESTATION VALIDE' : '✗ ATTESTATION INVALIDE'}
                    </span>
                  </div>
                  <div className="p-6">
                    {jsonResult.summary && (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                        <div>
                          <p className="font-mono text-xs text-dim">FREK-ID</p>
                          <p className="font-body text-sm text-light">{jsonResult.summary.mixId}</p>
                        </div>
                        <div>
                          <p className="font-mono text-xs text-dim">Artiste</p>
                          <p className="font-body text-sm text-light">{jsonResult.summary.artist}</p>
                        </div>
                        <div>
                          <p className="font-mono text-xs text-dim">Événement</p>
                          <p className="font-body text-sm text-light">{jsonResult.summary.event}</p>
                        </div>
                        <div>
                          <p className="font-mono text-xs text-dim">Date</p>
                          <p className="font-body text-sm text-light">{jsonResult.summary.date}</p>
                        </div>
                        <div>
                          <p className="font-mono text-xs text-dim">Tracks</p>
                          <p className="font-body text-sm text-light">{jsonResult.summary.tracksCount}</p>
                        </div>
                        <div>
                          <p className="font-mono text-xs text-dim">Niveau</p>
                          <p className="font-body text-sm text-light capitalize">{jsonResult.proofLevel}</p>
                        </div>
                      </div>
                    )}

                    {/* Checks */}
                    <div className="flex flex-wrap gap-2">
                      {jsonResult.checks.map((check) => (
                        <span
                          key={check.label}
                          className={`px-3 py-1 font-mono text-xs border ${
                            check.ok
                              ? 'bg-fgreen/10 border-fgreen/30 text-[#5DC882]'
                              : check.warn
                              ? 'bg-gold/10 border-gold/30 text-gold'
                              : 'bg-red-500/10 border-red-500/30 text-red-400'
                          }`}
                        >
                          {check.ok ? '✓' : check.warn ? '⚠' : '✗'} {check.label}
                        </span>
                      ))}
                    </div>

                    {jsonResult.missing.length > 0 && (
                      <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20">
                        <p className="font-mono text-xs text-red-400">
                          Champs manquants : {jsonResult.missing.join(', ')}
                        </p>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}

              {jsonError && (
                <div className="mt-6 p-4 border border-red-500/30 bg-red-500/5">
                  <p className="font-mono text-sm text-red-400">{jsonError}</p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}

export default Verifier;
