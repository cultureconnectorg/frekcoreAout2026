export const specFields = [
  { name: 'frek_version', type: 'string', required: true, desc: 'Version du schéma (ex: "0.4")' },
  { name: 'mix_id', type: 'string', required: true, desc: 'Identifiant unique FREK-YYYY-XX-NNN' },
  { name: 'created_at', type: 'datetime', required: true, desc: 'Date de création ISO 8601' },
  { name: 'artist', type: 'object', required: true, desc: 'Nom, territoire, identifiants' },
  { name: 'event', type: 'object', required: true, desc: 'Nom, date, lieu de la performance' },
  { name: 'tracklist', type: 'array', required: true, desc: 'Liste des œuvres du mix' },
  { name: 'audio_fingerprint', type: 'string', required: true, desc: 'Empreinte frek:fp:[sha256]' },
  { name: 'proof_level', type: 'string', required: false, desc: 'Niveau: strong/standard/weak' },
  { name: 'capture_device', type: 'string', required: false, desc: 'Source: frek_node/go/...' },
  { name: 'rfc3161_token', type: 'string', required: false, desc: 'Horodatage légal TSA' },
  { name: 'bitcoin_anchor', type: 'object', required: false, desc: 'Ancrage blockchain BTC' },
  { name: 'operator', type: 'object', required: false, desc: 'Opérateur certifié FREK' },
  { name: 'jurisdiction', type: 'string', required: false, desc: 'Juridiction (défaut: WIPO-CAM)' },
  { name: 'signature', type: 'string', required: true, desc: 'Signature ed25519:[hex]' },
  { name: 'public_key', type: 'string', required: true, desc: 'Clé publique frek:pk:[hex]' },
];

export const sampleFrekJson = `{
  "frek_version": "0.4",
  "mix_id": "FREK-2026-MQ-001",
  "created_at": "2026-05-22T23:30:00Z",
  "artist": {
    "name": "DJ Chimin",
    "territory": "MQ",
    "isni": "0000000012345678",
    "signature": "ed25519:abc123..."
  },
  "event": {
    "name": "Culture Connect 2026",
    "date": "2026-05-22",
    "location": "Fort-de-France, MQ",
    "organizer": {
      "name": "CVLN Group",
      "signature": "ed25519:def456..."
    }
  },
  "tracklist": [
    { "position": 1, "title": "Intro", "isrc": null },
    { "position": 2, "title": "Track 01", "isrc": "FRXXX0012345" }
  ],
  "audio_fingerprint": "frek:fp:a3f2b1c4d5e6f7...",
  "proof_level": "strong",
  "capture_device": "frek_node_v1",
  "rfc3161_token": "MIIBxTCCAW0...",
  "bitcoin_anchor": {
    "txid": "abc123...",
    "block": 850000,
    "merkle_root": "def456..."
  },
  "operator": {
    "id": "OP-001",
    "name": "Festival Ops",
    "certification": "frek:cert:2026"
  },
  "jurisdiction": "WIPO-CAM",
  "signature": "ed25519:ccddee3344...",
  "public_key": "frek:pk:aabbccdd..."
}`;
