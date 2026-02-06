import React, { useState, useCallback } from 'react';
import { Upload, FileJson, Music, CheckCircle, XCircle, AlertCircle, Download, Trash2 } from 'lucide-react';
import { validateFrekJson, canonicalize } from '../lib/frek-schema';
import { verifySignature, sha256, calculateDemoFingerprint } from '../lib/crypto';
import { downloadFile, readFileAsText, readFileAsArrayBuffer, formatDate, formatDuration, truncateHash } from '../lib/utils';

// Status types
const STATUS = {
  VALID: 'VALID',
  MODIFIED: 'MODIFIED',
  INVALID: 'INVALID',
  UNKNOWN: 'UNKNOWN',
  PENDING: 'PENDING'
};

const StatusBadge = ({ status, label }) => {
  const styles = {
    [STATUS.VALID]: 'bg-[#00FF94]/10 text-[#00FF94] border-[#00FF94]/30',
    [STATUS.MODIFIED]: 'bg-[#FFB800]/10 text-[#FFB800] border-[#FFB800]/30',
    [STATUS.INVALID]: 'bg-[#FF3333]/10 text-[#FF3333] border-[#FF3333]/30',
    [STATUS.UNKNOWN]: 'bg-zinc-800 text-zinc-500 border-zinc-700',
    [STATUS.PENDING]: 'bg-zinc-800 text-zinc-500 border-zinc-700'
  };

  const icons = {
    [STATUS.VALID]: <CheckCircle className="w-4 h-4" />,
    [STATUS.MODIFIED]: <AlertCircle className="w-4 h-4" />,
    [STATUS.INVALID]: <XCircle className="w-4 h-4" />,
    [STATUS.UNKNOWN]: <AlertCircle className="w-4 h-4" />,
    [STATUS.PENDING]: <AlertCircle className="w-4 h-4" />
  };

  return (
    <span className={`inline-flex items-center gap-2 px-3 py-1 font-mono text-xs uppercase tracking-widest border ${styles[status]}`}>
      {icons[status]}
      {label || status}
    </span>
  );
};

export function Verify() {
  const [frekFile, setFrekFile] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [frekData, setFrekData] = useState(null);
  const [results, setResults] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);

  // Handle FREK JSON file upload
  const handleFrekUpload = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFrekFile(file);
    setResults(null);

    try {
      const content = await readFileAsText(file);
      const data = JSON.parse(content);
      setFrekData(data);
    } catch (err) {
      setFrekData(null);
      setResults({
        global: STATUS.INVALID,
        json: { status: STATUS.INVALID, errors: [`Erreur de parsing JSON: ${err.message}`] },
        signature: { status: STATUS.UNKNOWN },
        fingerprint: { status: STATUS.UNKNOWN }
      });
    }
  }, []);

  // Handle audio file upload
  const handleAudioUpload = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAudioFile(file);
  }, []);

  // Clear all
  const handleClear = useCallback(() => {
    setFrekFile(null);
    setAudioFile(null);
    setFrekData(null);
    setResults(null);
  }, []);

  // Run verification
  const handleVerify = useCallback(async () => {
    if (!frekData) return;

    setIsVerifying(true);
    const verificationResults = {
      global: STATUS.PENDING,
      json: { status: STATUS.PENDING, errors: [] },
      signature: { status: STATUS.PENDING, error: null },
      fingerprint: { status: STATUS.UNKNOWN, match: null }
    };

    try {
      // Step 1: Validate JSON schema
      const jsonValidation = validateFrekJson(frekData);
      if (!jsonValidation.valid) {
        verificationResults.json = { 
          status: STATUS.INVALID, 
          errors: jsonValidation.errors.map(e => `${e.path}: ${e.message}`) 
        };
        verificationResults.global = STATUS.INVALID;
        setResults(verificationResults);
        setIsVerifying(false);
        return;
      }
      verificationResults.json = { status: STATUS.VALID, errors: [] };

      // Step 2: Verify signature
      const canonicalJson = canonicalize(frekData);
      const messageToVerify = frekData.fingerprint + canonicalJson;
      const messageHash = await sha256(messageToVerify);
      
      // Extract signature (remove ed25519: prefix)
      const signatureBase64 = frekData.signature.replace('ed25519:', '');
      const publicKey = frekData.public_key;

      const sigResult = verifySignature(messageHash, signatureBase64, publicKey);
      
      if (sigResult.valid) {
        verificationResults.signature = { status: STATUS.VALID, error: null };
      } else {
        verificationResults.signature = { 
          status: STATUS.INVALID, 
          error: sigResult.error || 'Signature invalide' 
        };
      }

      // Step 3: Verify fingerprint (if audio provided)
      if (audioFile) {
        try {
          const audioBuffer = await readFileAsArrayBuffer(audioFile);
          const calculatedFingerprint = await calculateDemoFingerprint(audioBuffer);
          
          if (calculatedFingerprint === frekData.fingerprint) {
            verificationResults.fingerprint = { status: STATUS.VALID, match: true };
          } else {
            verificationResults.fingerprint = { 
              status: STATUS.MODIFIED, 
              match: false,
              calculated: calculatedFingerprint,
              expected: frekData.fingerprint
            };
          }
        } catch (err) {
          verificationResults.fingerprint = { 
            status: STATUS.INVALID, 
            error: `Erreur de calcul fingerprint: ${err.message}` 
          };
        }
      } else {
        verificationResults.fingerprint = { status: STATUS.UNKNOWN };
      }

      // Determine global status
      if (verificationResults.json.status === STATUS.VALID && 
          verificationResults.signature.status === STATUS.VALID) {
        if (verificationResults.fingerprint.status === STATUS.VALID) {
          verificationResults.global = STATUS.VALID;
        } else if (verificationResults.fingerprint.status === STATUS.MODIFIED) {
          verificationResults.global = STATUS.MODIFIED;
        } else if (verificationResults.fingerprint.status === STATUS.UNKNOWN) {
          verificationResults.global = STATUS.VALID; // Valid structure/signature, fingerprint not checked
        } else {
          verificationResults.global = STATUS.INVALID;
        }
      } else {
        verificationResults.global = STATUS.INVALID;
      }

    } catch (err) {
      verificationResults.global = STATUS.INVALID;
      verificationResults.json.errors.push(`Erreur de vérification: ${err.message}`);
    }

    setResults(verificationResults);
    setIsVerifying(false);
  }, [frekData, audioFile]);

  // Export report
  const handleExportReport = useCallback(() => {
    if (!results || !frekData) return;

    const report = {
      timestamp: new Date().toISOString(),
      frek_version: frekData.frek_version,
      verification: {
        global_status: results.global,
        json_valid: results.json.status === STATUS.VALID,
        json_errors: results.json.errors,
        signature_valid: results.signature.status === STATUS.VALID,
        signature_error: results.signature.error,
        fingerprint_status: results.fingerprint.status,
        fingerprint_match: results.fingerprint.match
      },
      document: {
        fingerprint: frekData.fingerprint,
        timestamp: frekData.metadata?.timestamp,
        duration: frekData.metadata?.duration,
        source_type: frekData.metadata?.source_type,
        public_key: truncateHash(frekData.public_key, 8)
      }
    };

    downloadFile(
      JSON.stringify(report, null, 2),
      `frek-verification-${Date.now()}.json`,
      'application/json'
    );
  }, [results, frekData]);

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 md:py-16">
      {/* Header */}
      <div className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-2">
          Outil
        </p>
        <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
          Vérificateur FREK
        </h1>
        <p className="text-zinc-400 max-w-2xl">
          Vérification locale de fichiers .frek.json. 
          Aucune donnée ne quitte votre navigateur.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <div className="space-y-4">
          {/* FREK File Upload */}
          <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
            <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-4">
              1. Fichier FREK (obligatoire)
            </p>
            
            <label 
              className={`
                dropzone flex flex-col items-center justify-center p-8 cursor-pointer
                ${frekFile ? 'border-[#00F0FF] bg-[#00F0FF]/5' : 'hover:border-zinc-600'}
              `}
              data-testid="frek-upload-zone"
            >
              <input
                type="file"
                accept=".json,.frek.json"
                onChange={handleFrekUpload}
                className="hidden"
                data-testid="frek-file-input"
              />
              {frekFile ? (
                <>
                  <FileJson className="w-8 h-8 text-[#00F0FF] mb-2" />
                  <p className="font-mono text-sm text-zinc-300">{frekFile.name}</p>
                  <p className="font-mono text-xs text-zinc-600 mt-1">
                    {(frekFile.size / 1024).toFixed(2)} KB
                  </p>
                </>
              ) : (
                <>
                  <Upload className="w-8 h-8 text-zinc-600 mb-2" />
                  <p className="font-mono text-sm text-zinc-500">
                    Déposer un fichier .frek.json
                  </p>
                  <p className="font-mono text-xs text-zinc-700 mt-1">
                    ou cliquer pour sélectionner
                  </p>
                </>
              )}
            </label>
          </div>

          {/* Audio File Upload */}
          <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
            <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-4">
              2. Fichier Audio (optionnel)
            </p>
            
            <label 
              className={`
                dropzone flex flex-col items-center justify-center p-8 cursor-pointer
                ${audioFile ? 'border-[#00F0FF] bg-[#00F0FF]/5' : 'hover:border-zinc-600'}
              `}
              data-testid="audio-upload-zone"
            >
              <input
                type="file"
                accept="audio/*,.wav,.mp3,.flac,.aiff"
                onChange={handleAudioUpload}
                className="hidden"
                data-testid="audio-file-input"
              />
              {audioFile ? (
                <>
                  <Music className="w-8 h-8 text-[#00F0FF] mb-2" />
                  <p className="font-mono text-sm text-zinc-300">{audioFile.name}</p>
                  <p className="font-mono text-xs text-zinc-600 mt-1">
                    {(audioFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </>
              ) : (
                <>
                  <Music className="w-8 h-8 text-zinc-700 mb-2" />
                  <p className="font-mono text-sm text-zinc-600">
                    Déposer un fichier audio
                  </p>
                  <p className="font-mono text-xs text-zinc-700 mt-1">
                    Pour vérifier le fingerprint
                  </p>
                </>
              )}
            </label>
            
            <p className="font-mono text-[10px] text-zinc-700 mt-3">
              Note: Sans audio, le fingerprint sera marqué UNKNOWN (structure/signature vérifiées)
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleVerify}
              disabled={!frekData || isVerifying}
              className={`
                flex-1 flex items-center justify-center gap-2 px-6 py-3
                font-mono text-sm uppercase tracking-wide transition-colors
                ${frekData && !isVerifying
                  ? 'bg-zinc-100 text-black hover:bg-zinc-300'
                  : 'bg-zinc-900 text-zinc-600 cursor-not-allowed'
                }
              `}
              data-testid="verify-btn"
            >
              {isVerifying ? 'Vérification...' : 'Vérifier'}
            </button>
            
            <button
              onClick={handleClear}
              className="px-4 py-3 border border-zinc-800 text-zinc-500 hover:text-white hover:border-zinc-600 transition-colors"
              data-testid="clear-btn"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          {/* Global Status */}
          <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
            <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-4">
              Statut Global
            </p>
            
            {results ? (
              <div className="flex items-center gap-4" data-testid="global-status">
                <StatusBadge status={results.global} />
                <span className="font-mono text-sm text-zinc-500">
                  {results.global === STATUS.VALID && 'Attestation valide'}
                  {results.global === STATUS.MODIFIED && 'Audio modifié détecté'}
                  {results.global === STATUS.INVALID && 'Attestation invalide'}
                  {results.global === STATUS.UNKNOWN && 'Vérification partielle'}
                </span>
              </div>
            ) : (
              <p className="font-mono text-sm text-zinc-600">
                Aucune vérification effectuée
              </p>
            )}
          </div>

          {/* Detailed Results */}
          {results && (
            <>
              {/* JSON Validation */}
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-mono text-xs uppercase tracking-widest text-zinc-600">
                    Structure JSON
                  </p>
                  <StatusBadge status={results.json.status} label={results.json.status === STATUS.VALID ? 'Valide' : 'Invalide'} />
                </div>
                {results.json.errors.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {results.json.errors.map((err, i) => (
                      <li key={i} className="font-mono text-xs text-[#FF3333]">
                        • {err}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Signature */}
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-mono text-xs uppercase tracking-widest text-zinc-600">
                    Signature Ed25519
                  </p>
                  <StatusBadge 
                    status={results.signature.status} 
                    label={results.signature.status === STATUS.VALID ? 'Valide' : results.signature.status === STATUS.UNKNOWN ? 'Non vérifiée' : 'Invalide'} 
                  />
                </div>
                {results.signature.error && (
                  <p className="font-mono text-xs text-[#FF3333] mt-2">
                    {results.signature.error}
                  </p>
                )}
              </div>

              {/* Fingerprint */}
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-mono text-xs uppercase tracking-widest text-zinc-600">
                    Fingerprint Audio
                  </p>
                  <StatusBadge 
                    status={results.fingerprint.status} 
                    label={
                      results.fingerprint.status === STATUS.VALID ? 'Correspond' : 
                      results.fingerprint.status === STATUS.MODIFIED ? 'Modifié' :
                      results.fingerprint.status === STATUS.UNKNOWN ? 'Non vérifié' : 'Erreur'
                    } 
                  />
                </div>
                {results.fingerprint.status === STATUS.UNKNOWN && (
                  <p className="font-mono text-xs text-zinc-600 mt-2">
                    Uploadez un fichier audio pour vérifier le fingerprint
                  </p>
                )}
                {results.fingerprint.status === STATUS.MODIFIED && (
                  <div className="mt-2 space-y-1">
                    <p className="font-mono text-xs text-zinc-500">
                      Attendu: <span className="text-zinc-400">{truncateHash(results.fingerprint.expected)}</span>
                    </p>
                    <p className="font-mono text-xs text-zinc-500">
                      Calculé: <span className="text-[#FFB800]">{truncateHash(results.fingerprint.calculated)}</span>
                    </p>
                  </div>
                )}
              </div>

              {/* Export */}
              <button
                onClick={handleExportReport}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-600 font-mono text-sm uppercase tracking-wide transition-colors"
                data-testid="export-report-btn"
              >
                <Download className="w-4 h-4" />
                Exporter le rapport
              </button>
            </>
          )}

          {/* Document Info */}
          {frekData && (
            <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
              <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-3">
                Informations du Document
              </p>
              <div className="space-y-2 font-mono text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-600">Version</span>
                  <span className="text-zinc-400">{frekData.frek_version}</span>
                </div>
                {frekData.metadata?.timestamp && (
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Timestamp</span>
                    <span className="text-zinc-400">{formatDate(frekData.metadata.timestamp)}</span>
                  </div>
                )}
                {frekData.metadata?.duration && (
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Durée</span>
                    <span className="text-zinc-400">{formatDuration(frekData.metadata.duration)}</span>
                  </div>
                )}
                {frekData.metadata?.source_type && (
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Type</span>
                    <span className="text-zinc-400 uppercase">{frekData.metadata.source_type}</span>
                  </div>
                )}
                {frekData.fingerprint && (
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Fingerprint</span>
                    <span className="text-zinc-400">{truncateHash(frekData.fingerprint, 12)}</span>
                  </div>
                )}
                {frekData.segments && (
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Segments</span>
                    <span className="text-zinc-400">{frekData.segments.length}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Privacy Notice */}
      <div className="mt-12 p-4 border border-zinc-800 bg-[#0A0A0A]">
        <p className="font-mono text-[10px] text-zinc-600 text-center">
          Toute la vérification s'effectue localement dans votre navigateur. 
          Aucune donnée n'est envoyée à un serveur. 
          Vérifiable dans les outils de développement (Network tab).
        </p>
      </div>
    </div>
  );
}

export default Verify;
