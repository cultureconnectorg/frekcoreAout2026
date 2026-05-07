# FREK Passport — Verifier offline standalone

Verification cryptographique d'un `passport.json` FREK **sans aucune connexion** a FREKCORE.

Deux flavors :

| Flavor | Fichier | Dependance |
|---|---|---|
| Python CLI | `python/verify_passport.py` | `cryptography` (PyPI, pre-installe partout) |
| ES module / Browser | `js/verify_passport.js` | aucune (Web Crypto API native) |

## Pre-requis : la cle publique

Recuperer la cle publique une seule fois (peut etre archivee, distribuee hors-ligne) :

```bash
curl https://frekcore.com/api/v1/passport/key
```

Reponse :
```json
{
  "key_id": "frek-passport-v1",
  "algorithm": "Ed25519",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n",
  "public_key_raw_b64": "Crgwxp..."
}
```

## Python

```bash
# Avec la cle PEM
python verify_passport.py --passport passport.json --public-key key.pem

# Ou avec la cle raw base64
python verify_passport.py --passport passport.json --public-key-b64 "Crgwxp..."
```

Sortie :
```json
{
  "valid": true,
  "mode": "full",
  "errors": [],
  "envelope": {...},
  "claims": [...]
}
```

Exit code `0` si valide, `1` sinon.

## JavaScript (navigateur ou Node 20+)

```javascript
import { verifyPassport } from "./verify_passport.js";

const passport = await fetch("/passport.json").then(r => r.json());
const pubKeyB64 = "Crgwxp..."; // archivee / hardcodee

const result = await verifyPassport(passport, pubKeyB64);
console.log(result.valid, result.errors);
```

Demo navigateur : ouvrir `js/demo.html` dans un navigateur moderne (Chrome 113+, Firefox 130+, Safari 17+).

## Disclosure selective

Le porteur peut generer un sous-passeport ne contenant qu'une partie des claims. Le verifier accepte les deux formats (`disclosure: "full"` ou `"partial"`) sans configuration.

## Garanties

- **Signature** : Ed25519 (RFC 8032) sur `canonical_json(envelope)`.
- **Integrite** : SHA-256 + Merkle binaire. Toute modification d'un claim ou de l'envelope invalide la verification.
- **Souverainete** : aucun appel reseau a FREKCORE. Tant que la cle publique est conservee, la verification fonctionne meme si frekcore.com disparait.

## Specification

Voir `/api/v1/spec/v1.0.0` section `passport`.
