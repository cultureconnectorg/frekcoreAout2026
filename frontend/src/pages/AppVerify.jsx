import React, { useState, useCallback } from 'react';
import { NavLink } from 'react-router-dom';
import { Upload, FileJson, Music, CheckCircle, XCircle, AlertCircle, Download, Trash2, ArrowLeft } from 'lucide-react';
import { validateFrekJson, canonicalizeMetadata } from '../lib/frek-schema';
import { verifySignature, sha256, calculateDemoFingerprint } from '../lib/crypto';
import { downloadFile, readFileAsText, readFileAsArrayBuffer, formatDate, formatDuration, truncateHash } from '../lib/utils';

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

export function AppVerify() {
  const [frekFile, setFrekFile] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [frekData, setFrekData] = useState(null);
  const [results, setResults] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);

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
        json: { status: STATUS.INVALID, errors: [`JSON parse error: ${err.message}`] },
        signature: { status: STATUS.UNKNOWN },
        fingerprint: { status: STATUS.UNKNOWN }
      });
    }
  }, []);

  const handleAudioUpload = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAudioFile(file);
  }, []);

  const handleClear = useCallback(() => {
    setFrekFile(null);
    setAudioFile(null);
    setFrekData(null);
    setResults(null);
  }, []);

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

      const canonicalMetadata = canonicalizeMetadata(frekData.metadata);
      const messageToVerify = frekData.fingerprint + canonicalMetadata;
      const messageHash = await sha256(messageToVerify);
      
      const signatureBase64 = frekData.signature.replace('ed25519:', '');
      const publicKey = frekData.public_key;

      const sigResult = verifySignature(messageHash, signatureBase64, publicKey);
      
      if (sigResult.valid) {
        verificationResults.signature = { status: STATUS.VALID, error: null };
      } else {
        verificationResults.signature = { 
          status: STATUS.INVALID, 
          error: sigResult.error || 'Invalid signature' 
        };
      }

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
            error: `Fingerprint error: ${err.message}` 
          };
        }
      } else {
        verificationResults.fingerprint = { status: STATUS.UNKNOWN };
      }

      if (verificationResults.json.status === STATUS.VALID && 
          verificationResults.signature.status === STATUS.VALID) {
        if (verificationResults.fingerprint.status === STATUS.VALID) {
          verificationResults.global = STATUS.VALID;
        } else if (verificationResults.fingerprint.status === STATUS.MODIFIED) {
          verificationResults.global = STATUS.MODIFIED;
        } else if (verificationResults.fingerprint.status === STATUS.UNKNOWN) {
          verificationResults.global = STATUS.VALID;
        } else {
          verificationResults.global = STATUS.INVALID;
        }
      } else {
        verificationResults.global = STATUS.INVALID;
      }

    } catch (err) {
      verificationResults.global = STATUS.INVALID;
      verificationResults.json.errors.push(`Verification error: ${err.message}`);
    }

    setResults(verificationResults);
    setIsVerifying(false);
  }, [frekData, audioFile]);

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
    <div className="min-h-screen bg-[#030303]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#030303]/90 backdrop-blur-sm border-b border-zinc-900">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <NavLink to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#00F0FF] flex items-center justify-center">
              <span className="font-mono font-bold text-black text-sm">F</span>
            </div>
            <span className="font-mono font-bold text-lg tracking-tight text-white">FREK</span>
          </NavLink>
          
          <div className="hidden md:flex items-center gap-8">
            <NavLink to="/docs" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Documentation
            </NavLink>
            <NavLink to="/industry" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Industry
            </NavLink>
            <span className="font-mono text-sm px-4 py-2 bg-[#00F0FF] text-black">
              Verify
            </span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-24 pb-16 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-12 text-center">
            <h1 className="font-mono text-3xl md:text-4xl font-bold text-white mb-4">
              FREK Verification
            </h1>
            <p className="text-zinc-500 max-w-lg mx-auto">
              Verify .frek.json attestation files locally. 
              No data leaves your browser.
            </p>
          </div>

          {/* Verification Interface */}
          <div className="grid md:grid-cols-2 gap-8">
            {/* Upload Section */}
            <div className="space-y-6">
              {/* FREK File */}
              <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
                <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-4">
                  FREK File (required)
                </p>
                
                <label 
                  className={`
                    flex flex-col items-center justify-center p-8 cursor-pointer
                    border border-dashed transition-colors
                    ${frekFile ? 'border-[#00F0FF] bg-[#00F0FF]/5' : 'border-zinc-800 hover:border-zinc-600'}
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
                      <FileJson className="w-10 h-10 text-[#00F0FF] mb-3" />
                      <p className="font-mono text-sm text-white">{frekFile.name}</p>
                      <p className="font-mono text-xs text-zinc-600 mt-1">
                        {(frekFile.size / 1024).toFixed(2)} KB
                      </p>
                    </>
                  ) : (
                    <>
                      <Upload className="w-10 h-10 text-zinc-700 mb-3" />
                      <p className="font-mono text-sm text-zinc-500">
                        Drop .frek.json file
                      </p>
                    </>
                  )}
                </label>
              </div>

              {/* Audio File */}
              <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
                <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-4">
                  Audio File (optional)
                </p>
                
                <label 
                  className={`
                    flex flex-col items-center justify-center p-8 cursor-pointer
                    border border-dashed transition-colors
                    ${audioFile ? 'border-[#00F0FF] bg-[#00F0FF]/5' : 'border-zinc-800 hover:border-zinc-600'}
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
                      <Music className="w-10 h-10 text-[#00F0FF] mb-3" />
                      <p className="font-mono text-sm text-white">{audioFile.name}</p>
                      <p className="font-mono text-xs text-zinc-600 mt-1">
                        {(audioFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </>
                  ) : (
                    <>
                      <Music className="w-10 h-10 text-zinc-800 mb-3" />
                      <p className="font-mono text-sm text-zinc-600">
                        For fingerprint verification
                      </p>
                    </>
                  )}
                </label>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={handleVerify}
                  disabled={!frekData || isVerifying}
                  className={`
                    flex-1 py-4 font-mono text-sm uppercase tracking-wide transition-colors
                    ${frekData && !isVerifying
                      ? 'bg-[#00F0FF] text-black hover:bg-[#00F0FF]/90'
                      : 'bg-zinc-900 text-zinc-600 cursor-not-allowed'
                    }
                  `}
                  data-testid="verify-btn"
                >
                  {isVerifying ? 'Verifying...' : 'Verify'}
                </button>
                
                <button
                  onClick={handleClear}
                  className="px-4 py-4 border border-zinc-800 text-zinc-500 hover:text-white hover:border-zinc-600 transition-colors"
                  data-testid="clear-btn"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Results Section */}
            <div className="space-y-6">
              {/* Global Status */}
              <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
                <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-4">
                  Status
                </p>
                
                {results ? (
                  <div className="flex items-center gap-4" data-testid="global-status">
                    <StatusBadge status={results.global} />
                    <span className="font-mono text-sm text-zinc-500">
                      {results.global === STATUS.VALID && 'Valid attestation'}
                      {results.global === STATUS.MODIFIED && 'Audio modified'}
                      {results.global === STATUS.INVALID && 'Invalid attestation'}
                      {results.global === STATUS.UNKNOWN && 'Partial verification'}
                    </span>
                  </div>
                ) : (
                  <p className="font-mono text-sm text-zinc-700">
                    Upload a file to verify
                  </p>
                )}
              </div>

              {results && (
                <>
                  {/* JSON */}
                  <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                    <div className="flex items-center justify-between">
                      <p className="font-mono text-xs text-zinc-600">JSON Schema</p>
                      <StatusBadge status={results.json.status} label={results.json.status === STATUS.VALID ? 'Valid' : 'Invalid'} />
                    </div>
                    {results.json.errors.length > 0 && (
                      <ul className="mt-3 space-y-1">
                        {results.json.errors.slice(0, 3).map((err, i) => (
                          <li key={i} className="font-mono text-xs text-[#FF3333]">• {err}</li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* Signature */}
                  <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                    <div className="flex items-center justify-between">
                      <p className="font-mono text-xs text-zinc-600">Ed25519 Signature</p>
                      <StatusBadge 
                        status={results.signature.status} 
                        label={results.signature.status === STATUS.VALID ? 'Valid' : results.signature.status === STATUS.UNKNOWN ? 'N/A' : 'Invalid'} 
                      />
                    </div>
                  </div>

                  {/* Fingerprint */}
                  <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                    <div className="flex items-center justify-between">
                      <p className="font-mono text-xs text-zinc-600">Audio Fingerprint</p>
                      <StatusBadge 
                        status={results.fingerprint.status} 
                        label={
                          results.fingerprint.status === STATUS.VALID ? 'Match' : 
                          results.fingerprint.status === STATUS.MODIFIED ? 'Modified' :
                          results.fingerprint.status === STATUS.UNKNOWN ? 'Not checked' : 'Error'
                        } 
                      />
                    </div>
                  </div>

                  {/* Export */}
                  <button
                    onClick={handleExportReport}
                    className="w-full flex items-center justify-center gap-2 py-3 border border-zinc-800 text-zinc-500 hover:text-white hover:border-zinc-600 font-mono text-sm transition-colors"
                    data-testid="export-report-btn"
                  >
                    <Download className="w-4 h-4" />
                    Export Report
                  </button>
                </>
              )}

              {/* Document Info */}
              {frekData && (
                <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                  <p className="font-mono text-xs text-zinc-600 mb-3">Document Info</p>
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
                        <span className="text-zinc-600">Duration</span>
                        <span className="text-zinc-400">{formatDuration(frekData.metadata.duration)}</span>
                      </div>
                    )}
                    {frekData.metadata?.source_type && (
                      <div className="flex justify-between">
                        <span className="text-zinc-600">Type</span>
                        <span className="text-zinc-400 uppercase">{frekData.metadata.source_type}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Privacy Notice */}
          <div className="mt-12 p-4 border border-zinc-900 text-center">
            <p className="font-mono text-xs text-zinc-700">
              All verification is performed locally in your browser. No data is sent to any server.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AppVerify;
