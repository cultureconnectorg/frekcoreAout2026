"""
FREK v2 — Routes API
=====================
Endpoints pour les 11 nœuds de FREK.
"""
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel, Field
from typing import Optional, List
import base64
import os

from .pipeline import pipeline
from .routes_advanced import advanced_router
from .legacy_compat import legacy_rate_limit_ok, publish_legacy_invocation

logger = logging.getLogger("frek.routes")

# Router FREK principal
frek_router = APIRouter(prefix="/frek", tags=["FREK v2 Core (NODE 01-05)"])

# Inclure le routeur avancé (NODE 06-10)
frek_router.include_router(advanced_router, prefix="")

# STATE_6 Historical Compatibility Reconciliation (2026-09-02): `db` is
# added here ONLY so `/verify/{frek_id}`'s canonical cross-reference
# touch (below) can READ canonical D1 `content_binding` state -- see
# `docs/architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md`. Nothing
# in this module writes to `db`: canonical persistence stays exclusively
# owned by `content_binding`/`creative_lifecycle`'s own routes.
db = None


def set_db(database):
    global db
    db = database


# ═══════════════════════════════════════════════════════════════════
# Modèles de requête/réponse
# ═══════════════════════════════════════════════════════════════════

class CertifyRequest(BaseModel):
    """Requête de certification avec audio en base64"""
    audio_base64: str = Field(..., description="Audio encodé en base64")
    artiste_id: str = Field(..., description="Identifiant anonyme de l'artiste")
    gps_lat: Optional[float] = Field(None, description="Latitude GPS")
    gps_lon: Optional[float] = Field(None, description="Longitude GPS")
    device_id: Optional[str] = Field(None, description="Identifiant de l'appareil")
    pre_id: Optional[str] = Field(None, description="PRE-ID si cycle existant")


class GenesisRequest(BaseModel):
    """Requête de démarrage de cycle GENESIS"""
    artiste_id: str
    intention: dict = Field(..., description="{ concept, lieu, description }")


class WorkshopRequest(BaseModel):
    """Requête d'ajout de version WORKSHOP"""
    pre_id: str
    audio_base64: str
    notes: Optional[str] = None


class ResonanceRequest(BaseModel):
    """Requête de recherche de résonance"""
    frek_id: str
    limit: int = Field(5, ge=1, le=20)


# ═══════════════════════════════════════════════════════════════════
# Routes principales
# ═══════════════════════════════════════════════════════════════════

@frek_router.get("/")
async def frek_info():
    """Information sur FREK v2"""
    return {
        "frek_version": "2.0",
        "description": "Infrastructure de certification fréquentielle des œuvres créatives",
        "nodes": {
            "01": "EXTRACTION — Signal brut → Vecteur 528D",
            "02": "IDENTITÉ — Vecteur → FREK-ID (triple SHA-256)",
            "03": "CYCLE — 5 stades luciole (Genesis → Legacy)",
            "04": "MÉMOIRE — pgvector, ~2.5KB/œuvre",
            "05": "RÉSONANCE — Similarité, cohérence, tendances",
            "06": "RÉSEAU — Graphe vivant (5 types nœuds, 17 relations)",
            "07": "TRANSMISSION — BLE/NFC/WiFi/Ultrasons",
            "08": "SYSTÈME — Couche système audio",
            "09": "JURIDIQUE — Notaire de fait",
            "10": "INSTITUTIONNEL — Observatoire culturel",
            "11": "EXPERIENCE — 3% visible, 1 bouton",
        },
        "principle": "La fréquence est la signature universelle de ce qui existe. FREK la capture. Une fois. Pour toujours.",
        "message": "FREK atteste un fait technique — jamais un droit. Comme une luciole — elle s'allume. C'est tout.",
    }


@frek_router.get("/stats")
async def frek_stats():
    """Statistiques globales FREK"""
    return await pipeline.get_stats()


def _add_legacy_certify_note(result_dict: dict) -> dict:
    """STATE_6 hardening (2026-09-02): additive-only compatibility note.
    The `frek_id` this legacy pipeline mints (node02_identity.py's own
    triple-SHA-256 chain) is NOT the canonical `.fk` frek_id, and no
    content_binding is auto-created for it -- doing so would require
    synthesizing a `.fk` Cultural Object from unverified legacy input,
    an architecture decision this state explicitly declines to make
    silently (a real, disclosed semantic gap, not an oversight -- see
    `docs/architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md`'s D1
    section). The identifier itself is preserved exactly as minted,
    never silently destroyed or replaced (per the founder's own explicit
    instruction)."""
    return {
        **result_dict,
        "canonical_note": (
            "This frek_id is minted by the legacy node02_identity chain, "
            "not by canonical .fk creation (POST /api/v1/fk/create) -- it "
            "is not a canonical content_binding subject. See "
            "docs/architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md."
        ),
    }


@frek_router.post("/certify")
async def certify_audio(request: CertifyRequest):
    """
    🔴 ENDPOINT PRINCIPAL — Certification complète

    1 action → 17 opérations automatiques → FREK-ID

    INPUT: Audio base64 + métadonnées
    OUTPUT: FREK-ID complet avec extraction, identité, cycle, résonance
    """
    if not await legacy_rate_limit_ok(scope=request.artiste_id, write=True):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Audio base64 invalide: {e}")

    if len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Fichier audio trop petit")

    if len(audio_bytes) > 100 * 1024 * 1024:  # 100MB max
        raise HTTPException(status_code=400, detail="Fichier audio trop grand (max 100MB)")

    result = await pipeline.certify(
        audio_bytes=audio_bytes,
        artiste_id=request.artiste_id,
        gps_lat=request.gps_lat,
        gps_lon=request.gps_lon,
        device_id=request.device_id,
        pre_id=request.pre_id,
    )

    await publish_legacy_invocation(
        legacy_route="POST /api/frek/certify",
        canonical_target="content_binding",
        outcome="created",
    )
    return _add_legacy_certify_note(result.to_dict())


@frek_router.post("/certify/upload")
async def certify_audio_upload(
    audio: UploadFile = File(..., alias="audio"),
    artiste_id: str = Form(default="ARTISTE-UPLOAD"),
    gps_lat: Optional[float] = Form(default=None),
    gps_lon: Optional[float] = Form(default=None),
    device_id: Optional[str] = Form(default=None),
    pre_id: Optional[str] = Form(default=None),
):
    """
    Certification avec upload de fichier (multipart/form-data)
    """
    if not await legacy_rate_limit_ok(scope=artiste_id, write=True):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    audio_bytes = await audio.read()

    if len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Fichier audio trop petit")

    result = await pipeline.certify(
        audio_bytes=audio_bytes,
        artiste_id=artiste_id,
        gps_lat=gps_lat,
        gps_lon=gps_lon,
        device_id=device_id,
        pre_id=pre_id,
    )

    await publish_legacy_invocation(
        legacy_route="POST /api/frek/certify/upload",
        canonical_target="content_binding",
        outcome="created",
    )
    return _add_legacy_certify_note(result.to_dict())


async def _canonical_binding_for_legacy_id(frek_id: str) -> Optional[dict]:
    """Best-effort canonical cross-reference: does a D1 content_binding
    exist whose `legacy_identifier` matches this legacy frek_id? Returns
    None on any failure or when `db` is unset -- never raises, never
    blocks the legacy verify response (safety wins over completeness)."""
    if db is None:
        return None
    try:
        doc = await db.content_bindings.find_one(
            {"legacy_identifier": frek_id},
            {"_id": 0, "binding_id": 1, "frek_id": 1, "proof_state": 1, "computed_at": 1},
        )
        if not doc:
            return None
        return {"source": "content_binding (canonical, D1)", **doc}
    except Exception:
        logger.warning(
            "canonical content_binding cross-reference failed (non-blocking)",
            exc_info=True,
        )
        return None


@frek_router.get("/verify/{frek_id}")
async def verify_frek_id(frek_id: str):
    """
    Vérifie l'existence et récupère les détails d'un FREK-ID.

    STATE_6 hardening (2026-09-02): rate-limited (this route had none
    historically) and additively enriched with a `canonical_binding`
    cross-reference when a D1 `content_binding` record references this
    legacy identifier via its own `legacy_identifier` compatibility
    field (see `content_binding/models.py`) -- existing response fields
    are unchanged either way (PUBLIC READ, safe to hint at without
    breaking any consumer that ignores unknown keys).
    """
    if not await legacy_rate_limit_ok(scope=frek_id, write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    result = await pipeline.verify(frek_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    canonical_binding = await _canonical_binding_for_legacy_id(frek_id)
    if canonical_binding is not None:
        result = {**result, "canonical_binding": canonical_binding}

    await publish_legacy_invocation(
        legacy_route="GET /api/frek/verify/{frek_id}",
        canonical_target="content_binding",
        outcome="found",
    )
    return result


@frek_router.get("/verify/{frek_id}/qr.png")
async def get_qr_code(frek_id: str):
    """
    Génère un QR code PNG pour un FREK-ID
    """
    import qrcode
    import io
    from fastapi.responses import StreamingResponse
    
    # Vérifier que le FREK-ID existe
    result = await pipeline.verify(frek_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")
    
    # Générer le QR code
    app_url = os.environ.get('APP_URL', 'https://frekcore.com')
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(f"{app_url}/verify/{frek_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir en bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="image/png")


@frek_router.get("/verify/{frek_id}/certificat.pdf")
async def get_certificat_pdf(frek_id: str):
    """
    Génère un certificat PDF pour un FREK-ID
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    import io
    from fastapi.responses import StreamingResponse
    from datetime import datetime, timezone
    
    # Vérifier que le FREK-ID existe
    result = await pipeline.verify(frek_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")
    
    # Créer le PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Titre
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 3*cm, "ATTESTATION FREK")
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 4*cm, "Certification Fréquentielle")
    
    # Ligne de séparation
    c.line(2*cm, height - 4.5*cm, width - 2*cm, height - 4.5*cm)
    
    # FREK-ID
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 6*cm, "FREK-ID:")
    c.setFont("Courier", 12)
    c.drawString(2*cm, height - 6.7*cm, frek_id)
    
    # Timestamp
    timestamp_ms = result.get("timestamp_ms", 0)
    timestamp_str = datetime.fromtimestamp(timestamp_ms/1000, tz=timezone.utc).strftime("%d/%m/%Y à %H:%M:%S UTC")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 8*cm, "Horodatage:")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 8.7*cm, timestamp_str)
    
    # SHA-256
    sha256 = result.get("sha256_signal", "N/A")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 10*cm, "SHA-256 Signal:")
    c.setFont("Courier", 9)
    c.drawString(2*cm, height - 10.7*cm, sha256[:64] if sha256 else "N/A")
    
    # Hash chaîné
    hash_chaine = result.get("hash_chaine", "N/A")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 12*cm, "Hash Chaîné:")
    c.setFont("Courier", 9)
    c.drawString(2*cm, height - 12.7*cm, hash_chaine[:64] if hash_chaine else "N/A")
    
    # Stade
    stade = result.get("stade", "EMISSION")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 14*cm, "Stade:")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 14.7*cm, str(stade))
    
    # Note juridique
    c.line(2*cm, height - 16*cm, width - 2*cm, height - 16*cm)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width/2, height - 17*cm, "Cette attestation certifie un fait technique.")
    c.drawCentredString(width/2, height - 17.5*cm, "Elle ne constitue pas une déclaration de droits.")
    
    # Footer
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 2*cm, "FREK® — frekcore.com — © 2026 CVLN Group")
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=frek_{frek_id}.pdf"}
    )


# ═══════════════════════════════════════════════════════════════════
# Routes Cycle de Vie
# ═══════════════════════════════════════════════════════════════════

@frek_router.post("/genesis")
async def start_genesis(request: GenesisRequest):
    """
    STADE 1 — GENESIS

    Déclare l'intention de créer.
    L'œuvre existe dans FREK avant d'exister dans le monde.

    STATE_6 hardening (2026-09-02): rate-limited (this route had none
    historically). NOT redirected into canonical `creative_lifecycle`
    (`backend/creative_lifecycle`): that service requires an
    authenticated identity_engine session/admin actor
    (X-FREK-Session/X-Admin-Key), whereas this legacy route accepts a
    bare, unauthenticated `artiste_id` string with no identity
    resolution at all -- silently treating that string as an
    authenticated actor would weaken canonical creative_lifecycle's own
    security model (explicitly prohibited: "Historical zero-auth routes
    must NOT force canonical services to weaken their security model").
    This is a disclosed semantic gap, not an oversight -- see
    `docs/architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md`'s D2
    section.
    """
    if not await legacy_rate_limit_ok(scope=request.artiste_id, write=True):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    result = await pipeline.start_genesis(
        artiste_id=request.artiste_id,
        intention=request.intention,
    )
    await publish_legacy_invocation(
        legacy_route="POST /api/frek/genesis",
        canonical_target="creative_lifecycle",
        outcome="created",
    )
    return {
        **result,
        "canonical_note": (
            "This legacy GENESIS cycle is structurally separate from "
            "canonical creative_lifecycle (backend/creative_lifecycle), "
            "which requires an authenticated holder/admin actor this "
            "unauthenticated route does not have. See "
            "docs/architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md."
        ),
    }


@frek_router.post("/workshop")
async def add_workshop_version(request: WorkshopRequest):
    """
    STADE 2 — WORKSHOP

    Ajoute une version intermédiaire (privée, horodatée).
    Prouve le processus de création.

    STATE_6 hardening (2026-09-02): rate-limited (this route had none
    historically). Same disclosed semantic gap as /genesis above: not
    redirected into canonical creative_lifecycle for the same
    authentication-model reason.
    """
    if not await legacy_rate_limit_ok(scope=request.pre_id, write=True):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Audio base64 invalide: {e}")

    result = await pipeline.add_workshop(
        pre_id=request.pre_id,
        audio_bytes=audio_bytes,
        notes=request.notes,
    )
    await publish_legacy_invocation(
        legacy_route="POST /api/frek/workshop",
        canonical_target="creative_lifecycle",
        outcome="recorded",
    )
    return {
        **result,
        "canonical_note": (
            "This legacy WORKSHOP version is structurally separate from "
            "canonical creative_lifecycle (backend/creative_lifecycle). "
            "See docs/architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md."
        ),
    }


# ═══════════════════════════════════════════════════════════════════
# Routes Résonance
# ═══════════════════════════════════════════════════════════════════

@frek_router.post("/resonance")
async def find_resonance(request: ResonanceRequest):
    """
    NODE 05 — RÉSONANCE
    
    Trouve les œuvres qui vibrent comme celle-ci.
    Distance cosine dans l'espace 528D.
    """
    result = await pipeline.node05.find_resonance(
        source_frek_id=request.frek_id,
        limit=request.limit,
    )
    return result.to_dict()


@frek_router.get("/resonance/{frek_id}")
async def get_resonance(frek_id: str, limit: int = 5):
    """
    Recherche de résonance par GET
    """
    result = await pipeline.node05.find_resonance(
        source_frek_id=frek_id,
        limit=limit,
    )
    return result.to_dict()


@frek_router.get("/coherence/{artiste_id}")
async def get_artiste_coherence(artiste_id: str):
    """
    MOTEUR 2 — Cohérence stylistique d'un artiste
    
    < 60% = rupture de style détectée
    """
    coherence = await pipeline.node05.calculate_artiste_coherence(artiste_id)
    
    if coherence is None:
        return {
            "artiste_id": artiste_id,
            "coherence": None,
            "message": "Pas assez d'œuvres pour calculer la cohérence",
        }
    
    style_alert = None
    if coherence < 60:
        style_alert = "RUPTURE DE STYLE DÉTECTÉE"
    
    return {
        "artiste_id": artiste_id,
        "coherence": round(coherence, 1),
        "style_alert": style_alert,
    }


# ═══════════════════════════════════════════════════════════════════
# Routes Extraction directe (pour debug/test)
# ═══════════════════════════════════════════════════════════════════

@frek_router.post("/extract")
async def extract_features(
    file: UploadFile = File(...),
):
    """
    NODE 01 — Extraction seule (sans certification)
    
    Utile pour prévisualiser le vecteur avant émission.
    """
    audio_bytes = await file.read()
    
    result = await pipeline.node01.extract_from_bytes(audio_bytes)
    
    return result.to_dict()
