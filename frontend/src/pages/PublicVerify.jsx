import React, { useState, useCallback } from 'react';
import { NavLink } from 'react-router-dom';
import { Upload, Music, CheckCircle, XCircle, AlertCircle, Download, FileJson, Settings, ChevronDown, ChevronUp, Shield } from 'lucide-react';
import { validateFrekJson, canonicalizeMetadata } from '../lib/frek-schema';
import { verifySignature, sha256, calculateDemoFingerprint } from '../lib/crypto';
import { downloadFile, readFileAsText, readFileAsArrayBuffer, formatDate, formatDuration, truncateHash } from '../lib/utils';
import { DOMAINS } from '../lib/domains';

const STATUS = {
  VALID: 'VERIFIED',
  MODIFIED: 'MODIFIED',
  INVALID: 'NOT VERIFIED',
  UNKNOWN: 'INCONCLUSIVE',
  PENDING: 'CHECKING'
};

const StatusDisplay = ({ status }) => {
  const config = {
    [STATUS.VALID]: { 
      bg: 'bg-[#00FF94]/10', 
      border: 'border-[#00FF94]/30', 
      text: 'text-[#00FF94]',
      icon: CheckCircle,
      label: 'VERIFIED'
    },
    [STATUS.MODIFIED]: { 
      bg: 'bg-[#FFB800]/10', 
      border: 'border-[#FFB800]/30', 
      text: 'text-[#FFB800]',
      icon: AlertCircle,
      label: 'MODIFIED'
    },
    [STATUS.INVALID]: { 
      bg: 'bg-[#FF3333]/10', 
      border: 'border-[#FF3333]/30', 
      text: 'text-[#FF3333]',
      icon: XCircle,
      label: 'NOT VERIFIED'
    },
    [STATUS.UNKNOWN]: { 
      bg: 'bg-zinc-800', 
      border: 'border-zinc-700', 
      text: 'text-zinc-400',
      icon: AlertCircle,
      label: 'INCONCLUSIVE'
    },
    [STATUS.PENDING]: { 
      bg: 'bg-zinc-800', 
      border: 'border-zinc-700', 
      text: 'text-zinc-400',
      icon: AlertCircle,
      label: 'CHECKING...'
    }
  };

  const c = config[status] || config[STATUS.UNKNOWN];
  const Icon = c.icon;

  return (
    <div className={`${c.bg} ${c.border} border p-8 text-center`}>
      <Icon className={`w-16 h-16 ${c.text} mx-auto mb-4`} strokeWidth={1.5} />
      <p className={`font-mono text-2xl ${c.text} tracking-widest`}>{c.label}</p>
    </div>
  );
};

export function PublicVerify() {
  const docsUrl = DOMAINS.DOCS_BASE;
  const [mode, setMode] = useState('public'); // 'public' or 'developer'
  const [audioFile, setAudioFile] = useState(null);
  const [frekFile, setFrekFile] = useState(null);
  const [frekData, setFrekData] = useState(null);
  const [results, setResults] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Handle audio file upload (public mode)
  const handleAudioUpload = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAudioFile(file);
    setResults(null);
  }, []);

  // Handle FREK file upload (developer mode)
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
        message: `Invalid JSON: ${err.message}`,
        details: null
      });
    }
  }, []);

  // Clear all
  const handleClear = useCallback(() => {
    setAudioFile(null);
    setFrekFile(null);
    setFrekData(null);
    setResults(null);
  }, []);

  // Verify in PUBLIC mode (audio only - demo simulation)
  const handlePublicVerify = useCallback(async () => {
    if (!audioFile) return;
    
    setIsVerifying(true);
    
    try {
      // Simulate verification process
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // In demo mode, we calculate fingerprint but can't verify without a .frek.json
      const audioBuffer = await readFileAsArrayBuffer(audioFile);
      const fingerprint = await calculateDemoFingerprint(audioBuffer);
      
      // For public demo, show INCONCLUSIVE since we have no attestation to compare
      setResults({
        global: STATUS.UNKNOWN,
        message: 'Audio fingerprint calculated. No attestation file available for comparison.',
        details: {
          fingerprint: fingerprint,
          audioFile: audioFile.name,
          audioSize: audioFile.size
        }
      });
    } catch (err) {
      setResults({
        global: STATUS.INVALID,
        message: `Error processing audio: ${err.message}`,
        details: null
      });
    }
    
    setIsVerifying(false);
  }, [audioFile]);

  // Verify in DEVELOPER mode (full FREK verification)
  const handleDeveloperVerify = useCallback(async () => {
    if (!frekData) return;

    setIsVerifying(true);

    try {
      // Step 1: Validate JSON schema
      const jsonValidation = validateFrekJson(frekData);
      if (!jsonValidation.valid) {
        setResults({
          global: STATUS.INVALID,
          message: 'Invalid FREK file structure',
          details: {
            errors: jsonValidation.errors.map(e => `${e.path}: ${e.message}`)
          }
        });
        setIsVerifying(false);
        return;
      }

      // Step 2: Verify signature
      const canonicalMetadata = canonicalizeMetadata(frekData.metadata);
      const messageToVerify = frekData.fingerprint + canonicalMetadata;
      const messageHash = await sha256(messageToVerify);
      
      const signatureBase64 = frekData.signature.replace('ed25519:', '');
      const publicKey = frekData.public_key;

      const sigResult = verifySignature(messageHash, signatureBase64, publicKey);
      
      if (!sigResult.valid) {
        setResults({
          global: STATUS.INVALID,
          message: 'Signature verification failed',
          details: {
            error: sigResult.error,
            json: 'Valid',
            signature: 'Invalid'
          }
        });
        setIsVerifying(false);
        return;
      }

      // Step 3: Check fingerprint against audio if provided
      let fingerprintStatus = 'Not checked';
      if (audioFile) {
        const audioBuffer = await readFileAsArrayBuffer(audioFile);
        const calculatedFingerprint = await calculateDemoFingerprint(audioBuffer);
        
        if (calculatedFingerprint === frekData.fingerprint) {
          fingerprintStatus = 'Match';
          setResults({
            global: STATUS.VALID,
            message: 'Attestation verified. Audio fingerprint matches.',
            details: {
              json: 'Valid',
              signature: 'Valid',
              fingerprint: 'Match',
              timestamp: frekData.metadata?.timestamp,
              duration: frekData.metadata?.duration,
              source_type: frekData.metadata?.source_type
            }
          });
        } else {
          setResults({
            global: STATUS.MODIFIED,
            message: 'Audio does not match the attestation fingerprint.',
            details: {
              json: 'Valid',
              signature: 'Valid',
              fingerprint: 'Mismatch',
              expected: truncateHash(frekData.fingerprint, 12),
              calculated: truncateHash(calculatedFingerprint, 12)
            }
          });
        }
      } else {
        // No audio provided, signature valid
        setResults({
          global: STATUS.VALID,
          message: 'Attestation structure and signature verified.',
          details: {
            json: 'Valid',
            signature: 'Valid',
            fingerprint: 'Not checked (no audio provided)',
            timestamp: frekData.metadata?.timestamp,
            duration: frekData.metadata?.duration,
            source_type: frekData.metadata?.source_type
          }
        });
      }

    } catch (err) {
      setResults({
        global: STATUS.INVALID,
        message: `Verification error: ${err.message}`,
        details: null
      });
    }

    setIsVerifying(false);
  }, [frekData, audioFile]);

  // Export report
  const handleExportReport = useCallback(() => {
    if (!results) return;

    const report = {
      timestamp: new Date().toISOString(),
      mode: mode,
      status: results.global,
      message: results.message,
      details: results.details
    };

    downloadFile(
      JSON.stringify(report, null, 2),
      `frek-verification-${Date.now()}.json`,
      'application/json'
    );
  }, [results, mode]);

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
            <NavLink to="/standard" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Standard
            </NavLink>
            <NavLink to="/manifesto" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Manifesto
            </NavLink>
            <NavLink to="/industry" className="font-mono text-sm text-zinc-400 hover:text-white transition-colors">
              Industry
            </NavLink>
            <a 
              href={docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-sm text-zinc-400 hover:text-white transition-colors"
            >
              Developers
            </a>
            <span className="font-mono text-sm px-4 py-2 bg-[#00F0FF] text-black">
              Verify
            </span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-24 pb-16 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="font-serif text-4xl md:text-5xl text-white mb-4 font-light">
              Verify Audio
            </h1>
            <p className="text-zinc-500 max-w-md mx-auto">
              Check if an audio file has a valid FREK attestation.
              All verification runs locally in your browser.
            </p>
          </div>

          {/* PUBLIC MODE - Default */}
          <div className="space-y-6">
            {/* Audio Upload */}
            <div className="bg-[#0A0A0A] border border-zinc-800 p-8">
              <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-6 text-center">
                Upload Audio File
              </p>
              
              <label 
                className={`
                  flex flex-col items-center justify-center p-12 cursor-pointer
                  border-2 border-dashed transition-all duration-200
                  ${audioFile 
                    ? 'border-[#00F0FF] bg-[#00F0FF]/5' 
                    : 'border-zinc-800 hover:border-zinc-600 hover:bg-zinc-900/30'}
                `}
                data-testid="audio-upload-zone"
              >
                <input
                  type="file"
                  accept="audio/*,.wav,.mp3,.aiff,.flac,.m4a"
                  onChange={handleAudioUpload}
                  className="hidden"
                  data-testid="audio-file-input"
                />
                {audioFile ? (
                  <>
                    <Music className="w-16 h-16 text-[#00F0FF] mb-4" strokeWidth={1} />
                    <p className="font-mono text-lg text-white mb-1">{audioFile.name}</p>
                    <p className="font-mono text-sm text-zinc-600">
                      {(audioFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </>
                ) : (
                  <>
                    <Music className="w-16 h-16 text-zinc-700 mb-4" strokeWidth={1} />
                    <p className="font-mono text-lg text-zinc-400 mb-1">
                      Drop audio file here
                    </p>
                    <p className="font-mono text-sm text-zinc-700">
                      MP3, WAV, AIFF, FLAC supported
                    </p>
                  </>
                )}
              </label>
            </div>

            {/* Verify Button */}
            <button
              onClick={mode === 'public' ? handlePublicVerify : handleDeveloperVerify}
              disabled={mode === 'public' ? !audioFile : !frekData}
              className={`
                w-full py-5 font-mono text-lg uppercase tracking-widest transition-all
                ${(mode === 'public' ? audioFile : frekData) && !isVerifying
                  ? 'bg-white text-black hover:bg-zinc-200'
                  : 'bg-zinc-900 text-zinc-600 cursor-not-allowed'
                }
              `}
              data-testid="verify-btn"
            >
              {isVerifying ? 'Verifying...' : 'Verify'}
            </button>

            {/* Results */}
            {results && (
              <div className="space-y-4">
                <StatusDisplay status={results.global} />
                
                <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
                  <p className="text-zinc-400 mb-4">{results.message}</p>
                  
                  {results.details && (
                    <div className="space-y-2 font-mono text-xs">
                      {Object.entries(results.details).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-zinc-600">{key}</span>
                          <span className="text-zinc-400">
                            {Array.isArray(value) ? value.join(', ') : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Export */}
                <button
                  onClick={handleExportReport}
                  className="w-full flex items-center justify-center gap-2 py-3 border border-zinc-800 text-zinc-500 hover:text-white hover:border-zinc-600 font-mono text-sm transition-colors"
                  data-testid="export-report-btn"
                >
                  <Download className="w-4 h-4" />
                  Export Verification Report
                </button>
              </div>
            )}

            {/* Developer Mode Toggle */}
            <div className="border-t border-zinc-800 pt-6">
              <button
                onClick={() => {
                  setShowAdvanced(!showAdvanced);
                  if (!showAdvanced) setMode('developer');
                }}
                className="w-full flex items-center justify-between py-3 text-zinc-600 hover:text-zinc-400 transition-colors"
              >
                <span className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest">
                  <Settings className="w-4 h-4" />
                  Developer Mode
                </span>
                {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showAdvanced && (
                <div className="mt-4 p-6 bg-zinc-900/50 border border-zinc-800 space-y-4">
                  <p className="font-mono text-xs text-zinc-600 mb-4">
                    Upload .frek.json attestation file for full cryptographic verification.
                  </p>
                  
                  {/* Mode Toggle */}
                  <div className="flex gap-2 mb-4">
                    <button
                      onClick={() => setMode('public')}
                      className={`flex-1 py-2 font-mono text-xs uppercase tracking-wide border transition-colors ${
                        mode === 'public' 
                          ? 'bg-zinc-800 border-zinc-700 text-white' 
                          : 'border-zinc-800 text-zinc-600 hover:text-zinc-400'
                      }`}
                    >
                      Audio Only
                    </button>
                    <button
                      onClick={() => setMode('developer')}
                      className={`flex-1 py-2 font-mono text-xs uppercase tracking-wide border transition-colors ${
                        mode === 'developer' 
                          ? 'bg-[#00F0FF]/10 border-[#00F0FF]/30 text-[#00F0FF]' 
                          : 'border-zinc-800 text-zinc-600 hover:text-zinc-400'
                      }`}
                    >
                      FREK + Audio
                    </button>
                  </div>

                  {/* FREK File Upload - Always visible in developer section */}
                  <label 
                    className={`
                      flex flex-col items-center justify-center p-6 cursor-pointer
                      border border-dashed transition-colors
                      ${frekFile ? 'border-[#00F0FF] bg-[#00F0FF]/5' : 'border-zinc-700 hover:border-zinc-600'}
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
                        <p className="font-mono text-sm text-white">{frekFile.name}</p>
                      </>
                    ) : (
                      <>
                        <FileJson className="w-8 h-8 text-zinc-700 mb-2" />
                        <p className="font-mono text-sm text-zinc-600">
                          Upload .frek.json attestation file
                        </p>
                      </>
                    )}
                  </label>

                  {/* Info */}
                  <p className="font-mono text-[10px] text-zinc-700 mt-4">
                    Developer mode enables full Ed25519 signature verification and JSON schema validation.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Privacy Notice */}
          <div className="mt-12 text-center">
            <p className="font-mono text-xs text-zinc-700">
              All verification runs locally in your browser.<br/>
              No audio or data is uploaded to any server.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PublicVerify;
