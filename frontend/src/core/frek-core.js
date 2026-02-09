/**
 * FREK Core Module v0.4
 * 
 * Core verification and fingerprinting functions for the FREK protocol.
 * This module is designed to be reusable across different implementations.
 * 
 * Exports:
 * - canonicalize(metadata): Canonicalize metadata for consistent hashing
 * - verifySignature(message, signature, publicKey): Verify Ed25519 signature
 * - validateSchema(data): Validate FREK JSON structure
 * - hashAudio(audioBuffer, options): Generate audio fingerprint using FFT
 * - generateReport(results): Create verification report
 */

import nacl from 'tweetnacl';
import { decodeBase64 } from 'tweetnacl-util';
import { z } from 'zod';

// ============================================================================
// Schema Definitions
// ============================================================================

export const FrekSegmentSchema = z.object({
  t0: z.number().min(0),
  t1: z.number().min(0),
  h: z.string().regex(/^sha256:[a-f0-9]{64}$/, 'Hash must be sha256:<hex64>')
});

export const FrekMetadataSchema = z.object({
  timestamp: z.string().datetime({ offset: true }).or(z.string().datetime()),
  duration: z.number().positive(),
  source_type: z.enum(['live', 'studio', 'rehearsal', 'dispute'])
}).passthrough();

export const FrekDocumentSchema = z.object({
  frek_version: z.literal('0.4'),
  fingerprint: z.string().regex(/^sha256:[a-f0-9]{64}$/, 'Fingerprint must be sha256:<hex64>'),
  segments: z.array(FrekSegmentSchema).optional(),
  metadata: FrekMetadataSchema,
  signature: z.string().regex(/^ed25519:[A-Za-z0-9+/=]+$/, 'Signature must be ed25519:<base64>'),
  public_key: z.string().min(32, 'Public key must be base64 encoded')
});

// ============================================================================
// Canonicalization
// ============================================================================

/**
 * Canonicalize metadata for consistent hashing and signature verification.
 * Sorts keys alphabetically and produces deterministic JSON output.
 * @param {Object} metadata - Metadata object to canonicalize
 * @returns {string} Canonical JSON string
 */
export function canonicalize(metadata) {
  if (!metadata || typeof metadata !== 'object') {
    throw new Error('Invalid metadata: expected an object');
  }
  return JSON.stringify(metadata, Object.keys(metadata).sort(), 0);
}

// ============================================================================
// Cryptographic Functions
// ============================================================================

/**
 * Convert hex string to Uint8Array
 * @param {string} hex - Hex string
 * @returns {Uint8Array} Byte array
 */
function hexToBytes(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substr(i, 2), 16);
  }
  return bytes;
}

/**
 * Convert Uint8Array to hex string
 * @param {Uint8Array} bytes - Byte array
 * @returns {string} Hex string
 */
function bytesToHex(bytes) {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Verify Ed25519 signature
 * @param {string|Uint8Array} message - Message to verify (hex string or bytes)
 * @param {string} signatureBase64 - Base64 encoded signature
 * @param {string} publicKeyBase64 - Base64 encoded public key
 * @returns {{valid: boolean, error: string|null}}
 */
export function verifySignature(message, signatureBase64, publicKeyBase64) {
  try {
    let messageBytes;
    if (message instanceof Uint8Array) {
      messageBytes = message;
    } else if (typeof message === 'string' && /^[a-f0-9]{64}$/i.test(message)) {
      messageBytes = hexToBytes(message);
    } else if (typeof message === 'string') {
      messageBytes = new TextEncoder().encode(message);
    } else {
      throw new Error('Invalid message format');
    }
    
    const signatureBytes = decodeBase64(signatureBase64);
    const publicKeyBytes = decodeBase64(publicKeyBase64);
    
    if (signatureBytes.length !== 64) {
      return { valid: false, error: `Invalid signature length (got ${signatureBytes.length}, expected 64 bytes)` };
    }
    if (publicKeyBytes.length !== 32) {
      return { valid: false, error: `Invalid public key length (got ${publicKeyBytes.length}, expected 32 bytes)` };
    }
    
    const isValid = nacl.sign.detached.verify(messageBytes, signatureBytes, publicKeyBytes);
    return { valid: isValid, error: null };
  } catch (e) {
    return { valid: false, error: `Verification failed: ${e.message}` };
  }
}

/**
 * Generate SHA-256 hash using Web Crypto API
 * @param {string|Uint8Array} data - Data to hash
 * @returns {Promise<string>} Hex-encoded hash
 */
export async function sha256(data) {
  const encoder = new TextEncoder();
  const dataBuffer = typeof data === 'string' ? encoder.encode(data) : data;
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
  return bytesToHex(new Uint8Array(hashBuffer));
}

// ============================================================================
// Schema Validation
// ============================================================================

/**
 * Validate FREK JSON document against schema
 * @param {Object} data - FREK document to validate
 * @returns {{valid: boolean, data: Object|null, errors: Array}}
 */
export function validateSchema(data) {
  const result = FrekDocumentSchema.safeParse(data);
  if (result.success) {
    return { valid: true, data: result.data, errors: [] };
  } else {
    return { 
      valid: false, 
      data: null, 
      errors: result.error.errors.map(e => ({
        path: e.path.join('.'),
        message: e.message
      }))
    };
  }
}

// ============================================================================
// Audio Fingerprinting
// ============================================================================

/**
 * Audio Fingerprint Generator using Web Audio API and FFT
 * Implements a simplified spectral analysis for demo purposes.
 * 
 * Process:
 * 1. Decode audio to PCM
 * 2. Downsample to mono 22050Hz
 * 3. Apply windowed FFT analysis
 * 4. Extract spectral features
 * 5. Hash feature vector
 * 
 * @param {ArrayBuffer} audioBuffer - Raw audio file data
 * @param {Object} options - Configuration options
 * @param {number} options.sampleRate - Target sample rate (default: 22050)
 * @param {number} options.fftSize - FFT window size (default: 2048)
 * @param {number} options.hopSize - Hop size between windows (default: 1024)
 * @param {Function} options.onProgress - Progress callback
 * @returns {Promise<{fingerprint: string, segments: Array, duration: number}>}
 */
export async function hashAudio(audioBuffer, options = {}) {
  const {
    sampleRate = 22050,
    fftSize = 2048,
    hopSize = 1024,
    onProgress = () => {}
  } = options;

  onProgress(5, 'Initializing audio context');

  // Create offline audio context for processing
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  
  let audioData;
  try {
    onProgress(10, 'Decoding audio');
    audioData = await audioCtx.decodeAudioData(audioBuffer.slice(0));
  } catch (e) {
    throw new Error(`Failed to decode audio: ${e.message}`);
  }
  
  const duration = audioData.duration;
  onProgress(20, 'Audio decoded');

  // Get mono channel (average if stereo)
  const channelData = audioData.numberOfChannels > 1
    ? averageChannels(audioData)
    : audioData.getChannelData(0);

  onProgress(30, 'Downsampling');

  // Downsample to target sample rate
  const downsampledData = downsample(channelData, audioData.sampleRate, sampleRate);

  onProgress(40, 'Computing FFT');

  // Compute spectral features
  const features = computeSpectralFeatures(downsampledData, fftSize, hopSize, (p) => {
    onProgress(40 + Math.floor(p * 0.4), 'Analyzing spectrum');
  });

  onProgress(80, 'Generating segments');

  // Generate segment hashes (2-5 second windows as per FREK spec)
  const segmentDuration = 5; // seconds
  const samplesPerSegment = Math.floor(sampleRate * segmentDuration);
  const segments = [];
  
  for (let i = 0; i * samplesPerSegment < downsampledData.length; i++) {
    const start = i * samplesPerSegment;
    const end = Math.min(start + samplesPerSegment, downsampledData.length);
    const segmentData = downsampledData.slice(start, end);
    
    // Hash the segment's spectral features
    const segmentFeatures = computeSpectralFeatures(segmentData, fftSize, hopSize);
    const segmentHash = await sha256(new Float32Array(segmentFeatures).buffer);
    
    segments.push({
      t0: i * segmentDuration,
      t1: Math.min((i + 1) * segmentDuration, duration),
      h: `sha256:${segmentHash}`
    });
    
    if (segments.length >= 20) break; // Limit segments for demo
  }

  onProgress(90, 'Computing final fingerprint');

  // Compute overall fingerprint from all features
  const featureBuffer = new Float32Array(features).buffer;
  const fingerprint = await sha256(new Uint8Array(featureBuffer));

  await audioCtx.close();
  onProgress(100, 'Complete');

  return {
    fingerprint: `sha256:${fingerprint}`,
    segments,
    duration
  };
}

/**
 * Average multiple audio channels to mono
 * @param {AudioBuffer} audioData
 * @returns {Float32Array}
 */
function averageChannels(audioData) {
  const length = audioData.length;
  const result = new Float32Array(length);
  const numChannels = audioData.numberOfChannels;
  
  for (let c = 0; c < numChannels; c++) {
    const channelData = audioData.getChannelData(c);
    for (let i = 0; i < length; i++) {
      result[i] += channelData[i] / numChannels;
    }
  }
  
  return result;
}

/**
 * Downsample audio to target sample rate using linear interpolation
 * @param {Float32Array} data - Input audio data
 * @param {number} srcRate - Source sample rate
 * @param {number} dstRate - Target sample rate
 * @returns {Float32Array}
 */
function downsample(data, srcRate, dstRate) {
  if (srcRate === dstRate) return data;
  
  const ratio = srcRate / dstRate;
  const newLength = Math.floor(data.length / ratio);
  const result = new Float32Array(newLength);
  
  for (let i = 0; i < newLength; i++) {
    const srcIndex = i * ratio;
    const srcIndexFloor = Math.floor(srcIndex);
    const srcIndexCeil = Math.min(srcIndexFloor + 1, data.length - 1);
    const t = srcIndex - srcIndexFloor;
    
    result[i] = data[srcIndexFloor] * (1 - t) + data[srcIndexCeil] * t;
  }
  
  return result;
}

/**
 * Compute spectral features using windowed FFT
 * @param {Float32Array} data - Audio samples
 * @param {number} fftSize - FFT window size
 * @param {number} hopSize - Hop size
 * @param {Function} onProgress - Progress callback
 * @returns {Float32Array} Feature vector
 */
function computeSpectralFeatures(data, fftSize, hopSize, onProgress = () => {}) {
  const numFrames = Math.floor((data.length - fftSize) / hopSize) + 1;
  const numBands = 32; // Reduced frequency bands for fingerprinting
  const features = new Float32Array(numFrames * numBands);
  
  // Hann window
  const window = new Float32Array(fftSize);
  for (let i = 0; i < fftSize; i++) {
    window[i] = 0.5 * (1 - Math.cos(2 * Math.PI * i / (fftSize - 1)));
  }
  
  for (let frame = 0; frame < numFrames; frame++) {
    const start = frame * hopSize;
    
    // Extract and window the frame
    const frameData = new Float32Array(fftSize);
    for (let i = 0; i < fftSize; i++) {
      frameData[i] = (data[start + i] || 0) * window[i];
    }
    
    // Compute magnitude spectrum using simple DFT for key frequencies
    // This is a simplified version - real implementation would use FFT
    const spectrum = computeSimplifiedSpectrum(frameData, numBands);
    
    // Store band energies
    for (let b = 0; b < numBands; b++) {
      features[frame * numBands + b] = spectrum[b];
    }
    
    if (frame % 100 === 0) {
      onProgress(frame / numFrames);
    }
  }
  
  return features;
}

/**
 * Compute simplified spectrum for fingerprinting
 * Uses band energy analysis instead of full FFT
 * @param {Float32Array} frameData - Windowed audio frame
 * @param {number} numBands - Number of frequency bands
 * @returns {Float32Array} Band energies
 */
function computeSimplifiedSpectrum(frameData, numBands) {
  const n = frameData.length;
  const spectrum = new Float32Array(numBands);
  const bandSize = Math.floor(n / 2 / numBands);
  
  // Compute DFT for band center frequencies
  for (let band = 0; band < numBands; band++) {
    const k = Math.floor((band + 0.5) * bandSize);
    let real = 0, imag = 0;
    
    // Simplified DFT at frequency k
    const omega = 2 * Math.PI * k / n;
    for (let i = 0; i < n; i++) {
      real += frameData[i] * Math.cos(omega * i);
      imag -= frameData[i] * Math.sin(omega * i);
    }
    
    // Magnitude (log scale)
    const magnitude = Math.sqrt(real * real + imag * imag) / n;
    spectrum[band] = Math.log(1 + magnitude);
  }
  
  return spectrum;
}

// ============================================================================
// Report Generation
// ============================================================================

/**
 * Generate a verification report
 * @param {Object} params - Report parameters
 * @param {string} params.status - Verification status
 * @param {string} params.message - Result message
 * @param {Object} params.details - Verification details
 * @param {Object} params.frekData - Original FREK document (optional)
 * @param {Object} params.audioInfo - Audio file info (optional)
 * @returns {Object} Formatted report
 */
export function generateReport({ status, message, details, frekData = null, audioInfo = null }) {
  return {
    frek_verification_report: {
      version: '0.4',
      timestamp: new Date().toISOString(),
      status,
      message,
      details: {
        ...details,
        json_valid: details.json || null,
        signature_valid: details.signature || null,
        fingerprint_match: details.fingerprint || null
      },
      frek_metadata: frekData?.metadata || null,
      audio_file: audioInfo ? {
        name: audioInfo.name,
        size: audioInfo.size,
        type: audioInfo.type
      } : null
    }
  };
}

// ============================================================================
// Full Verification Pipeline
// ============================================================================

/**
 * Complete FREK verification pipeline
 * @param {Object} frekData - Parsed FREK JSON document
 * @param {ArrayBuffer} audioBuffer - Optional audio file for fingerprint comparison
 * @param {Function} onProgress - Progress callback
 * @returns {Promise<{valid: boolean, status: string, message: string, details: Object}>}
 */
export async function verifyFrek(frekData, audioBuffer = null, onProgress = () => {}) {
  const results = {
    json: null,
    signature: null,
    fingerprint: null
  };

  // Step 1: Validate JSON schema
  onProgress(10, 'Validating schema');
  const schemaResult = validateSchema(frekData);
  if (!schemaResult.valid) {
    return {
      valid: false,
      status: 'INVALID',
      message: 'Invalid FREK file structure',
      details: {
        json: 'Invalid',
        errors: schemaResult.errors
      }
    };
  }
  results.json = 'Valid';

  // Step 2: Verify signature
  onProgress(30, 'Verifying signature');
  const canonicalMetadata = canonicalize(frekData.metadata);
  const messageToVerify = frekData.fingerprint + canonicalMetadata;
  const messageHash = await sha256(messageToVerify);
  
  const signatureBase64 = frekData.signature.replace('ed25519:', '');
  const sigResult = verifySignature(messageHash, signatureBase64, frekData.public_key);
  
  if (!sigResult.valid) {
    return {
      valid: false,
      status: 'INVALID',
      message: 'Signature verification failed',
      details: {
        json: 'Valid',
        signature: 'Invalid',
        error: sigResult.error
      }
    };
  }
  results.signature = 'Valid';

  // Step 3: Compare fingerprint if audio provided
  if (audioBuffer) {
    onProgress(50, 'Computing audio fingerprint');
    
    try {
      const audioResult = await hashAudio(audioBuffer, {
        onProgress: (p, msg) => onProgress(50 + Math.floor(p * 0.4), msg)
      });
      
      onProgress(95, 'Comparing fingerprints');
      
      if (audioResult.fingerprint === frekData.fingerprint) {
        results.fingerprint = 'Match';
        return {
          valid: true,
          status: 'VERIFIED',
          message: 'Attestation verified. Audio fingerprint matches.',
          details: {
            ...results,
            timestamp: frekData.metadata?.timestamp,
            duration: frekData.metadata?.duration,
            source_type: frekData.metadata?.source_type,
            calculated_fingerprint: audioResult.fingerprint
          }
        };
      } else {
        return {
          valid: false,
          status: 'MODIFIED',
          message: 'Audio does not match the attestation fingerprint.',
          details: {
            ...results,
            fingerprint: 'Mismatch',
            expected: frekData.fingerprint,
            calculated: audioResult.fingerprint
          }
        };
      }
    } catch (e) {
      return {
        valid: false,
        status: 'ERROR',
        message: `Audio processing error: ${e.message}`,
        details: {
          ...results,
          error: e.message
        }
      };
    }
  }

  // No audio provided - signature valid
  onProgress(100, 'Complete');
  return {
    valid: true,
    status: 'VERIFIED',
    message: 'Attestation structure and signature verified.',
    details: {
      ...results,
      fingerprint: 'Not checked (no audio provided)',
      timestamp: frekData.metadata?.timestamp,
      duration: frekData.metadata?.duration,
      source_type: frekData.metadata?.source_type
    }
  };
}

// Export default object for convenience
export default {
  canonicalize,
  verifySignature,
  validateSchema,
  hashAudio,
  sha256,
  generateReport,
  verifyFrek
};
