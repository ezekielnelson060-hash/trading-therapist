from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models.behavior import TradingPlan

router = APIRouter()


class OnboardingBody(BaseModel):
    market_type: Optional[str] = None
    trading_style: Optional[str] = None
    max_trades_per_day: Optional[int] = None
    max_risk_per_trade: Optional[float] = None
    cooldown_after_losses: Optional[int] = None
    preferred_sessions: Optional[List[str]] = None
    symbols: Optional[List[str]] = None
    complete: bool = False


@router.get("/status")
async def onboarding_status(current_user: User = Depends(get_current_user)):
    return {
        "complete": bool(getattr(current_user, "onboarding_complete", False)),
        "market_type": getattr(current_user, "market_type", None),
        "trading_style": getattr(current_user, "trading_style", None),
    }


@router.post("/profile")
async def save_profile(
    body: OnboardingBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.market_type is not None:
        current_user.market_type = body.market_type
    if body.trading_style is not None:
        current_user.trading_style = body.trading_style

    if body.max_trades_per_day or body.max_risk_per_trade or body.symbols:
        result = await db.execute(
            select(TradingPlan).where(
                TradingPlan.user_id == current_user.id, TradingPlan.active == True
            )
        )
        plan = result.scalar_one_or_none()
        if not plan:
            plan = TradingPlan(
                user_id=current_user.id,
                name="Trading Constitution",
                active=True,
            )
            db.add(plan)
        if body.max_trades_per_day is not None:
            plan.max_trades_per_day = body.max_trades_per_day
        if body.max_risk_per_trade is not None:
            plan.max_risk_per_trade = Decimal(str(body.max_risk_per_trade))
        if body.symbols:
            plan.allowed_symbols = body.symbols
        if body.cooldown_after_losses is not None:
            rules = plan.other_rules or {}
            rules["cooldown_minutes_after_loss_streak"] = body.cooldown_after_losses
            plan.other_rules = rules

    if body.complete:
        current_user.onboarding_complete = True
    await db.flush()
    return {
        "status": "ok",
        "complete": bool(getattr(current_user, "onboarding_complete", False)),
        "market_type": current_user.market_type,
        "trading_style": current_user.trading_style,
    }
