import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { generateFrekJson, downloadFrekJson, copyFrekJson, validateWizardState } from '../../utils/frek-generator';
import { FrekJsonPreview } from './FrekJsonPreview';

export function Step4Review({
  state,
  setMixId,
  setCreatedAt,
  setSignature,
  setGenerating,
  setComplete,
}) {
  const [generatedDoc, setGeneratedDoc] = useState(null);
  const [copied, setCopied] = useState(false);
  const [downloaded, setDownloaded] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});

  // Validate on mount
  useEffect(() => {
    const validation = validateWizardState(state);
    setValidationErrors(validation.errors);
  }, [state]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const result = await generateFrekJson(state);
      setGeneratedDoc(result.document);
      setMixId(result.mixId);
      setCreatedAt(result.createdAt);
      setSignature({ value: result.signatureValue });
      setComplete(true);
    } catch (err) {
      console.error('Generation failed:', err);
    }
    setGenerating(false);
  };

  const handleDownload = () => {
    if (generatedDoc) {
      downloadFrekJson(generatedDoc, `${generatedDoc.mix_id}.frek.json`);
      setDownloaded(true);
    }
  };

  const handleCopy = async () => {
    if (generatedDoc) {
      const success = await copyFrekJson(generatedDoc);
      if (success) {
        setCopied(true);
        setTimeout(() => setCopied(false), 3000);
      }
    }
  };

  const hasErrors = Object.keys(validationErrors).filter(k => !k.includes('Warning')).length > 0;

  return (
    <div className="space-y-8">
      <div>
        <h3 className="font-display text-2xl text-fwhite mb-2">Revue & Génération</h3>
        <p className="font-body text-mid text-sm">
          Vérifiez les informations avant de générer votre attestation FREK.
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Artist */}
        <div className="p-6 bg-[#0a0a0a] border border-[#222]">
          <h4 className="font-mono text-xs text-terra uppercase tracking-wider mb-4">Artiste</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="font-mono text-xs text-dim">Nom de scène</span>
              <span className="font-body text-sm text-light">{state.artist.name || '—'}</span>
            </div>
            {state.artist.legal_name && (
              <div className="flex justify-between">
                <span className="font-mono text-xs text-dim">Nom légal</span>
                <span className="font-body text-sm text-light">{state.artist.legal_name}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="font-mono text-xs text-dim">Territoire</span>
              <span className="font-body text-sm text-light">{state.artist.territory}</span>
            </div>
          </div>
        </div>

        {/* Event */}
        <div className="p-6 bg-[#0a0a0a] border border-[#222]">
          <h4 className="font-mono text-xs text-terra uppercase tracking-wider mb-4">Événement</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="font-mono text-xs text-dim">Nom</span>
              <span className="font-body text-sm text-light truncate ml-4">{state.event.name || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-mono text-xs text-dim">Date</span>
              <span className="font-body text-sm text-light">{state.event.date}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-mono text-xs text-dim">Contexte</span>
              <span className="font-body text-sm text-light">{state.event.context}</span>
            </div>
            {state.event.venue && (
              <div className="flex justify-between">
                <span className="font-mono text-xs text-dim">Lieu</span>
                <span className="font-body text-sm text-light">{state.event.venue}</span>
              </div>
            )}
          </div>
        </div>

        {/* Tracklist */}
        <div className="p-6 bg-[#0a0a0a] border border-[#222]">
          <h4 className="font-mono text-xs text-terra uppercase tracking-wider mb-4">Tracklist</h4>
          {state.tracklist.length > 0 ? (
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {state.tracklist.map((track) => (
                <div key={track.position} className="font-mono text-xs text-mid">
                  {track.position}. {track.title || 'Sans titre'} — {track.artist || 'Artiste inconnu'}
                </div>
              ))}
            </div>
          ) : (
            <p className="font-mono text-xs text-dim">Aucune tracklist</p>
          )}
          <p className="mt-2 font-mono text-xs text-dim">
            {state.tracklist.length} titre{state.tracklist.length !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Fingerprint */}
        <div className="p-6 bg-[#0a0a0a] border border-[#222]">
          <h4 className="font-mono text-xs text-terra uppercase tracking-wider mb-4">Empreinte</h4>
          {state.audioFingerprint.value ? (
            <>
              <p className="font-mono text-xs text-terra break-all mb-2">
                {state.audioFingerprint.value.slice(0, 32)}...
              </p>
              <p className="font-mono text-xs text-dim">
                Méthode: {state.audioFingerprint.method}
              </p>
            </>
          ) : (
            <p className="font-mono text-xs text-gold">⚠️ Aucune empreinte</p>
          )}
        </div>
      </div>

      {/* Validation Errors */}
      {hasErrors && (
        <div className="p-4 border border-red-500/30 bg-red-500/5">
          <p className="font-mono text-sm text-red-400 mb-2">Champs obligatoires manquants :</p>
          <ul className="list-disc list-inside">
            {Object.entries(validationErrors)
              .filter(([k]) => !k.includes('Warning'))
              .map(([key, msg]) => (
                <li key={key} className="font-mono text-xs text-red-400">{msg}</li>
              ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {validationErrors.fingerprintWarning && !hasErrors && (
        <div className="p-4 border border-gold/30 bg-gold/5">
          <p className="font-mono text-xs text-gold">
            ⚠️ {validationErrors.fingerprintWarning}
          </p>
        </div>
      )}

      {/* Generate Button */}
      {!generatedDoc && (
        <button
          onClick={handleGenerate}
          disabled={hasErrors || state.isGenerating}
          className="w-full py-4 bg-terra text-fwhite font-display text-xl uppercase tracking-wider hover:bg-terra/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {state.isGenerating ? 'Génération...' : 'Générer l\'attestation'}
        </button>
      )}

      {/* Generated Result */}
      {generatedDoc && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* FREK-ID Display */}
          <div className="p-8 bg-[#0a0a0a] border border-fgreen/30 text-center">
            <p className="font-mono text-xs text-dim mb-2">FREK-ID</p>
            <p className="font-display text-5xl md:text-6xl text-gold">
              {generatedDoc.mix_id}
            </p>
            <p className="font-mono text-xs text-dim mt-4">
              Généré le {new Date(generatedDoc.created_at).toLocaleString('fr-FR')}
            </p>
          </div>

          {/* JSON Preview */}
          <FrekJsonPreview document={generatedDoc} />

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={handleDownload}
              className={`flex-1 py-4 font-display text-lg uppercase tracking-wider transition-colors ${
                downloaded
                  ? 'bg-fgreen text-fwhite'
                  : 'bg-terra text-fwhite hover:bg-terra/90'
              }`}
            >
              {downloaded ? '✓ Téléchargé' : 'Télécharger l\'attestation'}
            </button>
            <button
              onClick={handleCopy}
              className={`flex-1 py-4 border font-display text-lg uppercase tracking-wider transition-colors ${
                copied
                  ? 'border-fgreen text-fgreen bg-fgreen/10'
                  : 'border-terra text-terra hover:bg-terra/10'
              }`}
            >
              {copied ? '✓ Copié' : 'Copier le JSON'}
            </button>
          </div>

          {/* Success Message */}
          {downloaded && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="p-6 bg-fgreen/10 border border-fgreen/30 text-center"
            >
              <p className="font-body text-light mb-2">
                Votre attestation <strong className="text-gold">{generatedDoc.mix_id}</strong> a été générée.
              </p>
              <p className="font-mono text-xs text-mid">
                Conservez ce fichier — il constitue votre preuve.
              </p>
            </motion.div>
          )}
        </motion.div>
      )}
    </div>
  );
}

export default Step4Review;
