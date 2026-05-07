"""FREK EUDI — Plugin OpenID for Verifiable Credentials Issuance (OID4VCI).

Phase 4.5 — pont vers l'identite numerique europeenne.

Standards :
- OpenID4VCI Draft 13+ (OpenID for Verifiable Credentials Issuance)
- OAuth 2.0 Authorization Server Metadata (RFC 8414)
- Pre-authorized code flow (sans authentication interactive)

Flow utilisateur :
1. Le porteur clique "Importer dans mon EUDI Wallet" sur /verify/{frek_id}
2. Backend genere un credential offer signe avec pre-authorized_code (TTL 5 min, single-use)
3. Le porteur scanne le QR code → wallet parse `openid-credential-offer://...`
4. Wallet POST /token avec le code → recoit access_token JWT (TTL 5 min)
5. Wallet POST /credential avec le token → recoit le VC W3C signe Ed25519
6. VC importe dans le wallet, presentable n'importe ou en Europe

Aucun breaking change : reutilise le module did/vc.py existant.
"""
