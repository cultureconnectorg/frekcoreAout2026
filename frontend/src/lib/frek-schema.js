import { z } from 'zod';

// FREK v0.4 JSON Schema
export const FrekSegmentSchema = z.object({
  t0: z.number().min(0),
  t1: z.number().min(0),
  h: z.string().regex(/^sha256:[a-f0-9]{64}$/, 'Hash must be sha256:<hex64>')
});

export const FrekMetadataSchema = z.object({
  timestamp: z.string().datetime({ offset: true }).or(z.string().datetime()),
  duration: z.number().positive(),
  source_type: z.enum(['live', 'studio', 'rehearsal', 'dispute'])
}).passthrough(); // Allow additional non-PII fields

export const FrekDocumentSchema = z.object({
  frek_version: z.literal('0.4'),
  fingerprint: z.string().regex(/^sha256:[a-f0-9]{64}$/, 'Fingerprint must be sha256:<hex64>'),
  segments: z.array(FrekSegmentSchema).optional(),
  metadata: FrekMetadataSchema,
  signature: z.string().regex(/^ed25519:[A-Za-z0-9+/=]+$/, 'Signature must be ed25519:<base64>'),
  public_key: z.string().min(32, 'Public key must be base64 encoded')
});

// Validate FREK JSON
export function validateFrekJson(data) {
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

// Canonicalize metadata for signature verification
// The signed message is: fingerprint + canonical(metadata)
// This ensures only the core attestation data is signed
export function canonicalizeMetadata(metadata) {
  return JSON.stringify(metadata, Object.keys(metadata).sort(), 0);
}

// Example valid FREK document for testing
export const EXAMPLE_FREK_DOC = {
  frek_version: "0.4",
  fingerprint: "sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
  segments: [
    { t0: 0, t1: 5, h: "sha256:1111111111111111111111111111111111111111111111111111111111111111" },
    { t0: 5, t1: 10, h: "sha256:2222222222222222222222222222222222222222222222222222222222222222" }
  ],
  metadata: {
    timestamp: "2024-04-20T15:30:00Z",
    duration: 3600,
    source_type: "live"
  },
  signature: "ed25519:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
  public_key: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
};
