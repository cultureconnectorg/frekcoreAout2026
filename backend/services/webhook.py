"""
Stripe Webhook Handler
"""
import os
import logging

from fastapi import APIRouter, Request
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
        # Phase 3 (reports/15_DEPENDENCY_REMEDIATION.md): imported lazily,
        # inside the request handler, not at module load time. This is a
        # real, used dependency (not dead code) but it is a private package
        # not published on PyPI (see requirements.txt's comment on this
        # line); a deferred import means the rest of the application —
        # every other route in server.py — no longer fails to import in an
        # environment where this one package is unavailable. This route
        # itself still requires it and fails loudly (caught below, returned
        # as a JSON error) rather than silently.
        from emergentintegrations.payments.stripe.checkout import StripeCheckout

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
