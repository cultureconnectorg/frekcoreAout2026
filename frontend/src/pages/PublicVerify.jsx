import React, { useState, useCallback, useRef } from 'react';
import { Music, CheckCircle, XCircle, AlertCircle, Download, FileJson, Settings, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { verifyFrek, hashAudio, validateSchema, canonicalize, verifySignature, sha256, generateReport } from '../core/frek-core';
import { downloadFile, readFileAsText, readFileAsArrayBuffer, truncateHash } from '../lib/utils';
import { useLanguage } from '../lib/LanguageContext';
import { Navigation } from '../components/Navigation';
import { Footer } from '../components/Footer';

const STATUS = {
  VALID: 'VERIFIED',
  MODIFIED: 'MODIFIED',
  INVALID: 'NOT VERIFIED',
  UNKNOWN: 'INCONCLUSIVE',
  PENDING: 'CHECKING'
};

const StatusDisplay = ({ status, t }) => {
  const config = {
    [STATUS.VALID]: { 
      bg: 'bg-[#00FF94]/10', 
      border: 'border-[#00FF94]/30', 
      text: 'text-[#00FF94]',
      icon: CheckCircle,
      label: t.verify.verified
    },
    [STATUS.MODIFIED]: { 
      bg: 'bg-[#FFB800]/10', 
      border: 'border-[#FFB800]/30', 
      text: 'text-[#FFB800]',
      icon: AlertCircle,
      label: t.verify.modified
    },
    [STATUS.INVALID]: { 
      bg: 'bg-[#FF3333]/10', 
      border: 'border-[#FF3333]/30', 
      text: 'text-[#FF3333]',
      icon: XCircle,
      label: t.verify.notVerified
    },
    [STATUS.UNKNOWN]: { 
      bg: 'bg-zinc-800', 
      border: 'border-zinc-700', 
      text: 'text-zinc-400',
      icon: AlertCircle,
      label: t.verify.inconclusive
    },
    [STATUS.PENDING]: { 
      bg: 'bg-zinc-800', 
      border: 'border-zinc-700', 
      text: 'text-zinc-400',
      icon: Loader2,
      label: t.verify.checking
    }
  };

  const c = config[status] || config[STATUS.UNKNOWN];
  const Icon = c.icon;

  return (
    <div className={`${c.bg} ${c.border} border p-8 text-center`} data-testid="verification-status">
      <Icon className={`w-16 h-16 ${c.text} mx-auto mb-4 ${status === STATUS.PENDING ? 'animate-spin' : ''}`} strokeWidth={1.5} />
      <p className={`font-mono text-2xl ${c.text} tracking-widest`}>{c.label}</p>
    </div>
  );
};

export function PublicVerify() {
  const { t } = useLanguage();
  const [mode, setMode] = useState('public');
  const [audioFile, setAudioFile] = useState(null);
  const [frekFile, setFrekFile] = useState(null);
  const [frekData, setFrekData] = useState(null);
  const [results, setResults] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  
  const audioInputRef = useRef(null);
  const frekInputRef = useRef(null);

  // Handle drag events
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e, type) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer?.files;
    if (files && files[0]) {
      if (type === 'audio') {
        handleAudioFile(files[0]);
      } else {
        handleFrekFile(files[0]);
      }
    }
  }, []);

  // Handle audio file
  const handleAudioFile = useCallback((file) => {
    setAudioFile(file);
    setResults(null);
    setProgress(0);
  }, []);

  const handleAudioUpload = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file) handleAudioFile(file);
  }, [handleAudioFile]);

  // Handle FREK file
  const handleFrekFile = useCallback(async (file) => {
    setFrekFile(file);
    setResults(null);
    setProgress(0);

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

  const handleFrekUpload = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file) handleFrekFile(file);
  }, [handleFrekFile]);

  // Clear all
  const handleClear = useCallback(() => {
    setAudioFile(null);
    setFrekFile(null);
    setFrekData(null);
    setResults(null);
    setProgress(0);
  }, []);

  // Verify in PUBLIC mode - uses real FFT fingerprinting
  const handlePublicVerify = useCallback(async () => {
    if (!audioFile) return;
    
    setIsVerifying(true);
    setProgress(5);
    
    try {
      const audioBuffer = await readFileAsArrayBuffer(audioFile);
      
      // Use real FFT-based fingerprinting from frek-core
      const result = await hashAudio(audioBuffer, {
        onProgress: (p, msg) => setProgress(p)
      });
      
      setResults({
        global: STATUS.UNKNOWN,
        message: `${t.verify.fingerprintCalculated}. ${t.verify.noAttestation}`,
        details: {
          fingerprint: result.fingerprint,
          duration: `${result.duration.toFixed(2)}s`,
          segments: result.segments.length,
          audioFile: audioFile.name,
          audioSize: `${(audioFile.size / 1024 / 1024).toFixed(2)} MB`
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
  }, [audioFile, t]);

  // Verify in DEVELOPER mode - uses full FREK verification pipeline
  const handleDeveloperVerify = useCallback(async () => {
    if (!frekData) return;

    setIsVerifying(true);
    setProgress(5);

    try {
      // Use the full verification pipeline from frek-core
      const audioBuffer = audioFile ? await readFileAsArrayBuffer(audioFile) : null;
      
      const result = await verifyFrek(frekData, audioBuffer, (p, msg) => {
        setProgress(p);
      });

      const statusMap = {
        'VERIFIED': STATUS.VALID,
        'MODIFIED': STATUS.MODIFIED,
        'INVALID': STATUS.INVALID,
        'ERROR': STATUS.INVALID
      };

      const messageMap = {
        'VERIFIED': result.details.fingerprint === 'Match' ? t.verify.audioMatch : t.verify.structureVerified,
        'MODIFIED': t.verify.audioMismatch,
        'INVALID': result.details.errors ? t.verify.invalidStructure : t.verify.signatureFailed,
        'ERROR': result.message
      };

      setResults({
        global: statusMap[result.status] || STATUS.UNKNOWN,
        message: messageMap[result.status] || result.message,
        details: result.details
      });

    } catch (err) {
      setResults({
        global: STATUS.INVALID,
        message: `Verification error: ${err.message}`,
        details: null
      });
    }

    setIsVerifying(false);
  }, [frekData, audioFile, t]);

  // Export report using frek-core
  const handleExportReport = useCallback(() => {
    if (!results) return;

    const report = generateReport({
      status: results.global,
      message: results.message,
      details: results.details,
      frekData: frekData,
      audioInfo: audioFile ? {
        name: audioFile.name,
        size: audioFile.size,
        type: audioFile.type
      } : null
    });

    downloadFile(
      JSON.stringify(report, null, 2),
      `frek-verification-${Date.now()}.json`,
      'application/json'
    );
  }, [results, frekData, audioFile]);

  return (
    <div className="min-h-screen bg-[#030303]">
      <Navigation currentPage="verify" />

      {/* Main Content */}
      <div className="pt-24 pb-16 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="font-serif text-4xl md:text-5xl text-white mb-4 font-light">
              {t.verify.title}
            </h1>
            <p 
              className="text-zinc-500 max-w-md mx-auto"
              dangerouslySetInnerHTML={{ __html: t.verify.description }}
            />
          </div>

          {/* PUBLIC MODE - Default */}
          <div className="space-y-6">
            {/* Audio Upload with Drag & Drop */}
            <div className="bg-[#0A0A0A] border border-zinc-800 p-8">
              <p className="font-mono text-xs uppercase tracking-widest text-zinc-600 mb-6 text-center">
                {t.verify.uploadAudio}
              </p>
              
              <label 
                className={`
                  flex flex-col items-center justify-center p-12 cursor-pointer
                  border-2 border-dashed transition-all duration-200
                  ${isDragging 
                    ? 'border-[#00F0FF] bg-[#00F0FF]/10' 
                    : audioFile 
                      ? 'border-[#00F0FF] bg-[#00F0FF]/5' 
                      : 'border-zinc-800 hover:border-zinc-600 hover:bg-zinc-900/30'}
                `}
                data-testid="audio-upload-zone"
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, 'audio')}
              >
                <input
                  ref={audioInputRef}
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
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleClear();
                      }}
                      className="mt-4 font-mono text-xs text-zinc-500 hover:text-white underline"
                    >
                      Clear
                    </button>
                  </>
                ) : (
                  <>
                    <Music className="w-16 h-16 text-zinc-700 mb-4" strokeWidth={1} />
                    <p className="font-mono text-lg text-zinc-400 mb-1">
                      {t.verify.dropAudio}
                    </p>
                    <p className="font-mono text-sm text-zinc-700">
                      {t.verify.supported}
                    </p>
                  </>
                )}
              </label>
            </div>

            {/* Progress Bar */}
            {isVerifying && (
              <div className="bg-[#0A0A0A] border border-zinc-800 p-4">
                <div className="h-2 bg-zinc-800 overflow-hidden">
                  <div 
                    className="h-full bg-[#00F0FF] transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="font-mono text-xs text-zinc-600 mt-2 text-center">
                  {progress}% - {t.verify.verifying}
                </p>
              </div>
            )}

            {/* Verify Button */}
            <button
              onClick={mode === 'public' ? handlePublicVerify : handleDeveloperVerify}
              disabled={(mode === 'public' ? !audioFile : !frekData) || isVerifying}
              className={`
                w-full py-5 font-mono text-lg uppercase tracking-widest transition-all flex items-center justify-center gap-3
                ${(mode === 'public' ? audioFile : frekData) && !isVerifying
                  ? 'bg-white text-black hover:bg-zinc-200'
                  : 'bg-zinc-900 text-zinc-600 cursor-not-allowed'
                }
              `}
              data-testid="verify-btn"
            >
              {isVerifying && <Loader2 className="w-5 h-5 animate-spin" />}
              {isVerifying ? t.verify.verifying : t.verify.verifyBtn}
            </button>

            {/* Results */}
            {results && (
              <div className="space-y-4">
                <StatusDisplay status={results.global} t={t} />
                
                <div className="bg-[#0A0A0A] border border-zinc-800 p-6">
                  <p className="text-zinc-400 mb-4">{results.message}</p>
                  
                  {results.details && (
                    <div className="space-y-2 font-mono text-xs">
                      {Object.entries(results.details).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-zinc-600">{key}</span>
                          <span className="text-zinc-400 max-w-[60%] text-right break-all">
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
                  {t.verify.exportReport}
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
                data-testid="developer-mode-toggle"
              >
                <span className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest">
                  <Settings className="w-4 h-4" />
                  {t.verify.developerMode}
                </span>
                {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showAdvanced && (
                <div className="mt-4 p-6 bg-zinc-900/50 border border-zinc-800 space-y-4">
                  <p 
                    className="font-mono text-xs text-zinc-600 mb-4"
                    dangerouslySetInnerHTML={{ __html: t.verify.uploadFrek }}
                  />
                  
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
                      {t.verify.audioOnly}
                    </button>
                    <button
                      onClick={() => setMode('developer')}
                      className={`flex-1 py-2 font-mono text-xs uppercase tracking-wide border transition-colors ${
                        mode === 'developer' 
                          ? 'bg-[#00F0FF]/10 border-[#00F0FF]/30 text-[#00F0FF]' 
                          : 'border-zinc-800 text-zinc-600 hover:text-zinc-400'
                      }`}
                    >
                      {t.verify.frekAudio}
                    </button>
                  </div>

                  {/* FREK File Upload */}
                  <label 
                    className={`
                      flex flex-col items-center justify-center p-6 cursor-pointer
                      border border-dashed transition-colors
                      ${frekFile ? 'border-[#00F0FF] bg-[#00F0FF]/5' : 'border-zinc-700 hover:border-zinc-600'}
                    `}
                    data-testid="frek-upload-zone"
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, 'frek')}
                  >
                    <input
                      ref={frekInputRef}
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
                        <p 
                          className="font-mono text-sm text-zinc-600"
                          dangerouslySetInnerHTML={{ __html: t.verify.uploadFrek }}
                        />
                      </>
                    )}
                  </label>

                  {/* Info */}
                  <p 
                    className="font-mono text-[10px] text-zinc-700 mt-4"
                    dangerouslySetInnerHTML={{ __html: t.verify.devModeDesc }}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Privacy Notice */}
          <div className="mt-12 text-center">
            <p 
              className="font-mono text-xs text-zinc-700"
              dangerouslySetInnerHTML={{ __html: t.verify.privacyNotice }}
            />
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default PublicVerify;
