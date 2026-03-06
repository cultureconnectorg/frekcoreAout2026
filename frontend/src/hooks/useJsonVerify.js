import { useState, useCallback } from 'react';

/**
 * Hook for verifying .frek.json attestation files
 */
export function useJsonVerify() {
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const verifyJson = useCallback(async (text) => {
    setIsVerifying(true);
    setError(null);
    setResult(null);

    try {
      const data = JSON.parse(text);

      const checks = [
        {
          label: 'JSON valide',
          ok: true,
          warn: false
        },
        {
          label: 'frek_version',
          ok: data.frek_version === '0.4',
          warn: data.frek_version && data.frek_version !== '0.4'
        },
        {
          label: 'mix_id présent',
          ok: !!data.mix_id,
          warn: false
        },
        {
          label: 'Format FREK-ID',
          ok: data.mix_id && /^FREK-\d{4}-[A-Z]{2}-\d{3,}/.test(data.mix_id),
          warn: false
        },
        {
          label: 'Tracklist',
          ok: data.tracklist?.length > 0,
          warn: data.tracklist?.length === 0
        },
        {
          label: 'Fingerprint',
          ok: data.audio_fingerprint?.startsWith('frek:fp:'),
          warn: false
        },
        {
          label: 'Signature Ed25519',
          ok: data.signature?.startsWith('ed25519:'),
          warn: false
        },
        {
          label: 'Clé publique',
          ok: data.public_key?.startsWith('frek:pk:'),
          warn: false
        },
        {
          label: 'RFC 3161',
          ok: !!data.rfc3161_token,
          warn: !data.rfc3161_token
        },
        {
          label: 'Cosignature artiste',
          ok: !!data.artist?.signature,
          warn: !data.artist?.signature
        },
        {
          label: 'Cosignature organisateur',
          ok: !!data.event?.organizer?.signature,
          warn: !data.event?.organizer?.signature
        }
      ];

      const required = [
        'frek_version',
        'mix_id',
        'artist',
        'event',
        'tracklist',
        'audio_fingerprint',
        'signature',
        'public_key'
      ];
      const missing = required.filter((f) => !data[f]);
      const isValid = missing.length === 0;

      // Determine proof level
      let proofLevel = 'standard';
      if (data.rfc3161_token && data.bitcoin_anchor && data.operator) {
        proofLevel = 'strong';
      } else if (!data.rfc3161_token && !data.artist?.signature) {
        proofLevel = 'weak';
      }

      const verificationResult = {
        data,
        checks,
        missing,
        isValid,
        proofLevel,
        summary: {
          mixId: data.mix_id,
          artist: data.artist?.name,
          event: data.event?.name,
          date: data.event?.date,
          tracksCount: data.tracklist?.length || 0,
          fingerprint: data.audio_fingerprint,
        }
      };

      setResult(verificationResult);
      return verificationResult;
    } catch (err) {
      const errorResult = {
        data: null,
        checks: [{ label: 'JSON valide', ok: false, warn: false }],
        missing: [],
        isValid: false,
        error: err.message
      };
      setResult(errorResult);
      setError('JSON invalide: ' + err.message);
      return errorResult;
    } finally {
      setIsVerifying(false);
    }
  }, []);

  const reset = useCallback(() => {
    setIsVerifying(false);
    setResult(null);
    setError(null);
  }, []);

  return {
    verifyJson,
    isVerifying,
    result,
    error,
    reset,
  };
}

export default useJsonVerify;
