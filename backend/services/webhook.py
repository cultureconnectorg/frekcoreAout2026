"""
Stripe Webhook Handler
"""
import os
import logging

from fastapi import APIRouter, Request
from emergentintegrations.payments.stripe.checkout import StripeCheckout
from frek_v1.utils import now_iso

webhook_router = APIRouter(tags=["Webhooks"])
logger = logging.getLogger("frek.webhook")

db = None


def set_db(database):
    global db
    db = database


@webhook_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")

    try:
        host_url = str(request.base_url)
        webhook_url = f"{host_url}api/webhook/stripe"
        stripe_checkout = StripeCheckout(
            api_key=os.environ.get("STRIPE_API_KEY", ""),
            webhook_url=webhook_url,
        )
        event = await stripe_checkout.handle_webhook(body, signature)

        logger.info(f"Webhook: {event.event_type} | session={event.session_id} | status={event.payment_status}")

        if event.payment_status == "paid":
            # Find and update transaction
            tx = await db.payment_transactions.find_one(
                {"session_id": event.session_id, "payment_status": {"$ne": "paid"}},
                {"_id": 0}
            )
            if tx:
                now = now_iso()
                await db.badges.update_one(
                    {"badge_id": tx["badge_id"]},
                    {"$inc": {"jetons_solde": tx["jetons"]}}
                )
                await db.payment_transactions.update_one(
                    {"session_id": event.session_id},
                    {"$set": {"payment_status": "paid", "status": "complete", "updated_at": now}}
                )
                logger.info(f"Webhook: Credited {tx['jetons']}J to {tx['badge_id']}")

        return {"status": "ok"}

    except Exception as e:
        logger.warning(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}
