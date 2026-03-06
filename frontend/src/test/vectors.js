/**
 * Test vectors for FREK JSON verification
 * Contains valid and invalid test cases
 */

// Valid FREK v0.4 document with all required fields (standard proof level)
export const validFrekJson = {
  frek_version: '0.4',
  mix_id: 'FREK-2026-MQ-001',
  created_at: '2026-03-06T12:00:00.000Z',
  artist: {
    name: 'DJ Kathy',
    legal_name: 'Kathy-Liana Bravo',
    territory: 'MQ',
    signature: 'ed25519:artistsig123', // Added for standard proof level
  },
  event: {
    name: 'Culture Connect 2026',
    date: '2026-03-06',
    start_time: '22:00',
    venue: 'La Savane',
    city: 'Fort-de-France',
    context: 'live',
  },
  tracklist: [
    { position: 1, title: 'Zouk La Sé Sèl Médikaman', artist: 'Kassav\'' },
    { position: 2, title: 'Mwen Alé', artist: 'Jocelyne Béroard' },
  ],
  audio_fingerprint: 'frek:fp:a3f8c2d1e4b7f9a0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4',
  signature: 'ed25519:signature123456789abcdef',
  public_key: 'frek:pk:publickey123456789abcdef',
  timestamp: {
    captured_at: '2026-03-06T22:00:00.000Z',
    timezone: 'America/Martinique',
    source: 'device',
  },
  operator: {
    name: 'DJ Kathy',
    role: 'dj',
  },
};

// Valid minimal document (only required fields)
export const validMinimalFrekJson = {
  frek_version: '0.4',
  mix_id: 'FREK-2026-FR-100',
  artist: { name: 'Test DJ', territory: 'FR' },
  event: { name: 'Test Event', date: '2026-01-01', context: 'studio' },
  tracklist: [{ position: 1, title: 'Test Track', artist: 'Test Artist' }],
  audio_fingerprint: 'frek:fp:0000000000000000000000000000000000000000000000000000000000000000',
  signature: 'ed25519:testsignature',
  public_key: 'frek:pk:testpublickey',
};

// Strong proof level document
export const strongProofFrekJson = {
  ...validFrekJson,
  rfc3161_token: 'base64encodedtoken==',
  bitcoin_anchor: {
    txid: '0x123abc456def',
    block_height: 800000,
  },
};

// Weak proof level document (no signature verification possible)
export const weakProofFrekJson = {
  frek_version: '0.4',
  mix_id: 'FREK-2026-XX-999',
  artist: { name: 'Anonymous DJ' },
  event: { name: 'Unknown Event', date: '2026-01-01', context: 'live' },
  tracklist: [],
  audio_fingerprint: 'frek:fp:weak0000000000000000000000000000000000000000000000000000000000',
  signature: 'ed25519:weaksig',
  public_key: 'frek:pk:weakkey',
};

// Invalid: Missing frek_version
export const invalidMissingVersion = {
  mix_id: 'FREK-2026-MQ-001',
  artist: { name: 'DJ Test' },
  event: { name: 'Test Event', date: '2026-01-01', context: 'live' },
  tracklist: [],
  audio_fingerprint: 'frek:fp:test',
  signature: 'ed25519:test',
  public_key: 'frek:pk:test',
};

// Invalid: Wrong version
export const invalidWrongVersion = {
  frek_version: '0.3',
  mix_id: 'FREK-2026-MQ-001',
  artist: { name: 'DJ Test' },
  event: { name: 'Test Event', date: '2026-01-01', context: 'live' },
  tracklist: [],
  audio_fingerprint: 'frek:fp:test',
  signature: 'ed25519:test',
  public_key: 'frek:pk:test',
};

// Invalid: Bad FREK-ID format
export const invalidBadFrekId = {
  frek_version: '0.4',
  mix_id: 'INVALID-ID-FORMAT',
  artist: { name: 'DJ Test' },
  event: { name: 'Test Event', date: '2026-01-01', context: 'live' },
  tracklist: [],
  audio_fingerprint: 'frek:fp:test',
  signature: 'ed25519:test',
  public_key: 'frek:pk:test',
};

// Invalid: Missing required fields
export const invalidMissingFields = {
  frek_version: '0.4',
  mix_id: 'FREK-2026-MQ-001',
  // Missing: artist, event, tracklist, audio_fingerprint, signature, public_key
};

// Invalid: Bad fingerprint format
export const invalidBadFingerprint = {
  frek_version: '0.4',
  mix_id: 'FREK-2026-MQ-001',
  artist: { name: 'DJ Test' },
  event: { name: 'Test Event', date: '2026-01-01', context: 'live' },
  tracklist: [],
  audio_fingerprint: 'invalid-fingerprint-format',
  signature: 'ed25519:test',
  public_key: 'frek:pk:test',
};

// Invalid JSON string
export const invalidJsonString = 'this is not valid JSON {{{';

// Empty object
export const emptyObject = {};
