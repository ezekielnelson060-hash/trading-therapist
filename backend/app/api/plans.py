from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, TradingPlan

router = APIRouter()


class PlanCreate(BaseModel):
    name: str = "Default Plan"
    max_trades_per_day: Optional[int] = None
    max_risk_per_trade: Optional[float] = None
    max_daily_loss: Optional[float] = None
    allowed_symbols: Optional[List[str]] = None
    other_rules: Optional[Dict[str, Any]] = None
    active: bool = True


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    max_trades_per_day: Optional[int] = None
    max_risk_per_trade: Optional[float] = None
    max_daily_loss: Optional[float] = None
    allowed_symbols: Optional[List[str]] = None
    other_rules: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class PlanOut(BaseModel):
    id: str
    name: str
    max_trades_per_day: Optional[int]
    max_risk_per_trade: Optional[float]
    max_daily_loss: Optional[float]
    allowed_symbols: Optional[List[str]]
    other_rules: Optional[Dict[str, Any]]
    active: bool

    class Config:
        from_attributes = True


def _to_out(p: TradingPlan) -> PlanOut:
    return PlanOut(
        id=p.id,
        name=p.name,
        max_trades_per_day=p.max_trades_per_day,
        max_risk_per_trade=float(p.max_risk_per_trade) if p.max_risk_per_trade is not None else None,
        max_daily_loss=float(p.max_daily_loss) if p.max_daily_loss is not None else None,
        allowed_symbols=p.allowed_symbols,
        other_rules=p.other_rules,
        active=p.active,
    )


@router.get("/", response_model=List[PlanOut])
async def list_plans(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TradingPlan).where(TradingPlan.user_id == current_user.id))
    return [_to_out(p) for p in result.scalars().all()]


@router.get("/active", response_model=Optional[PlanOut])
async def get_active_plan(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TradingPlan).where(TradingPlan.user_id == current_user.id, TradingPlan.active == True)
    )
    p = result.scalar_one_or_none()
    return _to_out(p) if p else None


@router.post("/", response_model=PlanOut)
async def create_plan(body: PlanCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if body.active:
        result = await db.execute(
            select(TradingPlan).where(TradingPlan.user_id == current_user.id, TradingPlan.active == True)
        )
        for old in result.scalars().all():
            old.active = False
    plan = TradingPlan(
        user_id=current_user.id,
        name=body.name,
        max_trades_per_day=body.max_trades_per_day,
        max_risk_per_trade=Decimal(str(body.max_risk_per_trade)) if body.max_risk_per_trade is not None else None,
        max_daily_loss=Decimal(str(body.max_daily_loss)) if body.max_daily_loss is not None else None,
        allowed_symbols=body.allowed_symbols,
        other_rules=body.other_rules,
        active=body.active,
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return _to_out(plan)


@router.patch("/{plan_id}", response_model=PlanOut)
async def update_plan(plan_id: str, body: PlanUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TradingPlan).where(TradingPlan.id == plan_id, TradingPlan.user_id == current_user.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")
    data = body.model_dump(exclude_unset=True)
    if "max_risk_per_trade" in data and data["max_risk_per_trade"] is not None:
        data["max_risk_per_trade"] = Decimal(str(data["max_risk_per_trade"]))
    if "max_daily_loss" in data and data["max_daily_loss"] is not None:
        data["max_daily_loss"] = Decimal(str(data["max_daily_loss"]))
    if data.get("active") is True:
        others = await db.execute(
            select(TradingPlan).where(
                TradingPlan.user_id == current_user.id,
                TradingPlan.id != plan_id,
                TradingPlan.active == True,
            )
        )
        for old in others.scalars().all():
            old.active = False
    for k, v in data.items():
        setattr(plan, k, v)
    await db.flush()
    await db.refresh(plan)
    return _to_out(plan)


@router.delete("/{plan_id}")
async def delete_plan(plan_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TradingPlan).where(TradingPlan.id == plan_id, TradingPlan.user_id == current_user.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")
    await db.delete(plan)
    await db.flush()
    return {"status": "ok"}
