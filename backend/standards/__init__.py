"""FREK Standards — Manifest universel de compatibilite.

Phase 4.5 — pont vers les ecosystemes mondiaux d'identite numerique.

Documente et expose la conformite FREKCORE avec :
- W3C DID Core 1.0 + DID Methods Registry
- W3C VC Data Model 2.0
- DIF Well-Known DID Configuration (preuve domain-DID lien)
- OpenID4VCI / OID4VP (EUDI Wallet)
- ISO mDL (mobile driving license — preparation USA roadmap)
- ID4Africa Principles (Africa Continental Free Trade Area, ITU pays en developpement)
- ITU-T X.509 / SP 800-63 (NIST identity assurance levels)

Endpoints :
    GET /api/.well-known/jwks.json                JWK Set Ed25519 universel
    GET /api/.well-known/did-configuration.json   DIF DID Configuration
    GET /api/v1/standards/manifest                Manifest declaratif global
    GET /api/v1/standards/{ecosystem}             Mapping detaille par ecosysteme
"""
