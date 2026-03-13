"""
CC2026 Email Service — Amazon SES + Templates Jinja2
Campagnes automatiques J-30 a J+1
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from frek_v1.auth import require_permission
from frek_v1.utils import now_iso

email_router = APIRouter(prefix="/email", tags=["CC2026 Email"])
logger = logging.getLogger("frek.email")

db = None

# SES mode: "live" (real SES) or "log" (dev mode - logs only)
SES_MODE = "log"

CAMPAIGN_TYPES = {
    "bienvenue": {"subject": "Bienvenue Culture Connect 2026", "trigger": "inscription"},
    "j-30": {"subject": "J-30 : Le compte a rebours commence", "trigger": "auto"},
    "j-15": {"subject": "J-15 : Votre badge vous attend", "trigger": "auto"},
    "j-7": {"subject": "J-7 : Derniers preparatifs", "trigger": "auto"},
    "j-1": {"subject": "Demain c'est le jour J !", "trigger": "auto"},
    "j-0": {"subject": "Les portes sont ouvertes !", "trigger": "auto"},
    "j+1": {"subject": "Merci ! Votre empreinte culturelle", "trigger": "auto"},
    "recharge": {"subject": "Confirmation de recharge jetons", "trigger": "achat"},
}


def set_db(database):
    global db
    db = database


def _render_template(template_name: str, variables: dict) -> str:
    """Render email HTML template"""
    templates = {
        "bienvenue": f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8fafc;">
            <div style="background: linear-gradient(135deg, #2cc4f5, #06b6d4); padding: 40px 30px; text-align: center;">
                <h1 style="color: white; font-size: 28px; margin: 0;">Culture Connect 2026</h1>
                <p style="color: rgba(255,255,255,0.8); font-size: 14px; margin-top: 8px;">22 Mai 2026 - Parc de La Savane, Fort-de-France</p>
            </div>
            <div style="padding: 30px; background: white;">
                <h2 style="color: #1e293b;">Bienvenue {variables.get('prenom', '')} !</h2>
                <p style="color: #64748b; line-height: 1.6;">Votre badge <strong style="color: #2cc4f5;">{variables.get('badge_id', '')}</strong> ({variables.get('type_badge', '')}) est pret.</p>
                <p style="color: #64748b;">Votre identite FREK : <code style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">{variables.get('frek_id', '')}</code></p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{variables.get('qr_url', '#')}" style="background: #2cc4f5; color: white; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: bold; display: inline-block;">Activer mon Badge</a>
                </div>
                <p style="color: #94a3b8; font-size: 12px; text-align: center;">FREK - Fichier de Referencement et d'Empreinte Kulturelle</p>
            </div>
        </div>""",
        "recharge": f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2cc4f5; padding: 30px; text-align: center;">
                <h1 style="color: white; font-size: 24px;">Recharge Confirmee</h1>
            </div>
            <div style="padding: 30px; background: white;">
                <h2 style="color: #1e293b;">Bonjour {variables.get('prenom', '')} !</h2>
                <p style="color: #64748b;">Votre wallet a ete credite de <strong>{variables.get('jetons', 0)} jetons</strong> (Pack {variables.get('pack', '')}).</p>
                <p style="color: #64748b;">Solde actuel : <strong style="color: #2cc4f5; font-size: 20px;">{variables.get('solde', 0)} J</strong></p>
            </div>
        </div>""",
    }
    return templates.get(template_name, f"<p>Template {template_name} non trouve</p>")


async def _send_email(to_email: str, subject: str, html_body: str) -> dict:
    """Send email via SES or log mode"""
    if SES_MODE == "log":
        logger.info(f"[EMAIL LOG] To: {to_email} | Subject: {subject}")
        return {"status": "logged", "message_id": f"log-{now_iso()}"}

    # Real SES implementation (requires AWS credentials)
    try:
        import boto3
        ses = boto3.client("ses", region_name="eu-west-1")
        response = ses.send_email(
            Source="Culture Connect 2026 <noreply@frekcore.com>",
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": html_body}},
            },
        )
        return {"status": "sent", "message_id": response["MessageId"]}
    except Exception as e:
        logger.error(f"SES error: {e}")
        return {"status": "error", "error": str(e)}


class SendEmailRequest(BaseModel):
    badge_id: str
    template: str = "bienvenue"
    to_email: Optional[str] = None


class CampaignRequest(BaseModel):
    campaign_type: str = Field(..., description="bienvenue, j-30, j-15, j-7, j-1, j-0, j+1, recharge")
    segment: Optional[str] = None
    event: str = "CC2026"


@email_router.get("/templates")
async def list_templates():
    return {"templates": CAMPAIGN_TYPES, "ses_mode": SES_MODE}


@email_router.post("/send")
async def send_email(
    request: SendEmailRequest,
    client: dict = Depends(require_permission("emit")),
):
    badge = await db.badges.find_one({"badge_id": request.badge_id}, {"_id": 0})
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge {request.badge_id} introuvable")

    campaign_info = CAMPAIGN_TYPES.get(request.template, CAMPAIGN_TYPES["bienvenue"])

    variables = {
        "prenom": badge.get("prenom", ""),
        "nom": badge.get("nom", ""),
        "badge_id": badge["badge_id"],
        "frek_id": badge.get("frek_id", ""),
        "type_badge": badge.get("type_name", badge.get("type_badge", "")),
        "qr_url": f"https://frekcore.com/activate/{badge.get('qr_token', '')}",
        "jetons_solde": badge.get("jetons_solde", 0),
        "event_date": "22 Mai 2026",
    }

    html = _render_template(request.template, variables)
    to = request.to_email or f"participant_{badge['badge_id']}@cc2026.frekcore.com"

    result = await _send_email(to, campaign_info["subject"], html)

    # Log email sent
    email_log = {
        "badge_id": request.badge_id,
        "template": request.template,
        "subject": campaign_info["subject"],
        "to_email": to,
        "status": result["status"],
        "message_id": result.get("message_id"),
        "timestamp": now_iso(),
        "client_id": client["client_id"],
    }
    await db.email_logs.insert_one(email_log)
    email_log.pop("_id", None)

    return {"email": email_log, "html_preview": html[:500]}


@email_router.post("/campaign")
async def launch_campaign(
    request: CampaignRequest,
    client: dict = Depends(require_permission("emit")),
):
    if request.campaign_type not in CAMPAIGN_TYPES:
        raise HTTPException(status_code=400, detail=f"Type invalide. Choix: {list(CAMPAIGN_TYPES.keys())}")

    query = {"event": request.event}
    if request.segment:
        query["type_badge"] = request.segment

    badges = await db.badges.find(query, {"_id": 0}).to_list(10000)
    campaign_info = CAMPAIGN_TYPES[request.campaign_type]

    sent = 0
    errors = 0
    now = now_iso()

    for badge in badges:
        variables = {
            "prenom": badge.get("prenom", ""),
            "badge_id": badge["badge_id"],
            "frek_id": badge.get("frek_id", ""),
            "type_badge": badge.get("type_name", ""),
            "qr_url": f"https://frekcore.com/activate/{badge.get('qr_token', '')}",
            "jetons_solde": badge.get("jetons_solde", 0),
        }
        html = _render_template(request.campaign_type, variables)
        to = f"participant_{badge['badge_id']}@cc2026.frekcore.com"

        result = await _send_email(to, campaign_info["subject"], html)
        if result["status"] in ("sent", "logged"):
            sent += 1
        else:
            errors += 1

    # Save campaign record
    campaign = {
        "campaign_id": f"camp-{request.campaign_type}-{now[:10]}",
        "type": request.campaign_type,
        "segment": request.segment,
        "event": request.event,
        "total_badges": len(badges),
        "sent": sent,
        "errors": errors,
        "timestamp": now,
        "client_id": client["client_id"],
    }
    await db.email_campaigns.insert_one(campaign)
    campaign.pop("_id", None)

    return campaign


@email_router.get("/stats")
async def email_stats(event: str = "CC2026"):
    total_sent = await db.email_logs.count_documents({"status": {"$in": ["sent", "logged"]}})
    total_errors = await db.email_logs.count_documents({"status": "error"})

    by_template = {}
    async for doc in db.email_logs.aggregate([
        {"$group": {"_id": "$template", "count": {"$sum": 1}}},
    ]):
        by_template[doc["_id"]] = doc["count"]

    campaigns = await db.email_campaigns.find({}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(10)

    return {
        "total_sent": total_sent,
        "total_errors": total_errors,
        "deliverability": round((total_sent / max(total_sent + total_errors, 1)) * 100, 1),
        "by_template": by_template,
        "recent_campaigns": campaigns,
        "ses_mode": SES_MODE,
    }
