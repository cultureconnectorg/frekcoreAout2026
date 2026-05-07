"""FREK DID — Methode `did:frek:{frek_id}` + W3C Verifiable Credentials.

Phase 4 — interop eIDAS 2.0 / EUDI Wallet.

Modele :
- DID = `did:frek:{frek_id}` (identifiant decentralise W3C DID Core 1.0)
- DID Document : verificationMethod base sur la cle Ed25519 du module passport (memes
  garanties cryptographiques que les passeports — meme racine de confiance)
- Verifiable Credential V2 (W3C VC Data Model 2.0) avec proof DataIntegrityProof
  type=DataIntegrityProof / cryptosuite=eddsa-jcs-2022 (RFC 8785 JCS)

Endpoints :
    GET /api/v1/did/{frek_id}     DID Document JSON-LD
    GET /api/v1/vc/{frek_id}      Verifiable Credential signe (cultural identity)
    GET /api/v1/did/method/spec   Methode `did:frek` documentee

Aucun secret expose. Verification offline avec la cle publique uniquement.
"""
