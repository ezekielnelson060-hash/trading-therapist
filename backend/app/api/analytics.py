from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, BehavioralEvent
from app.services.tilt import full_behavioral_snapshot

router = APIRouter()


@router.get("/tilt")
async def get_tilt(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Primary product surface: tilt score, baseline, signals, do-not-trade."""
    return await full_behavioral_snapshot(db, current_user.id)


@router.get("/baseline")
async def get_baseline(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snap = await full_behavioral_snapshot(db, current_user.id)
    return snap["baseline"]


@router.get("/autopsy")
async def get_autopsy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snap = await full_behavioral_snapshot(db, current_user.id)
    return snap["autopsy"]


@router.get("/behavioral")
async def behavioral_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snap = await full_behavioral_snapshot(db, current_user.id)
    tilt = snap["tilt"]
    events_result = await db.execute(
        select(BehavioralEvent)
        .where(BehavioralEvent.user_id == current_user.id)
        .order_by(BehavioralEvent.detected_at.desc())
        .limit(20)
    )
    events = [
        {
            "id": e.id,
            "type": e.event_type,
            "severity": float(e.severity) if e.severity is not None else 0,
            "title": e.title,
            "description": e.description,
            "detected_at": e.detected_at.isoformat() if e.detected_at else None,
            "acknowledged": e.acknowledged,
        }
        for e in events_result.scalars().all()
    ]
    return {
        "total_trades_analyzed": snap["total_closed_trades"],
        "tilt_score": tilt["tilt_score"],
        "state": tilt["state"],
        "state_label": tilt["state_label"],
        "do_not_trade": tilt["do_not_trade"],
        "recommendation": tilt["recommendation"],
        "signals": tilt["signals"],
        "baseline": snap["baseline"],
        "autopsy": snap["autopsy"],
        "constitution": snap["constitution"],
        "events": events,
        "message": snap["message"],
    }


@router.get("/events")
async def list_behavioral_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BehavioralEvent)
        .where(BehavioralEvent.user_id == current_user.id)
        .order_by(BehavioralEvent.detected_at.desc())
        .limit(50)
    )
    return [
        {
            "id": e.id,
            "type": e.event_type,
            "severity": float(e.severity) if e.severity is not None else 0,
            "title": e.title,
            "description": e.description,
            "details": e.details,
            "detected_at": e.detected_at,
            "acknowledged": e.acknowledged,
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
            BehavioralEvent.id == event_id, BehavioralEvent.user_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")
    event.acknowledged = True
    await db.flush()
    return {"status": "ok", "id": event.id}
