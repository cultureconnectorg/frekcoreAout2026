#!/usr/bin/env python3
"""FREK NFC Encoder — script CLI pour encoder des tags NTAG215/NTAG216.

Usage local terrain :
  python scripts/nfc_encode.py --frek-id FREK-XXXX
  python scripts/nfc_encode.py --batch badges.csv  # csv avec colonne frek_id

Prerequis :
  pip install ndeflib pyscard nfcpy   (selon ton lecteur)
  Lecteur PC/SC ou ACR122U recommande sur Linux/macOS.

Le script encode l'URI `https://frekcore.com/card/{frek_id}` en NDEF record URI.
Au tap sur smartphone (Android/iOS Safari), ouvre directement la FREK Card virtuelle.

NB: ce script ne fait PAS d'appel reseau. Il ne modifie rien cote serveur.
Il prepare uniquement le contenu NDEF a ecrire sur le tag.
"""
import argparse
import csv
import sys
from pathlib import Path

DEFAULT_BASE_URL = "https://frekcore.com/card"


def build_uri(frek_id: str, base_url: str = DEFAULT_BASE_URL) -> str:
    return f"{base_url.rstrip('/')}/{frek_id.strip()}"


def encode_uri_to_ndef(uri: str) -> bytes:
    """Construit un NDEF Message contenant un URI Record (RTD URI).

    Format NDEF :
      [TLV NDEF tag 0x03]
      [length]
      [record header 0xD1 | type_length 0x01 | payload_length | type 'U']
      [URI identifier code 0x00 (pas de prefix)]
      [URI bytes]
      [TLV terminator 0xFE]
    """
    uri_bytes = uri.encode("utf-8")
    payload = b"\x00" + uri_bytes  # 0x00 = pas d'abbreviation
    record_header = 0xD1  # MB=1, ME=1, CF=0, SR=1, IL=0, TNF=1 (Well-known)
    type_length = 0x01
    payload_length = len(payload)
    record = bytes([record_header, type_length, payload_length]) + b"U" + payload

    msg = record
    ndef_tlv = bytes([0x03, len(msg)]) + msg + bytes([0xFE])
    return ndef_tlv


def write_tag_via_nfcpy(ndef_bytes: bytes, dry_run: bool = False) -> bool:
    """Tente d'ecrire sur un tag via nfcpy (PN532, ACR122U).

    Si dry-run : affiche seulement le hex.
    """
    if dry_run:
        print("DRY-RUN — bytes a graver sur le tag (hex):")
        print(ndef_bytes.hex())
        return True
    try:
        import nfc  # type: ignore  # noqa: F401
    except ImportError:
        print("ERROR: nfcpy n'est pas installe (pip install nfcpy).")
        return False
    # Note : implementation reelle terrain depend du lecteur.
    # Cette stub montre la structure ; il faut adapter selon votre matos.
    print("INFO: place le tag NTAG215 sur le lecteur dans les 5 secondes...")
    print(f"NDEF bytes ({len(ndef_bytes)}o):", ndef_bytes.hex())
    print("INFO: utiliser ndef + tag.ndef.records = [Record(...)] selon nfcpy doc.")
    return True


def main():
    p = argparse.ArgumentParser(description="Encode FREK Card NFC NTAG215")
    p.add_argument("--frek-id", help="Un seul FREK-ID a encoder")
    p.add_argument("--batch", help="CSV avec colonne 'frek_id' (header)")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"Base URL (default: {DEFAULT_BASE_URL})")
    p.add_argument("--dry-run", action="store_true", help="N'ecrit rien, affiche le NDEF hex.")
    args = p.parse_args()

    if not args.frek_id and not args.batch:
        p.error("Specifier --frek-id ou --batch")

    ids = []
    if args.frek_id:
        ids.append(args.frek_id)
    if args.batch:
        path = Path(args.batch)
        if not path.exists():
            print(f"ERROR: fichier introuvable {path}")
            sys.exit(2)
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ids.extend(row["frek_id"].strip() for row in reader if row.get("frek_id"))

    print(f"FREK NFC encoder — {len(ids)} tag(s) a graver")
    for frek_id in ids:
        uri = build_uri(frek_id, base_url=args.base_url)
        ndef_bytes = encode_uri_to_ndef(uri)
        print(f"\n--- {frek_id} ---")
        print(f"URI: {uri}")
        print(f"NDEF length: {len(ndef_bytes)} bytes")
        write_tag_via_nfcpy(ndef_bytes, dry_run=args.dry_run)
        if not args.dry_run:
            input("Tag suivant — appuyer sur Entree apres avoir change le tag...")


if __name__ == "__main__":
    main()
