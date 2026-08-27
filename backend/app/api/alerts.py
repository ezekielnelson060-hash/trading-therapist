from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models.teams import Alert
from app.services.tilt import full_behavioral_snapshot
from app.services.alerts import evaluate_tilt_alerts

router = APIRouter()


@router.get("/")
async def list_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert)
        .where(Alert.user_id == current_user.id)
        .order_by(Alert.created_at.desc())
        .limit(50)
    )
    return [
        {
            "id": a.id,
            "type": a.alert_type,
            "title": a.title,
            "body": a.body,
            "severity": a.severity,
            "read": a.read,
            "email_sent": a.email_sent,
            "created_at": a.created_at,
        }
        for a in result.scalars().all()
    ]


@router.post("/evaluate")
async def evaluate_now(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snap = await full_behavioral_snapshot(db, current_user.id)
    tilt = snap.get("tilt") or {}
    alert = await evaluate_tilt_alerts(db, current_user, tilt)
    await db.flush()
    return {
        "tilt_score": tilt.get("tilt_score"),
        "do_not_trade": tilt.get("do_not_trade"),
        "alert_created": bool(alert),
        "alert": (
            {"id": alert.id, "title": alert.title, "email_sent": alert.email_sent}
            if alert
            else None
        ),
    }


@router.post("/{alert_id}/read")
async def mark_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id)
    )
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(404, "Alert not found")
    a.read = True
    await db.flush()
    return {"status": "ok"}
