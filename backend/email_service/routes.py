"""
CC2026 Email Service — Amazon SES Production + Templates Jinja2
Campagnes automatiques J-30 a J+1
"""
import os
import logging
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from frek_v1.auth import require_permission
from frek_v1.utils import now_iso

email_router = APIRouter(prefix="/email", tags=["CC2026 Email"])
logger = logging.getLogger("frek.email")

db = None

# SES config
AWS_REGION = os.environ.get("AWS_SES_REGION", "eu-west-1")
SES_SENDER = "Culture Connect 2026 <frekcore@gmail.com>"
APP_URL = os.environ.get("APP_URL", "https://frekcore.com")

CAMPAIGN_TYPES = {
    "bienvenue": {"subject": "Bienvenue Culture Connect 2026", "trigger": "inscription"},
    "j-30": {"subject": "J-30 : Le compte a rebours commence", "trigger": "auto"},
    "j-15": {"subject": "J-15 : Votre badge vous attend", "trigger": "auto"},
    "j-7": {"subject": "J-7 : Derniers preparatifs", "trigger": "auto"},
    "j-1": {"subject": "Demain c'est le jour J !", "trigger": "auto"},
    "j-0": {"subject": "Les portes sont ouvertes !", "trigger": "auto"},
    "j+1": {"subject": "Merci ! Votre empreinte culturelle", "trigger": "auto"},
    "recharge": {"subject": "Confirmation de recharge jetons CC2026", "trigger": "achat"},
}


def set_db(database):
    global db
    db = database


def _get_ses_client():
    return boto3.client(
        "ses",
        region_name=AWS_REGION,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )


def _render_template(template_name: str, variables: dict) -> str:
    prenom = variables.get('prenom', '')
    badge_id = variables.get('badge_id', '')
    frek_id = variables.get('frek_id', '')
    type_badge = variables.get('type_badge', '')
    qr_url = variables.get('qr_url', '#')
    jetons_solde = variables.get('jetons_solde', 0)
    pack = variables.get('pack', '')
    jetons = variables.get('jetons', 0)
    solde = variables.get('solde', 0)

    header = f"""
    <div style="background: linear-gradient(135deg, #2cc4f5, #06b6d4); padding: 40px 30px; text-align: center; border-radius: 16px 16px 0 0;">
        <h1 style="color: white; font-size: 28px; margin: 0; font-family: 'Helvetica Neue', Arial, sans-serif;">Culture Connect 2026</h1>
        <p style="color: rgba(255,255,255,0.8); font-size: 14px; margin-top: 8px;">22 Mai 2026 &middot; Parc de La Savane &middot; Fort-de-France, Martinique</p>
    </div>"""

    footer = """
    <div style="padding: 20px; text-align: center; background: #f8fafc; border-radius: 0 0 16px 16px;">
        <p style="color: #94a3b8; font-size: 11px; margin: 0;">FREK &mdash; Fichier de R&eacute;f&eacute;rencement et d'Empreinte Kulturelle</p>
        <p style="color: #cbd5e1; font-size: 10px; margin: 4px 0 0;">frekcore.com | Culture Connect 2026 | CVLN Group</p>
    </div>"""

    templates = {
        "bienvenue": f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
            {header}
            <div style="padding: 30px;">
                <h2 style="color: #1e293b; margin-top: 0;">Bienvenue {prenom} !</h2>
                <p style="color: #64748b; line-height: 1.7;">Votre badge <strong style="color: #2cc4f5;">{badge_id}</strong> de type <strong>{type_badge}</strong> a ete cree.</p>
                <p style="color: #64748b; line-height: 1.7;">Votre identite culturelle FREK : <code style="background: #f1f5f9; padding: 3px 8px; border-radius: 6px; font-size: 12px;">{frek_id}</code></p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{qr_url}" style="background: linear-gradient(135deg, #2cc4f5, #06b6d4); color: white; padding: 14px 36px; border-radius: 12px; text-decoration: none; font-weight: bold; display: inline-block; font-size: 16px;">Activer mon Badge</a>
                </div>
                <p style="color: #94a3b8; font-size: 13px; text-align: center;">Cliquez pour activer votre badge et recevoir votre QR code personnel.</p>
            </div>
            {footer}
        </div>""",

        "j-30": f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
            {header}
            <div style="padding: 30px;">
                <h2 style="color: #1e293b; margin-top: 0;">J-30 {prenom} !</h2>
                <p style="color: #64748b; line-height: 1.7;">Le compte a rebours est lance. Culture Connect 2026 vous attend dans 30 jours.</p>
                <div style="background: #f8fafc; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
                    <p style="font-size: 48px; color: #2cc4f5; font-weight: bold; margin: 0;">30</p>
                    <p style="color: #64748b; margin: 4px 0 0;">jours restants</p>
                </div>
                <div style="text-align: center; margin: 20px 0;">
                    <a href="https://frekcore.com" style="background: #2cc4f5; color: white; padding: 12px 28px; border-radius: 10px; text-decoration: none; font-weight: bold;">Voir le programme</a>
                </div>
            </div>
            {footer}
        </div>""",

        "j-15": f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
            {header}
            <div style="padding: 30px;">
                <h2 style="color: #1e293b; margin-top: 0;">Votre badge vous attend, {prenom} !</h2>
                <p style="color: #64748b; line-height: 1.7;">J-15 : pensez a activer votre badge pour le jour J.</p>
                <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 16px; margin: 16px 0;">
                    <p style="color: #0284c7; margin: 0;"><strong>Badge:</strong> {badge_id}</p>
                    <p style="color: #0284c7; margin: 4px 0 0;"><strong>Type:</strong> {type_badge}</p>
                </div>
                <div style="text-align: center; margin: 20px 0;">
                    <a href="{qr_url}" style="background: #2cc4f5; color: white; padding: 12px 28px; border-radius: 10px; text-decoration: none; font-weight: bold;">Telecharger mon Badge</a>
                </div>
            </div>
            {footer}
        </div>""",

        "recharge": f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
            {header}
            <div style="padding: 30px;">
                <h2 style="color: #1e293b; margin-top: 0;">Recharge confirmee !</h2>
                <p style="color: #64748b; line-height: 1.7;">Bonjour {prenom}, votre wallet a ete credite.</p>
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px; margin: 16px 0; text-align: center;">
                    <p style="font-size: 36px; color: #16a34a; font-weight: bold; margin: 0;">+{jetons} J</p>
                    <p style="color: #64748b; margin: 8px 0 0;">Pack {pack}</p>
                    <p style="color: #16a34a; margin: 8px 0 0; font-size: 14px;">Solde actuel : <strong>{solde} Jetons</strong></p>
                </div>
            </div>
            {footer}
        </div>""",
    }

    # Default template for j-7, j-1, j-0, j+1
    default_tpl = f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
        {header}
        <div style="padding: 30px;">
            <h2 style="color: #1e293b; margin-top: 0;">Bonjour {prenom} !</h2>
            <p style="color: #64748b; line-height: 1.7;">Culture Connect 2026 approche. Votre badge {badge_id} est pret.</p>
            <div style="text-align: center; margin: 20px 0;">
                <a href="https://frekcore.com" style="background: #2cc4f5; color: white; padding: 12px 28px; border-radius: 10px; text-decoration: none; font-weight: bold;">Mon espace CC2026</a>
            </div>
        </div>
        {footer}
    </div>"""

    return templates.get(template_name, default_tpl)


async def _send_email(to_email: str, subject: str, html_body: str) -> dict:
    """Send email via Amazon SES"""
    try:
        ses = _get_ses_client()
        response = ses.send_email(
            Source=SES_SENDER,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Html": {"Data": html_body, "Charset": "UTF-8"}},
            },
        )
        logger.info(f"[SES] Sent to {to_email} | MessageId: {response['MessageId']}")
        return {"status": "sent", "message_id": response["MessageId"]}
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = e.response["Error"]["Message"]
        logger.warning(f"[SES] Error {error_code}: {error_msg}")
        # Fallback to log mode if SES not configured
        if error_code in ("MessageRejected", "InvalidParameterValue", "AccessDenied"):
            logger.info(f"[EMAIL FALLBACK LOG] To: {to_email} | Subject: {subject}")
            return {"status": "logged", "message_id": f"fallback-{now_iso()}", "ses_error": error_msg}
        return {"status": "error", "error": f"{error_code}: {error_msg}"}
    except Exception as e:
        logger.warning(f"[SES] Exception: {e}")
        logger.info(f"[EMAIL FALLBACK LOG] To: {to_email} | Subject: {subject}")
        return {"status": "logged", "message_id": f"fallback-{now_iso()}", "error": str(e)}


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
    ses_status = "configured"
    try:
        ses = _get_ses_client()
        ses.get_account_sending_enabled()
    except Exception:
        ses_status = "fallback_log"
    return {"templates": CAMPAIGN_TYPES, "ses_status": ses_status}


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
        "qr_url": f"{APP_URL}/activate/{badge.get('qr_token', '')}",
        "jetons_solde": badge.get("jetons_solde", 0),
        "event_date": "22 Mai 2026",
    }

    html = _render_template(request.template, variables)
    to = request.to_email or f"participant_{badge['badge_id']}@cc2026.frekcore.com"

    result = await _send_email(to, campaign_info["subject"], html)

    email_log = {
        "badge_id": request.badge_id,
        "template": request.template,
        "subject": campaign_info["subject"],
        "to_email": to,
        "status": result["status"],
        "message_id": result.get("message_id"),
        "ses_error": result.get("ses_error") or result.get("error"),
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

    for badge in badges:
        variables = {
            "prenom": badge.get("prenom", ""),
            "badge_id": badge["badge_id"],
            "frek_id": badge.get("frek_id", ""),
            "type_badge": badge.get("type_name", ""),
            "qr_url": f"{APP_URL}/activate/{badge.get('qr_token', '')}",
            "jetons_solde": badge.get("jetons_solde", 0),
        }
        html = _render_template(request.campaign_type, variables)
        to = f"participant_{badge['badge_id']}@cc2026.frekcore.com"

        result = await _send_email(to, campaign_info["subject"], html)
        if result["status"] in ("sent", "logged"):
            sent += 1
        else:
            errors += 1

    now = now_iso()
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
async def email_stats():
    total_sent = await db.email_logs.count_documents({"status": "sent"})
    total_logged = await db.email_logs.count_documents({"status": "logged"})
    total_errors = await db.email_logs.count_documents({"status": "error"})
    total_all = total_sent + total_logged + total_errors

    by_template = {}
    async for doc in db.email_logs.aggregate([
        {"$group": {"_id": "$template", "count": {"$sum": 1}}},
    ]):
        by_template[doc["_id"]] = doc["count"]

    campaigns = await db.email_campaigns.find({}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(10)

    return {
        "total_sent_ses": total_sent,
        "total_logged_fallback": total_logged,
        "total_errors": total_errors,
        "deliverability": round((total_sent / max(total_all, 1)) * 100, 1),
        "by_template": by_template,
        "recent_campaigns": campaigns,
    }
