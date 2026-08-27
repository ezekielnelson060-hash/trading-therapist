from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.services.tilt import full_behavioral_snapshot

router = APIRouter()


class LockBody(BaseModel):
    minutes: int = 60
    reason: Optional[str] = None


@router.get("/")
async def lock_status(current_user: User = Depends(get_current_user)):
    until = current_user.trading_locked_until
    locked = bool(getattr(current_user, "trading_locked", False))
    if until and until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    if locked and until and until < datetime.now(timezone.utc):
        locked = False
    return {
        "locked": locked,
        "until": current_user.trading_locked_until,
        "reason": getattr(current_user, "trading_lock_reason", None),
        "note": "Soft lock in TiltShield — cannot force-close broker positions without broker API rights.",
    }


@router.post("/engage")
async def engage_lock(
    body: LockBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snap = await full_behavioral_snapshot(db, current_user.id)
    tilt = snap.get("tilt") or {}
    minutes = max(5, min(body.minutes, 24 * 60))
    current_user.trading_locked = True
    current_user.trading_locked_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    current_user.trading_lock_reason = body.reason or (
        f"Manual lock · tilt {tilt.get('tilt_score')}/100 · {tilt.get('state_label')}"
    )
    await db.flush()
    return {
        "locked": True,
        "until": current_user.trading_locked_until,
        "reason": current_user.trading_lock_reason,
        "message": f"Trading locked in-app for {minutes} minutes.",
    }


@router.post("/auto-from-tilt")
async def auto_lock_from_tilt(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snap = await full_behavioral_snapshot(db, current_user.id)
    tilt = snap.get("tilt") or {}
    if not tilt.get("do_not_trade"):
        return {"locked": False, "message": "Tilt below pause threshold — no auto-lock."}
    current_user.trading_locked = True
    current_user.trading_locked_until = datetime.now(timezone.utc) + timedelta(minutes=60)
    current_user.trading_lock_reason = (
        f"Auto lock from tilt {tilt.get('tilt_score')}/100 — {tilt.get('recommendation')}"
    )
    await db.flush()
    return {
        "locked": True,
        "until": current_user.trading_locked_until,
        "reason": current_user.trading_lock_reason,
        "message": "Auto soft-lock engaged for 60 minutes.",
    }


@router.post("/release")
async def release_lock(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.trading_locked = False
    current_user.trading_locked_until = None
    current_user.trading_lock_reason = None
    await db.flush()
    return {"locked": False, "message": "Lock released. Stick to your constitution."}
