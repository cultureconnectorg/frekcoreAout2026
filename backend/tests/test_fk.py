"""Tests FK — validation du contrat de survie.

Test fondamental : un .fk cree doit rester verifiable HORS LIGNE, sur toute machine,
sans DB ni serveur. C'est ce qui garantit la philosophie "objet culturel portable".
"""
import asyncio
import io
import zipfile
import json
import pytest

from fk.packager import create_fk, canonical_json, sha256_hex
from fk.validator import validate_fk, summary


@pytest.mark.asyncio
async def test_create_fk_minimal():
    """Un FK minimal (sans media) doit s'assembler et etre valide."""
    fk_bytes, fk_obj = await create_fk(
        title="Test song",
        object_type="song",
        primary_creator_name="Alice",
    )
    assert fk_obj.manifest.frek_id.startswith("fk-")
    assert len(fk_bytes) > 0

    # Verifier que c'est un ZIP valide
    zf = zipfile.ZipFile(io.BytesIO(fk_bytes))
    names = set(zf.namelist())
    assert "manifest.fk.json" in names
    assert "metadata/identity.json" in names
    assert "proof/frekcore-attestation.json" in names

    report = validate_fk(fk_bytes)
    assert report["valid"] is True, f"Report: {report}"
    assert report["frek_id"] == fk_obj.manifest.frek_id
    assert report["creator"] == "Alice"
    assert report["title"] == "Test song"


@pytest.mark.asyncio
async def test_create_fk_with_media():
    """Un FK avec plusieurs medias doit inclure et hasher chaque fichier."""
    audio = b"RIFF" + b"\x00" * 100  # fake WAV header
    image = bytes.fromhex("89504E470D0A1A0A") + b"\x00" * 50  # fake PNG

    fk_bytes, fk_obj = await create_fk(
        title="Concert Bataclan",
        object_type="event",
        primary_creator_name="Artiste X",
        media_files=[
            ("song.wav", audio, "audio/wav"),
            ("photo.png", image, "image/png"),
        ],
    )

    assert len(fk_obj.media.items) == 2
    kinds = {i.kind for i in fk_obj.media.items}
    assert kinds == {"audio", "image"}

    report = validate_fk(fk_bytes)
    assert report["valid"] is True, f"Errors: {report['errors']}"
    assert report["media_count"] == 2


@pytest.mark.asyncio
async def test_survival_offline_verification():
    """
    TEST DE SURVIE FONDAMENTAL :
    Un .fk cree doit rester verifiable hors ligne, sans DB, sans reseau.

    Simulation : on cree le .fk, on jette la reference, et on le rouvre
    dans un contexte totalement propre. L'identite doit etre preservee.
    """
    fk_bytes, fk_obj = await create_fk(
        title="Œuvre patrimoniale",
        object_type="heritage",
        primary_creator_name="Musée du Quai Branly",
        description="Objet du fonds",
        context={"location": "Paris", "date": "2026-07-08"},
        media_files=[("scan.pdf", b"%PDF-1.4\n" + b"x" * 200, "application/pdf")],
    )

    original_frek_id = fk_obj.manifest.frek_id
    original_root = fk_obj.proof.root_hash
    del fk_obj  # oublie totalement l'objet original

    # Verification "cold" — comme si on rechargeait le .fk sur une autre machine
    report = validate_fk(fk_bytes)

    assert report["valid"] is True, f"Survival test FAIL: {report['errors']}"
    assert report["frek_id"] == original_frek_id
    assert report["creator"] == "Musée du Quai Branly"
    assert report["object_type"] == "heritage"
    # La signature s'est verifiee avec la cle publique EMBARQUEE dans le .fk
    sig_check = next(c for c in report["checks"] if c["check"] == "signature_valid")
    assert sig_check["ok"] is True


@pytest.mark.asyncio
async def test_tampering_detected_manifest():
    """Une modification du manifest doit invalider la signature."""
    fk_bytes, fk_obj = await create_fk(
        title="Original", object_type="song", primary_creator_name="Bob",
    )
    # Reouvrir le zip, modifier le manifest, recreer
    zin = zipfile.ZipFile(io.BytesIO(fk_bytes))
    buf = io.BytesIO()
    zout = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)
    for name in zin.namelist():
        data = zin.read(name)
        if name == "manifest.fk.json":
            m = json.loads(data.decode())
            m["object_type"] = "FAKE"  # tamper !
            data = canonical_json(m).encode("utf-8")
        zout.writestr(name, data)
    zout.close()

    report = validate_fk(buf.getvalue())
    assert report["valid"] is False
    # Le hash du manifest doit avoir change -> layer_hash_manifest doit echouer
    manifest_check = next(c for c in report["checks"]
                          if c["check"] == "layer_hash_manifest")
    assert manifest_check["ok"] is False


@pytest.mark.asyncio
async def test_tampering_detected_media():
    """Une modification d'un media doit invalider l'integrite."""
    fk_bytes, fk_obj = await create_fk(
        title="Song", object_type="song", primary_creator_name="Carol",
        media_files=[("song.wav", b"RIFF" + b"\x00" * 100, "audio/wav")],
    )
    zin = zipfile.ZipFile(io.BytesIO(fk_bytes))
    buf = io.BytesIO()
    zout = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)
    for name in zin.namelist():
        data = zin.read(name)
        if name.startswith("media/audio/"):
            data = b"TAMPERED"
        zout.writestr(name, data)
    zout.close()

    report = validate_fk(buf.getvalue())
    assert report["valid"] is False
    media_check = next(c for c in report["checks"] if c["check"] == "media_integrity")
    assert media_check["ok"] is False


@pytest.mark.asyncio
async def test_canonical_json_deterministic():
    """Le JSON canonique doit etre stable — sinon les hashes deviennent instables."""
    a = {"z": 1, "a": {"y": 2, "b": 3}}
    b = {"a": {"b": 3, "y": 2}, "z": 1}
    assert canonical_json(a) == canonical_json(b)
    assert sha256_hex(canonical_json(a).encode()) == sha256_hex(canonical_json(b).encode())


@pytest.mark.asyncio
async def test_frek_id_prefix():
    """Les FK-ID doivent commencer par fk- pour se distinguer des m- (moments)."""
    _, obj = await create_fk(title="x", object_type="song", primary_creator_name="y")
    assert obj.manifest.frek_id.startswith("fk-")
    # 2 chars prefix + 12hex + 4hex + 2 tirets = 2 + 12 + 4 + 2 = 20 chars
    assert len(obj.manifest.frek_id) == 20
