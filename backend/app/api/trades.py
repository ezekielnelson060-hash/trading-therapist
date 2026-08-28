from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Trade, User

router = APIRouter()


class TradeOut(BaseModel):
    id: str
    symbol: str
    side: str
    quantity: Decimal
    entry_price: Optional[Decimal]
    exit_price: Optional[Decimal]
    entry_time: datetime
    exit_time: Optional[datetime]
    net_pnl: Optional[Decimal]
    commission: Decimal
    status: str
    source: str
    class Config:
        from_attributes = True


class TradeCreateManual(BaseModel):
    symbol: str
    side: str
    quantity: Decimal
    entry_price: Decimal
    exit_price: Optional[Decimal] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    net_pnl: Optional[Decimal] = None
    commission: Decimal = Decimal("0")


@router.get("/", response_model=List[TradeOut])
async def list_trades(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    symbol: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Trade).where(Trade.user_id == current_user.id).order_by(desc(Trade.entry_time))
    if symbol:
        q = q.where(Trade.symbol == symbol)
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/with-context")
async def trades_with_behavioral_context(
    limit: int = Query(40, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trade list with behavioral verdict (Disciplined / Behavioral break)."""
    from app.models.behavior import TradingPlan
    from app.services.trade_context import annotate_trades

    result = await db.execute(
        select(Trade)
        .where(Trade.user_id == current_user.id)
        .order_by(desc(Trade.entry_time))
        .limit(limit)
    )
    trades = list(result.scalars().all())
    plan_r = await db.execute(
        select(TradingPlan).where(TradingPlan.user_id == current_user.id, TradingPlan.active == True)
    )
    plan = plan_r.scalar_one_or_none()
    return {"trades": annotate_trades(trades, plan), "count": len(trades)}


@router.get("/summary")
async def trade_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.count(Trade.id).label("total_trades"),
            func.sum(Trade.net_pnl).label("total_pnl"),
            func.avg(Trade.net_pnl).label("avg_pnl"),
        ).where(Trade.user_id == current_user.id, Trade.status == "closed")
    )
    row = result.one()
    wins = await db.execute(
        select(func.count(Trade.id)).where(
            Trade.user_id == current_user.id, Trade.status == "closed", Trade.net_pnl > 0
        )
    )
    win_count = wins.scalar() or 0
    total = row.total_trades or 0
    win_rate = (win_count / total) if total > 0 else 0
    return {
        "total_trades": total,
        "total_pnl": float(row.total_pnl or 0),
        "avg_pnl": float(row.avg_pnl or 0),
        "win_rate": round(win_rate, 4),
        "wins": win_count,
        "losses": total - win_count,
    }


@router.post("/manual", response_model=TradeOut)
async def create_manual_trade(
    body: TradeCreateManual,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    trade = Trade(
        user_id=current_user.id,
        symbol=body.symbol.upper(),
        side=body.side.lower(),
        quantity=body.quantity,
        entry_price=body.entry_price,
        exit_price=body.exit_price,
        entry_time=body.entry_time,
        exit_time=body.exit_time,
        net_pnl=body.net_pnl,
        commission=body.commission,
        status="closed" if body.exit_time else "open",
        source="manual",
    )
    db.add(trade)
    await db.flush()
    await db.refresh(trade)
    return trade


@router.post("/demo-seed")
async def seed_demo_behavior(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Synthetic loss → size-up → rapid re-entry sequence to test Tilt Engine."""
    from datetime import timedelta, timezone
    from app.services.behavioral import analyze_new_trade

    now = datetime.now(timezone.utc)
    specs = [
        ("XAUUSD", "buy", Decimal("0.10"), Decimal("50"), -180),
        ("XAUUSD", "buy", Decimal("0.10"), Decimal("30"), -150),
        ("EURUSD", "sell", Decimal("0.10"), Decimal("-20"), -120),
        ("XAUUSD", "buy", Decimal("0.10"), Decimal("40"), -90),
        ("XAUUSD", "buy", Decimal("0.10"), Decimal("-80"), -45),
        ("XAUUSD", "buy", Decimal("0.10"), Decimal("-60"), -35),
        ("XAUUSD", "buy", Decimal("0.18"), Decimal("-40"), -25),
        ("XAUUSD", "buy", Decimal("0.20"), Decimal("-55"), -15),
        ("EURUSD", "buy", Decimal("0.15"), Decimal("-30"), -8),
        ("XAUUSD", "buy", Decimal("0.22"), Decimal("-25"), -3),
    ]
    created = 0
    events_n = 0
    for i, (sym, side, qty, pnl, mins_ago) in enumerate(specs):
        entry = now + timedelta(minutes=mins_ago - 12)
        exit_t = now + timedelta(minutes=mins_ago)
        external_id = f"demo-{current_user.id[:8]}-{i}-{int(exit_t.timestamp())}"
        existing = await db.execute(select(Trade).where(Trade.external_id == external_id))
        if existing.scalar_one_or_none():
            continue
        trade = Trade(
            user_id=current_user.id,
            symbol=sym,
            side=side,
            quantity=qty,
            entry_price=Decimal("1.0"),
            exit_price=Decimal("1.0"),
            entry_time=entry,
            exit_time=exit_t,
            net_pnl=pnl,
            commission=Decimal("0"),
            status="closed",
            source="demo_seed",
            external_id=external_id,
        )
        db.add(trade)
        await db.flush()
        created += 1
        evs = await analyze_new_trade(db, current_user.id, trade)
        events_n += len(evs or [])
    await db.flush()
    return {
        "status": "ok",
        "created": created,
        "behavioral_events": events_n,
        "note": "Demo data only. Refresh State to see Tilt Score.",
    }
