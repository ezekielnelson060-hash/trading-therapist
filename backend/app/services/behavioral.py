"""Behavioral analytics — detect patterns from real trades."""
from datetime import timedelta
from decimal import Decimal
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Trade, BehavioralEvent, TradingPlan


async def analyze_new_trade(db: AsyncSession, user_id: str, trade: Trade) -> List[BehavioralEvent]:
    events: List[BehavioralEvent] = []
    if trade.status != "closed":
        return events

    result = await db.execute(
        select(Trade)
        .where(Trade.user_id == user_id, Trade.status == "closed")
        .order_by(Trade.entry_time.desc())
        .limit(30)
    )
    recent = list(result.scalars().all())

    if len(recent) >= 2:
        prev = recent[1] if recent[0].id == trade.id else recent[0]
        if prev.net_pnl is not None and prev.net_pnl < 0 and trade.entry_time and prev.exit_time:
            delta = trade.entry_time - prev.exit_time
            if timedelta(0) <= delta <= timedelta(minutes=30):
                e = BehavioralEvent(
                    user_id=user_id,
                    trade_ids=[prev.id, trade.id],
                    event_type="revenge_trading",
                    severity=Decimal("75"),
                    title="Possible revenge trading",
                    description=f"Re-entered within {int(delta.total_seconds()//60)} min after a loss on {prev.symbol}.",
                )
                db.add(e)
                events.append(e)

    if len(recent) >= 2:
        prev = None
        for t in recent:
            if t.id != trade.id:
                prev = t
                break
        if prev and prev.net_pnl is not None and prev.net_pnl < 0:
            if trade.quantity and prev.quantity and trade.quantity > prev.quantity * Decimal("1.5"):
                e = BehavioralEvent(
                    user_id=user_id,
                    trade_ids=[prev.id, trade.id],
                    event_type="size_increase_after_loss",
                    severity=Decimal("70"),
                    title="Size increased after a loss",
                    description=f"Size {float(trade.quantity)} vs previous {float(prev.quantity)} after a loss.",
                )
                db.add(e)
                events.append(e)

    day_start = trade.entry_time.replace(hour=0, minute=0, second=0, microsecond=0) if trade.entry_time else None
    if day_start:
        day_end = day_start + timedelta(days=1)
        day_trades = [t for t in recent if t.entry_time and day_start <= t.entry_time < day_end]
        plan_result = await db.execute(
            select(TradingPlan).where(TradingPlan.user_id == user_id, TradingPlan.active == True)
        )
        plan = plan_result.scalar_one_or_none()
        limit = plan.max_trades_per_day if plan and plan.max_trades_per_day else 10
        if len(day_trades) > limit:
            e = BehavioralEvent(
                user_id=user_id,
                trade_ids=[t.id for t in day_trades[:5]],
                event_type="overtrading",
                severity=Decimal("65"),
                title="Overtrading detected",
                description=f"{len(day_trades)} trades today (limit {limit}).",
            )
            db.add(e)
            events.append(e)

    plan_result = await db.execute(
        select(TradingPlan).where(TradingPlan.user_id == user_id, TradingPlan.active == True)
    )
    plan = plan_result.scalar_one_or_none()
    if plan and plan.allowed_symbols and trade.symbol not in plan.allowed_symbols:
        e = BehavioralEvent(
            user_id=user_id,
            trade_ids=[trade.id],
            event_type="plan_deviation",
            severity=Decimal("60"),
            title="Symbol outside trading plan",
            description=f"{trade.symbol} is not in allowed symbols: {', '.join(plan.allowed_symbols)}.",
        )
        db.add(e)
        events.append(e)

    if events:
        await db.flush()
    return events
