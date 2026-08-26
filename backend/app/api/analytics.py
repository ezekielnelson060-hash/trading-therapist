from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Trade, BehavioralEvent, User

router = APIRouter()


@router.get("/behavioral")
async def get_behavioral_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Trade).where(Trade.user_id == current_user.id, Trade.status == "closed")
        .order_by(Trade.entry_time.desc()).limit(200)
    )
    trades = list(result.scalars().all())

    events_result = await db.execute(
        select(BehavioralEvent).where(BehavioralEvent.user_id == current_user.id)
        .order_by(BehavioralEvent.detected_at.desc()).limit(20)
    )
    events = [
        {
            "id": e.id, "type": e.event_type, "severity": float(e.severity),
            "title": e.title, "description": e.description,
            "detected_at": e.detected_at.isoformat() if e.detected_at else None,
            "acknowledged": e.acknowledged,
        }
        for e in events_result.scalars().all()
    ]

    if not trades:
        return {"message": "No trades yet. Connect a broker.", "events": [], "total_trades_analyzed": 0}

    wins = sum(1 for t in trades[:30] if t.net_pnl is not None and t.net_pnl > 0)
    recent_n = min(30, len(trades))
    win_rate = (wins / recent_n * 100) if recent_n else 0

    return {
        "total_trades_analyzed": len(trades),
        "recent_win_rate": round(win_rate, 1),
        "events": events,
        "message": f"{len(events)} behavioral event(s) from your real trade history." if events else "No strong negative patterns stored yet.",
    }


@router.get("/events")
async def list_behavioral_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BehavioralEvent).where(BehavioralEvent.user_id == current_user.id)
        .order_by(BehavioralEvent.detected_at.desc()).limit(50)
    )
    return [
        {
            "id": e.id, "type": e.event_type, "severity": float(e.severity),
            "title": e.title, "description": e.description, "details": e.details,
            "detected_at": e.detected_at, "acknowledged": e.acknowledged,
        }
        for e in result.scalars().all()
    ]


@router.post("/events/{event_id}/acknowledge")
async def acknowledge_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BehavioralEvent).where(
            BehavioralEvent.id == event_id, BehavioralEvent.user_id == current_user.id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")
    event.acknowledged = True
    await db.flush()
    return {"status": "ok", "id": event.id}
