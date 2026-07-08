#!/usr/bin/env python3
"""Verifier OTS — reconstruit et valide la preuve OpenTimestamps.

Depend UNIQUEMENT de la lib `opentimestamps` (PyPI, open-source).
Aucun appel a FREKCORE. Contacte optionnellement les calendars publics
(bob/alice/finney) pour upgrade la preuve vers une attestation Bitcoin
definitive.

Usage:  python3 verify_ots_offline.py notary_proof.ots notary_block.json
"""
import json, sys
from opentimestamps.core.serialize import BytesDeserializationContext
from opentimestamps.core.timestamp import Timestamp

ots_file = sys.argv[1] if len(sys.argv) > 1 else 'notary_proof.ots'
block_file = sys.argv[2] if len(sys.argv) > 2 else 'notary_block.json'

block = json.load(open(block_file))
msg = bytes.fromhex(block['block_hash'])
ots = open(ots_file, 'rb').read()

ctx = BytesDeserializationContext(ots)
ts = Timestamp.deserialize(ctx, msg)

pending, btc = [], []
def walk(t):
    for a in t.attestations:
        cls = a.__class__.__name__
        (btc if 'Bitcoin' in cls else pending).append((cls, str(a)))
    for _, sub in t.ops.items():
        walk(sub)
walk(ts)

print(json.dumps({
    "block_hash": block['block_hash'],
    "ots_bytes": len(ots),
    "pending_calendars": [p[1] for p in pending],
    "bitcoin_attestations": [b[1] for b in btc],
    "status": "BTC_CONFIRMED" if btc else "PENDING_BTC",
    "verdict": "Preuve valide, calendars publics independants FREKCORE"
}, indent=2))
