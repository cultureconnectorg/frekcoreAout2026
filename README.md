# FREK v0.4 — Musical Proof Standard

## FREKCORE backend verification

The FastAPI/MongoDB backend uses the exact dependency set in `backend/requirements.txt`.
For a reproducible local service, copy `backend/.env.example` to private `backend/.env`,
replace its placeholders with secret-manager values, and run `docker compose up --build`.
The container uses Python 3.12 and starts MongoDB plus the backend on port 8001.

Backend tests target `TEST_BACKEND_URL` (default `http://localhost:8001`) and require Mongo
plus explicit client secrets. After dependencies are installed, generate and verify the
versioned FastAPI contract with `python scripts/export_openapi.py` and
`python scripts/export_openapi.py --check`. The exporter does not enable public docs.

## Overview

FREK is an open protocol for verifying DJ mixes and musical performances. Cryptographic proof without surveillance.

**Website Architecture:**
- `/` — Public landing page
- `/docs` — Developer documentation
- `/app` — Verification tool
- `/industry` — Industry solutions

## Installation

### Prerequisites
- Node.js >= 18
- Yarn

### Local Development

```bash
cd frontend
yarn install
yarn start
```

Frontend runs on `http://localhost:3000`.

**Note**: Backend is optional and disabled by default. FREK operates entirely in the browser.

## Architecture

```
/app
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── PublicLanding.jsx    # / route
│   │   │   ├── Industry.jsx         # /industry route
│   │   │   ├── AppVerify.jsx        # /app route
│   │   │   └── docs/                # /docs/* routes
│   │   ├── components/
│   │   │   └── DocsLayout.jsx       # Docs sidebar layout
│   │   └── lib/
│   │       ├── frek-schema.js       # JSON validation (Zod)
│   │       └── crypto.js            # Ed25519 verification
│   └── package.json
├── backend/                          # Optional (disabled)
└── README.md
```

## Routes

| Route | Layer | Description |
|-------|-------|-------------|
| `/` | PUBLIC | Industry landing page |
| `/industry` | PUBLIC | Industry solutions |
| `/docs` | DOCS | Manifesto |
| `/docs/architecture` | DOCS | Technical pipeline |
| `/docs/spec` | DOCS | .frek.json specification |
| `/docs/governance` | DOCS | Governance model |
| `/docs/changelog` | DOCS | Version history |
| `/app` | APP | Verification tool |

## .frek.json Format

```json
{
  "frek_version": "0.4",
  "fingerprint": "sha256:<hex64>",
  "segments": [
    {"t0": 0, "t1": 5, "h": "sha256:<hex64>"}
  ],
  "metadata": {
    "timestamp": "ISO8601",
    "duration": 3600,
    "source_type": "live|studio|rehearsal|dispute"
  },
  "signature": "ed25519:<base64>",
  "public_key": "<base64>"
}
```

## Verification Module

The `/app` module performs:

1. **JSON Validation** — Structure against v0.4 schema
2. **Signature Verification** — Ed25519 cryptographic check
3. **Fingerprint Comparison** — Audio matching (optional)
4. **Report Export** — JSON verification report

**Important**: All processing is local. No data leaves the browser.

## Non-Negotiable Principles

1. FREK does not judge music
2. FREK does not rank artists
3. FREK does not collect personal data
4. FREK never becomes a platform
5. FREK works offline by default

## Limitations

- Demo fingerprint uses SHA-256 on raw data (not full spectral analysis)
- Version 0.4 is in development phase
- Segments are optional

## License

Open standard under copyleft license.

---

*FREK — An open protocol for verifying DJ mixes and musical performances.*
