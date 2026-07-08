"""FK Packager — assemble un .fk (ZIP) a partir des couches en memoire.

Etapes de creation :
1. Generer FREK-ID (fk-{12hex}-{4hex})
2. Assembler les 7 couches JSON canonicalisees
3. Calculer SHA-256 de chaque couche
4. Calculer root_hash = SHA-256 des layer_hashes canonicalisees
5. Signer root_hash avec Ed25519 (cle passport reutilisee)
6. Notariser dans FREK-Chain (block)
7. Emballer en ZIP avec structure normalisee
"""
import base64
import hashlib
import io
import json
import logging
import secrets
import zipfile
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from passport import keys as passport_keys

from .models import (
    FK_VERSION, MediaItem, IdentityLayer, CreatorsLayer, TimelineLayer,
    MediaLayer, IntelligenceLayer, RightsLayer, ProofLayer,
    ManifestFK, AttestationRef, BlockRef, LayersMap, Version, FKObject,
)

logger = logging.getLogger("frek.fk.packager")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_frek_id() -> str:
    """fk-{12hex}-{4hex} — distinct de m-* (moments) et des ID stage-based."""
    return f"fk-{secrets.token_hex(6)}-{secrets.token_hex(2)}"


def canonical_json(data: Any) -> str:
    """JSON deterministe : cles triees, pas d'espaces, UTF-8."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of_json(obj: Any) -> str:
    return sha256_hex(canonical_json(obj).encode("utf-8"))


def _detect_kind(content_type: str) -> str:
    if content_type.startswith("audio/"):
        return "audio"
    if content_type.startswith("video/"):
        return "video"
    if content_type.startswith("image/"):
        return "image"
    if content_type in ("application/pdf",) or content_type.startswith("text/"):
        return "document"
    return "data"


def _safe_name(name: str) -> str:
    """Nettoie un nom de fichier pour usage dans le ZIP."""
    keep = "-_.()[] "
    cleaned = "".join(c for c in name if c.isalnum() or c in keep).strip()
    return cleaned or "file"


def _ext_for(content_type: str, fallback: str = "bin") -> str:
    mapping = {
        "audio/mpeg": "mp3", "audio/mp3": "mp3",
        "audio/wav": "wav", "audio/x-wav": "wav", "audio/wave": "wav",
        "audio/flac": "flac", "audio/webm": "webm", "audio/ogg": "ogg",
        "audio/mp4": "m4a", "audio/aac": "aac",
        "video/mp4": "mp4", "video/quicktime": "mov", "video/webm": "webm",
        "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif",
        "application/pdf": "pdf",
        "text/plain": "txt", "text/markdown": "md",
    }
    return mapping.get(content_type, fallback)


def build_media_layer(files: List[Tuple[str, bytes, str]]) -> Tuple[MediaLayer, Dict[str, bytes]]:
    """
    files : list de (original_name, bytes, content_type).
    Retourne (MediaLayer, {zip_path: bytes}) — les bytes a ecrire dans le ZIP.
    """
    items: List[MediaItem] = []
    zip_files: Dict[str, bytes] = {}
    for i, (orig_name, data, ctype) in enumerate(files):
        kind = _detect_kind(ctype)
        ext = _ext_for(ctype, "bin")
        safe = _safe_name(orig_name.rsplit(".", 1)[0])[:60] or f"item_{i}"
        # Chemin final dans le ZIP
        zip_path = f"media/{kind}/{i:02d}_{safe}.{ext}"
        zip_files[zip_path] = data
        items.append(MediaItem(
            path=zip_path,
            content_type=ctype,
            size=len(data),
            sha256=sha256_hex(data),
            kind=kind,
            original_name=orig_name,
        ))
    return MediaLayer(items=items), zip_files


def _compute_layer_hashes(
    manifest: ManifestFK,
    identity: IdentityLayer,
    creators: CreatorsLayer,
    timeline: TimelineLayer,
    media: MediaLayer,
    intelligence: IntelligenceLayer,
    rights: RightsLayer,
) -> Dict[str, str]:
    return {
        "manifest": sha256_of_json(manifest.model_dump()),
        "identity": sha256_of_json(identity.model_dump()),
        "creators": sha256_of_json(creators.model_dump()),
        "timeline": sha256_of_json(timeline.model_dump()),
        "media": sha256_of_json(media.model_dump()),
        "intelligence": sha256_of_json(intelligence.model_dump()),
        "rights": sha256_of_json(rights.model_dump()),
    }


def _compute_root_hash(layer_hashes: Dict[str, str]) -> str:
    return sha256_of_json(layer_hashes)


async def create_fk(
    *,
    title: str,
    object_type: str,
    primary_creator_name: str,
    primary_creator_role: Optional[str] = "creator",
    contributors: Optional[List[Dict[str, Any]]] = None,
    description: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    external_refs: Optional[Dict[str, str]] = None,
    media_files: Optional[List[Tuple[str, bytes, str]]] = None,
    rights_owner_name: Optional[str] = None,
) -> Tuple[bytes, FKObject]:
    """
    Cree un .fk en memoire (bytes ZIP) + retourne l'objet FKObject complet.

    Signature Ed25519 embarquee (verifiable offline). Block FREK-Chain
    optionnel — cree si notary service disponible.
    """
    frek_id = generate_frek_id()
    now = _now_iso()

    # 1. Assemble les couches en memoire (sauf preuve)
    identity = IdentityLayer(
        frek_id=frek_id,
        title=title,
        object_type=object_type,
        description=description,
        context=context or {},
        external_refs=external_refs or {},
    )
    creators = CreatorsLayer(
        primary_creator={"name": primary_creator_name, "role": primary_creator_role},
        contributors=[{"name": c.get("name", ""), "role": c.get("role")}
                      for c in (contributors or [])],
    )
    timeline = TimelineLayer(
        created_at=now,
        description=description,
        versions=[Version(version="1.0", created_at=now, note="Creation initiale")],
    )
    media_layer, media_files_map = build_media_layer(media_files or [])
    intelligence = IntelligenceLayer()  # vide en v0.1
    rights = RightsLayer(
        owner={"name": rights_owner_name, "role": "owner"} if rights_owner_name else None,
    )

    # 2. Notarise DABORD pour obtenir block_hash — puis on fige le manifest
    block_info = None
    block_hash_str: Optional[str] = None
    try:
        from notary.service import notarize_event
        blk = await notarize_event(
            payload_type="fk_created",
            payload_id=frek_id,
            payload_data={
                "frek_id": frek_id,
                "object_type": object_type,
                "title_hash": sha256_hex(title.encode("utf-8")),
                "created_at": now,
                "media_count": len(media_layer.items),
            },
            metadata={"fk_version": FK_VERSION, "signature_algo": "ed25519"},
        )
        if blk and isinstance(blk, dict):
            block_hash_str = blk.get("block_hash")
            block_info = BlockRef(
                block_hash=block_hash_str,
                height=blk.get("height"),
                created_at=blk.get("created_at"),
            )
    except Exception as e:
        logger.warning(f"FK notarisation skipped ({frek_id}): {e}")

    # 3. Manifest racine (attestation_ref FIGE avant hashage)
    manifest = ManifestFK(
        frek_id=frek_id,
        object_type=object_type,
        created_at=now,
        layers=LayersMap(),
        attestation_ref=AttestationRef(block_hash=block_hash_str),
    )

    # 4. Calcul des hashes de couches (apres finalisation du manifest)
    layer_hashes = _compute_layer_hashes(
        manifest, identity, creators, timeline, media_layer, intelligence, rights,
    )

    # 5. Root hash
    root_hash = _compute_root_hash(layer_hashes)

    # 6. Signature Ed25519 sur le root_hash
    signature_bytes = passport_keys.sign(root_hash.encode("utf-8"))
    signature_b64 = base64.b64encode(signature_bytes).decode("ascii")
    pub_pem = passport_keys.public_key_pem()
    pub_raw = passport_keys.public_key_raw_b64()

    # 7. Couche preuve
    proof = ProofLayer(
        frek_id=frek_id,
        issued_at=now,
        issuer="frekcore-notary-v1",
        signature_algo="ed25519",
        public_key_pem=pub_pem,
        public_key_raw_b64=pub_raw,
        signature=signature_b64,
        layer_hashes=layer_hashes,
        root_hash=root_hash,
        block=block_info,
    )

    fk_object = FKObject(
        manifest=manifest,
        identity=identity,
        creators=creators,
        timeline=timeline,
        media=media_layer,
        intelligence=intelligence,
        rights=rights,
        proof=proof,
    )

    # 8. Serialisation ZIP
    zip_bytes = pack_zip(fk_object, media_files_map)
    return zip_bytes, fk_object


def pack_zip(fk: FKObject, media_files_map: Dict[str, bytes]) -> bytes:
    """Emballe l'objet FK complet dans un ZIP conforme (.fk)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Manifest racine (canonique)
        zf.writestr("manifest.fk.json",
                    canonical_json(fk.manifest.model_dump()).encode("utf-8"))
        # Metadata
        zf.writestr("metadata/identity.json",
                    canonical_json(fk.identity.model_dump()).encode("utf-8"))
        zf.writestr("metadata/creators.json",
                    canonical_json(fk.creators.model_dump()).encode("utf-8"))
        zf.writestr("metadata/timeline.json",
                    canonical_json(fk.timeline.model_dump()).encode("utf-8"))
        # Media manifest
        zf.writestr("media/media.json",
                    canonical_json(fk.media.model_dump()).encode("utf-8"))
        # Media binaires
        for path, data in media_files_map.items():
            zf.writestr(path, data)
        # Intelligence (vide reserve)
        zf.writestr("intelligence/intelligence.json",
                    canonical_json(fk.intelligence.model_dump()).encode("utf-8"))
        # Droits
        zf.writestr("rights/ownership.json",
                    canonical_json(fk.rights.model_dump()).encode("utf-8"))
        # Preuve (contient signature Ed25519 + cle publique)
        zf.writestr("proof/frekcore-attestation.json",
                    canonical_json(fk.proof.model_dump()).encode("utf-8"))
        # README lisible humain
        zf.writestr("README.txt", _readme_text(fk).encode("utf-8"))
    return buf.getvalue()


def _readme_text(fk: FKObject) -> str:
    return (
        f"FK Cultural Object Container v{FK_VERSION}\n"
        f"===========================================\n\n"
        f"FREK-ID  : {fk.manifest.frek_id}\n"
        f"Type     : {fk.manifest.object_type}\n"
        f"Titre    : {fk.identity.title}\n"
        f"Createur : {fk.creators.primary_creator.name}\n"
        f"Cree le  : {fk.manifest.created_at}\n\n"
        f"Ce fichier est un objet culturel FK, signe cryptographiquement\n"
        f"par FREKCORE (Ed25519). Il peut etre verifie hors ligne :\n"
        f"  1. Dezipper l'archive\n"
        f"  2. Utiliser un validateur FK (voir frekcore.io/spec/fk)\n\n"
        f"Les formats existants transportent les medias.\n"
        f"FK transporte leur sens.\n"
    )
