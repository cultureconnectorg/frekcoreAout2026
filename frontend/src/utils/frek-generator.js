import { generateFrekId } from './frek-id';

/**
 * Calculate SHA-256 hash of a string
 * @param {string} text - Text to hash
 * @returns {Promise<string>} Hex-encoded hash
 */
async function sha256(text) {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Generate complete .frek.json document from wizard state
 * @param {object} state - Wizard state
 * @returns {Promise<object>} Complete FREK document
 */
export async function generateFrekJson(state) {
  const { artist, event, tracklist, audioFingerprint } = state;
  
  // Generate FREK-ID
  const mixId = generateFrekId(event.date, artist.territory);
  
  // Generate timestamp
  const createdAt = new Date().toISOString();
  
  // Build base document (without signature)
  const baseDocument = {
    frek_version: '0.4',
    mix_id: mixId,
    created_at: createdAt,
    artist: {
      name: artist.name,
      ...(artist.legal_name && { legal_name: artist.legal_name }),
      territory: artist.territory,
    },
    event: {
      name: event.name,
      date: event.date,
      ...(event.start_time && { start_time: event.start_time }),
      ...(event.venue && { venue: event.venue }),
      ...(event.city && { city: event.city }),
      context: event.context,
    },
    tracklist: tracklist.length > 0
      ? tracklist.map((track) => ({
          position: track.position,
          title: track.title,
          artist: track.artist,
          ...(track.isrc && { isrc: track.isrc }),
          ...(track.start_time && { start_time: track.start_time }),
        }))
      : [],
    audio_fingerprint: {
      method: audioFingerprint.method || 'sha256-raw',
      value: audioFingerprint.value || '',
      algorithm: audioFingerprint.algorithm || 'Manual entry',
      sample_rate: audioFingerprint.sample_rate || 44100,
      fft_size: audioFingerprint.fft_size || 2048,
    },
    timestamp: {
      captured_at: createdAt,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      source: 'device',
    },
    operator: {
      name: artist.name,
      role: 'dj',
    },
  };

  // Calculate self-signature (SHA-256 of the document)
  const documentString = JSON.stringify(baseDocument, null, 2);
  const signatureValue = await sha256(documentString);

  // Add signature to document
  const finalDocument = {
    ...baseDocument,
    signature: {
      method: 'sha256-self',
      value: signatureValue,
    },
  };

  return {
    document: finalDocument,
    mixId,
    createdAt,
    signatureValue,
  };
}

/**
 * Download JSON file
 * @param {object} document - FREK document
 * @param {string} filename - Filename to use
 */
export function downloadFrekJson(document, filename) {
  const jsonString = JSON.stringify(document, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  
  const link = window.document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  
  URL.revokeObjectURL(url);
}

/**
 * Copy JSON to clipboard
 * @param {object} document - FREK document
 * @returns {Promise<boolean>} Success status
 */
export async function copyFrekJson(document) {
  try {
    const jsonString = JSON.stringify(document, null, 2);
    await navigator.clipboard.writeText(jsonString);
    return true;
  } catch (err) {
    console.error('Failed to copy:', err);
    return false;
  }
}

/**
 * Validate wizard state before generation
 * @param {object} state - Wizard state
 * @returns {object} Validation result with errors
 */
export function validateWizardState(state) {
  const errors = {};
  
  // Artist validation
  if (!state.artist.name?.trim()) {
    errors.artistName = 'Le nom de scène est obligatoire';
  }
  if (!state.artist.territory) {
    errors.artistTerritory = 'Le territoire est obligatoire';
  }
  
  // Event validation
  if (!state.event.name?.trim()) {
    errors.eventName = "Le nom de l'événement est obligatoire";
  }
  if (!state.event.date) {
    errors.eventDate = 'La date est obligatoire';
  }
  if (!state.event.context) {
    errors.eventContext = 'Le contexte est obligatoire';
  }
  
  // Fingerprint validation (optional but show warning)
  if (!state.audioFingerprint.value) {
    errors.fingerprintWarning = "Aucune empreinte audio — valeur probatoire réduite";
  }
  
  return {
    isValid: Object.keys(errors).filter(k => !k.includes('Warning')).length === 0,
    errors,
  };
}

export default {
  generateFrekJson,
  downloadFrekJson,
  copyFrekJson,
  validateWizardState,
};
