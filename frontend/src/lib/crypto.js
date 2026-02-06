import nacl from 'tweetnacl';
import { decodeBase64, encodeBase64, decodeUTF8 } from 'tweetnacl-util';

// Convert hex string to Uint8Array
function hexToBytes(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substr(i, 2), 16);
  }
  return bytes;
}

// Verify Ed25519 signature
// message can be: Uint8Array, hex string (64 chars), or regular string
export function verifySignature(message, signatureBase64, publicKeyBase64) {
  try {
    let messageBytes;
    if (message instanceof Uint8Array) {
      messageBytes = message;
    } else if (typeof message === 'string' && /^[a-f0-9]{64}$/i.test(message)) {
      // It's a hex string (SHA-256 hash)
      messageBytes = hexToBytes(message);
    } else {
      messageBytes = decodeUTF8(message);
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

// Generate SHA-256 hash (browser native) - returns hex string
export async function sha256(data) {
  const encoder = new TextEncoder();
  const dataBuffer = typeof data === 'string' ? encoder.encode(data) : data;
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Generate SHA-256 hash and return as Uint8Array (for signing)
export async function sha256Bytes(data) {
  const encoder = new TextEncoder();
  const dataBuffer = typeof data === 'string' ? encoder.encode(data) : data;
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
  return new Uint8Array(hashBuffer);
}

// Generate keypair for demo/testing
export function generateKeyPair() {
  const keyPair = nacl.sign.keyPair();
  return {
    publicKey: encodeBase64(keyPair.publicKey),
    secretKey: encodeBase64(keyPair.secretKey)
  };
}

// Sign message for demo/testing
export function signMessage(message, secretKeyBase64) {
  try {
    const messageBytes = typeof message === 'string' ? decodeUTF8(message) : message;
    const secretKeyBytes = decodeBase64(secretKeyBase64);
    const signature = nacl.sign.detached(messageBytes, secretKeyBytes);
    return { signature: encodeBase64(signature), error: null };
  } catch (e) {
    return { signature: null, error: `Signing failed: ${e.message}` };
  }
}

// Demo fingerprint calculation (simplified FFT-based approach)
// In production, this would use proper audio analysis
export async function calculateDemoFingerprint(audioArrayBuffer) {
  // For demo purposes: hash the raw audio data
  // Real implementation would use spectral analysis (FFT) + perceptual hashing
  const hashHex = await sha256(new Uint8Array(audioArrayBuffer));
  return `sha256:${hashHex}`;
}

// Generate demo segments from audio
export async function generateDemoSegments(audioArrayBuffer, segmentDuration = 5) {
  const segments = [];
  const totalDuration = audioArrayBuffer.byteLength / (44100 * 2); // Rough estimate
  const numSegments = Math.ceil(totalDuration / segmentDuration);
  
  const chunkSize = Math.floor(audioArrayBuffer.byteLength / numSegments);
  const view = new Uint8Array(audioArrayBuffer);
  
  for (let i = 0; i < numSegments && i < 20; i++) { // Limit to 20 segments for demo
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, audioArrayBuffer.byteLength);
    const chunk = view.slice(start, end);
    const hash = await sha256(chunk);
    segments.push({
      t0: i * segmentDuration,
      t1: (i + 1) * segmentDuration,
      h: `sha256:${hash}`
    });
  }
  
  return segments;
}
