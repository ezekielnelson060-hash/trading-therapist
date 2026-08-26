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


@router.get("/summary")
async def trade_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(func.count(Trade.id).label("total_trades"),
               func.sum(Trade.net_pnl).label("total_pnl"),
               func.avg(Trade.net_pnl).label("avg_pnl"))
        .where(Trade.user_id == current_user.id, Trade.status == "closed")
    )
    row = result.one()
    wins = await db.execute(
        select(func.count(Trade.id)).where(
            Trade.user_id == current_user.id, Trade.status == "closed", Trade.net_pnl > 0)
    )
    win_count = wins.scalar() or 0
    total = row.total_trades or 0
    win_rate = (win_count / total * 100) if total > 0 else 0
    return {
        "total_trades": total,
        "total_pnl": float(row.total_pnl or 0),
        "avg_pnl": float(row.avg_pnl or 0),
        "win_rate": round(win_rate, 2),
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
        user_id=current_user.id, symbol=body.symbol.upper(), side=body.side.lower(),
        quantity=body.quantity, entry_price=body.entry_price, exit_price=body.exit_price,
        entry_time=body.entry_time, exit_time=body.exit_time, net_pnl=body.net_pnl,
        commission=body.commission, status="closed" if body.exit_time else "open", source="manual",
    )
    db.add(trade)
    await db.flush()
    await db.refresh(trade)
    return trade
