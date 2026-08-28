from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from datetime import datetime, timezone

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
    snap = await full_behavioral_snapshot(db, current_user.id)
    try:
        from app.services.alerts import evaluate_tilt_alerts

        await evaluate_tilt_alerts(db, current_user, snap.get("tilt") or {})
    except Exception:
        pass
    return snap


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
        "cost_of_behavior": snap.get("cost_of_behavior"),
        "weekly": snap.get("weekly"),
        "events": events,
        "message": snap["message"],
    }


@router.get("/weekly")
async def weekly_behavioral_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snap = await full_behavioral_snapshot(db, current_user.id)
    week = dict(snap.get("weekly") or {})
    if "focus_next_week" not in week:
        revenge = week.get("revenge_flags") or 0
        over = week.get("overtrading_flags") or 0
        week["needs_attention"] = (
            (["Revenge entries after consecutive losses"] if revenge else [])
            + (["Trade frequency above plan/baseline"] if over else [])
        ) or ["No major flags this week"]
        week["improved"] = (
            ["Fewer revenge flags than a chaotic session"] if not revenge else []
        ) or ["Keep following your constitution"]
        week["focus_next_week"] = (
            "Do not enter another position for 30 minutes after your second consecutive loss."
            if revenge
            else (
                "Cap daily trades at your constitution max and stop when hit."
                if over
                else "Protect the baseline: same size, same cooldown after any loss."
            )
        )
    return {
        "weekly": week,
        "cost_of_behavior": snap.get("cost_of_behavior"),
        "tilt": snap.get("tilt"),
        "message": "Weekly behavior is the product. P&L is secondary.",
    }


@router.post("/pause/acknowledge")
async def acknowledge_pause(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snap = await full_behavioral_snapshot(db, current_user.id)
    tilt = snap.get("tilt") or {}
    e = BehavioralEvent(
        user_id=current_user.id,
        event_type="pause_acknowledged",
        severity=Decimal(str(tilt.get("tilt_score") or 0)),
        title="Pause acknowledged",
        description=(
            f"Trader acknowledged tilt {tilt.get('tilt_score')}/100 "
            f"({tilt.get('state_label')}). Recommendation: {tilt.get('recommendation')}"
        ),
        details={"tilt": tilt, "at": datetime.now(timezone.utc).isoformat()},
        acknowledged=True,
    )
    db.add(e)
    await db.flush()
    return {
        "status": "ok",
        "message": "Pause logged. Do not increase risk to recover losses.",
        "tilt_score": tilt.get("tilt_score"),
    }


@router.post("/pause/override")
async def override_pause(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snap = await full_behavioral_snapshot(db, current_user.id)
    tilt = snap.get("tilt") or {}
    e = BehavioralEvent(
        user_id=current_user.id,
        event_type="pause_override",
        severity=Decimal(str(tilt.get("tilt_score") or 0)),
        title="Pause overridden",
        description=(
            f"Trader continued despite tilt {tilt.get('tilt_score')}/100. "
            "This override is stored against your behavioral record."
        ),
        details={"tilt": tilt, "at": datetime.now(timezone.utc).isoformat()},
        acknowledged=False,
    )
    db.add(e)
    await db.flush()
    return {
        "status": "ok",
        "warning": "Override logged. Your constitution still applies.",
        "tilt_score": tilt.get("tilt_score"),
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
