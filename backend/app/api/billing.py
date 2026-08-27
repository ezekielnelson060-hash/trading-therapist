from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models import User

router = APIRouter()

PLANS = {
    "free": {
        "name": "Free",
        "price_usd": 0,
        "features": ["Basic tilt", "Limited history", "Demo data"],
    },
    "trader": {
        "name": "Trader",
        "price_usd": 15,
        "features": ["MT5 + IBKR", "Baseline + tilt", "Autopsy", "Coach", "Weekly report"],
    },
    "pro": {
        "name": "Pro",
        "price_usd": 39,
        "features": [
            "Everything in Trader",
            "Tilt alerts + email",
            "Cost of behavior",
            "Soft trading lock",
        ],
    },
    "teams": {
        "name": "Teams / Prop",
        "price_usd": 99,
        "features": ["Everything in Pro", "Multi-trader risk view", "Desk aggregation"],
    },
}


@router.get("/plans")
async def list_plans():
    return {"plans": PLANS}


@router.get("/me")
async def my_billing(current_user: User = Depends(get_current_user)):
    return {
        "plan": current_user.plan or "free",
        "plan_expires_at": current_user.plan_expires_at,
        "stripe_customer_id": getattr(current_user, "stripe_customer_id", None),
        "features": PLANS.get(current_user.plan or "free", PLANS["free"])["features"],
    }


@router.post("/checkout")
async def create_checkout(
    plan: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if plan not in ("trader", "pro", "teams"):
        raise HTTPException(400, "plan must be trader, pro, or teams")

    if not settings.STRIPE_SECRET_KEY:
        current_user.plan = plan
        await db.flush()
        return {
            "mode": "stub",
            "message": f"Plan set to {plan} (no Stripe key — demo upgrade).",
            "plan": plan,
            "checkout_url": None,
        }

    price_id = settings.STRIPE_PRICE_TRADER if plan == "trader" else settings.STRIPE_PRICE_PRO
    if not price_id:
        raise HTTPException(400, f"Missing Stripe price id for {plan}")

    try:
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=current_user.email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.APP_URL}/dashboard?billing=success",
            cancel_url=f"{settings.APP_URL}/billing?billing=cancel",
            metadata={"user_id": current_user.id, "plan": plan},
        )
        return {"mode": "stripe", "checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(500, f"Stripe error: {e}")


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.STRIPE_SECRET_KEY:
        return {"ok": True, "ignored": True}
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET or ""
        )
    except Exception as e:
        raise HTTPException(400, str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata") or {}
        user_id = meta.get("user_id")
        plan = meta.get("plan") or "trader"
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.plan = plan
                if session.get("customer"):
                    user.stripe_customer_id = session["customer"]
                await db.flush()
    return {"ok": True}
