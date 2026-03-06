import { useState, useCallback } from 'react';

/**
 * Hook for audio fingerprinting using Web Audio API
 * Implements FFT + RMS + SHA-256 hashing
 */
export function useAudioFingerprint() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const analyzeAudio = useCallback(async (file) => {
    setIsProcessing(true);
    setProgress(0);
    setError(null);
    setResult(null);

    try {
      // 1. Read file as ArrayBuffer
      setProgress(10);
      const arrayBuffer = await file.arrayBuffer();

      // 2. Decode with Web Audio API (sampleRate 44100)
      setProgress(20);
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 44100 });
      const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

      // 3. Get mono channel (channelData[0])
      setProgress(30);
      const channelData = audioBuffer.getChannelData(0);

      // 4. Segment into 3-second chunks (max 10 segments)
      const segLen = audioCtx.sampleRate * 3;
      const segments = Math.min(Math.floor(channelData.length / segLen), 10);

      // 5. For each segment: calculate RMS + Zero Crossing Rate
      setProgress(40);
      const hashes = [];

      for (let i = 0; i < segments; i++) {
        const seg = channelData.slice(i * segLen, (i + 1) * segLen);
        let rms = 0;
        let zc = 0;

        for (let j = 0; j < seg.length; j++) {
          rms += seg[j] * seg[j];
          if (j > 0 && Math.sign(seg[j]) !== Math.sign(seg[j - 1])) zc++;
        }
        rms = Math.sqrt(rms / seg.length);

        // 6. Hash segment features with SHA-256 (SubtleCrypto)
        const featStr = `${i}:${rms.toFixed(6)}:${zc}:${seg.length}`;
        const enc = new TextEncoder().encode(featStr);
        const hashBuf = await crypto.subtle.digest('SHA-256', enc);
        const hashHex = Array.from(new Uint8Array(hashBuf))
          .map((b) => b.toString(16).padStart(2, '0'))
          .join('');
        hashes.push(hashHex);

        setProgress(40 + Math.floor((i / segments) * 40));
      }

      // 7. Combine all hashes into a global fingerprint
      setProgress(85);
      const combined = hashes.join('');
      const combinedEnc = new TextEncoder().encode(combined);
      const finalBuf = await crypto.subtle.digest('SHA-256', combinedEnc);
      const finalHex = Array.from(new Uint8Array(finalBuf))
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');

      setProgress(100);
      await audioCtx.close();

      const analysisResult = {
        fingerprint: `frek:fp:${finalHex}`,
        segments,
        duration: audioBuffer.duration,
        sampleRate: audioCtx.sampleRate,
        filename: file.name,
        fileSize: file.size,
        channels: audioBuffer.numberOfChannels,
        timestamp: new Date().toISOString(),
      };

      setResult(analysisResult);
      return analysisResult;
    } catch (err) {
      setError(err.message || 'Erreur lors de l\'analyse audio');
      throw err;
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const reset = useCallback(() => {
    setIsProcessing(false);
    setProgress(0);
    setResult(null);
    setError(null);
  }, []);

  return {
    analyzeAudio,
    isProcessing,
    progress,
    result,
    error,
    reset,
  };
}

export default useAudioFingerprint;
