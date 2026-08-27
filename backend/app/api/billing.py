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
        "seat_cap": 1,
        "features": ["Basic tilt", "Demo data", "1 trader"],
    },
    "trader": {
        "name": "Trader",
        "price_usd": 19,
        "seat_cap": 1,
        "features": [
            "MT5 + IBKR ingestion",
            "Baseline + tilt score",
            "Daily autopsy + weekly report",
            "Coach grounded in real trades",
            "1 trader seat",
        ],
    },
    "pro": {
        "name": "Pro",
        "price_usd": 49,
        "seat_cap": 5,
        "features": [
            "Everything in Trader",
            "Tilt alerts + email",
            "Cost of behavior",
            "Soft trading lock",
            "Up to 5 seats",
        ],
    },
    "desk_500": {
        "name": "Desk — 500",
        "price_usd": 299,
        "seat_cap": 500,
        "features": [
            "Prop / coaching desk risk view",
            "Up to 500 traders monitored",
            "Aggregated tilt + high-risk count",
            "Team invites + roles",
        ],
    },
    "desk_2k": {
        "name": "Desk — 2,000",
        "price_usd": 799,
        "seat_cap": 2000,
        "features": [
            "Everything in Desk 500",
            "Up to 2,000 traders",
            "Desk-wide behavioral heat",
            "Coach / risk-manager roles",
        ],
    },
    "desk_10k": {
        "name": "Desk — 10,000",
        "price_usd": 2499,
        "seat_cap": 10000,
        "features": [
            "Everything in Desk 2,000",
            "Up to 10,000 traders",
            "Enterprise risk monitoring",
            "Large prop / multi-program scale",
        ],
    },
}


@router.get("/plans")
async def list_plans():
    return {"plans": PLANS}


@router.get("/me")
async def my_billing(current_user: User = Depends(get_current_user)):
    plan = current_user.plan or "free"
    return {
        "plan": plan,
        "plan_expires_at": current_user.plan_expires_at,
        "stripe_customer_id": getattr(current_user, "stripe_customer_id", None),
        "features": PLANS.get(plan, PLANS["free"])["features"],
        "seat_cap": PLANS.get(plan, PLANS["free"]).get("seat_cap"),
    }


@router.post("/checkout")
async def create_checkout(
    plan: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if plan not in ("trader", "pro", "desk_500", "desk_2k", "desk_10k"):
        raise HTTPException(400, "invalid plan")

    if not settings.STRIPE_SECRET_KEY:
        current_user.plan = plan
        await db.flush()
        return {
            "mode": "stub",
            "message": f"Plan set to {plan} (demo — no Stripe key). Capacity: {PLANS[plan]['seat_cap']} seats.",
            "plan": plan,
            "checkout_url": None,
        }

    price_map = {
        "trader": settings.STRIPE_PRICE_TRADER,
        "pro": settings.STRIPE_PRICE_PRO,
        "desk_500": getattr(settings, "STRIPE_PRICE_DESK_500", None),
        "desk_2k": getattr(settings, "STRIPE_PRICE_DESK_2K", None),
        "desk_10k": getattr(settings, "STRIPE_PRICE_DESK_10K", None),
    }
    price_id = price_map.get(plan)
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
