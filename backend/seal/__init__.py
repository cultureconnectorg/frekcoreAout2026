"""FREK Certified Seal — script JS embeddable pour partenaires.

Usage cote partenaire :
    <script src="https://frekcore.com/seal.js" data-frek-id="abcd-..." async></script>

Le script :
1. Lit l'attribut data-frek-id de sa propre balise
2. Appelle /api/v1/passport/{frek_id} et /api/v1/passport/key
3. Verifie offline (Ed25519 + Merkle) cote navigateur du visiteur
4. Injecte un SVG signe avec le statut, lien vers /verify/{frek_id}
5. Aucun call externe ailleurs que vers FREKCORE — aucun tracking

Servi via FastAPI avec CORS permissif et cache HTTP cote partenaire.
"""
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import Response

from passport import keys

seal_router = APIRouter(tags=["FREK Certified Seal — Embeddable"])

SEAL_DIR = Path(__file__).resolve().parent
SEAL_JS_PATH = SEAL_DIR / "seal.js"


@seal_router.get("/seal.js")
async def seal_js():
    """Sert le script JS standalone que les partenaires embeddent.

    Cache 5 min cote CDN/navigateur. Aucun secret. La cle publique est
    injectee a la volee pour eviter un round-trip supplementaire.
    """
    js_template = SEAL_JS_PATH.read_text(encoding="utf-8")
    js = js_template.replace(
        "%%FREK_PUBLIC_KEY_B64%%",
        keys.public_key_raw_b64(),
    )
    return Response(
        content=js,
        media_type="application/javascript; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=300",
            "Access-Control-Allow-Origin": "*",
        },
    )


@seal_router.get("/seal/demo")
async def seal_demo():
    """Page de demo pour tester le seal en isolation."""
    html = (SEAL_DIR / "demo.html").read_text(encoding="utf-8")
    return Response(content=html, media_type="text/html; charset=utf-8")
