"""FREK PDF Batch — generation effective."""
import io
import logging
import zipfile
from typing import Optional

import qrcode
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

logger = logging.getLogger("frek.pdf_batch.service")

# Default Twina template — A6 portrait (105 x 148 mm) = format poche
DEFAULT_TEMPLATE = {
    "title": "FrekCore",
    "subtitle": "Carte d'acces certifiee",
    "footer": "Notaire culturel tech · cvln.com",
    "accent_hex": "#0EA5E9",
    "verify_base_url": "https://frekcore.com/verify",
}


def _hex_to_rgb(hex_str: str) -> tuple[float, float, float]:
    h = hex_str.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def _render_pdf(badge: dict, template: dict) -> bytes:
    """Genere un seul PDF A6 pour un badge."""
    buf = io.BytesIO()
    width, height = A6
    c = canvas.Canvas(buf, pagesize=A6)
    accent = _hex_to_rgb(template.get("accent_hex") or DEFAULT_TEMPLATE["accent_hex"])

    # Header bar
    c.setFillColorRGB(*accent)
    c.rect(0, height - 18 * mm, width, 18 * mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(8 * mm, height - 10 * mm, template.get("title") or DEFAULT_TEMPLATE["title"])
    c.setFont("Helvetica", 8)
    c.drawString(8 * mm, height - 15 * mm, template.get("subtitle") or DEFAULT_TEMPLATE["subtitle"])

    # Nom & prenom
    c.setFillColorRGB(0.1, 0.15, 0.2)
    nom = badge.get("nom") or ""
    prenom = badge.get("prenom") or ""
    name = f"{prenom} {nom}".strip() or "Porteur"
    c.setFont("Helvetica-Bold", 16)
    c.drawString(8 * mm, height - 32 * mm, name[:32])

    # Type badge
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.4, 0.45, 0.55)
    type_label = badge.get("type_name") or badge.get("type_badge") or ""
    c.drawString(8 * mm, height - 38 * mm, type_label)

    # Badge ID
    c.setFont("Courier-Bold", 11)
    c.setFillColorRGB(*accent)
    c.drawString(8 * mm, height - 50 * mm, badge.get("badge_id") or "")

    # FREK-ID (smaller, truncated)
    frek_id = badge.get("frek_id") or ""
    c.setFont("Courier", 6)
    c.setFillColorRGB(0.5, 0.55, 0.65)
    c.drawString(8 * mm, height - 56 * mm, f"FREK-ID {frek_id[:40]}")

    # QR code → /verify/{frek_id}
    if frek_id:
        verify_url = f"{(template.get('verify_base_url') or DEFAULT_TEMPLATE['verify_base_url']).rstrip('/')}/{frek_id}"
        qr_img = qrcode.make(verify_url)
        qr_buf = io.BytesIO()
        qr_img.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        c.drawImage(ImageReader(qr_buf), width - 38 * mm, 12 * mm, 32 * mm, 32 * mm)

    # Footer
    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.6, 0.65, 0.75)
    c.drawString(8 * mm, 6 * mm, template.get("footer") or DEFAULT_TEMPLATE["footer"])

    c.showPage()
    c.save()
    return buf.getvalue()


def render_batch_zip(badges: list[dict], template: Optional[dict] = None) -> bytes:
    """Genere un ZIP contenant N PDFs (1 par badge)."""
    tpl = {**DEFAULT_TEMPLATE, **(template or {})}
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for b in badges:
            pdf_bytes = _render_pdf(b, tpl)
            fname = f"badge-{b.get('badge_id') or b.get('frek_id') or 'noid'}.pdf"
            zf.writestr(fname, pdf_bytes)
    zip_buf.seek(0)
    return zip_buf.read()
