"""Post-trade behavioral check-ins — turn subjective motives into measurable data."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Trade
from app.models.behavior import EmotionalLog

router = APIRouter()

MOTIVES = [
    "planned_setup",
    "fomo",
    "revenge",
    "fear_of_missing",
    "saw_something",
    "boredom",
    "other",
]


class CheckInCreate(BaseModel):
    trade_id: Optional[str] = None
    motive: str = Field(..., description="planned_setup | fomo | revenge | fear_of_missing | saw_something | boredom | other")
    confidence: int = Field(5, ge=1, le=10)
    emotional_state: int = Field(5, ge=1, le=10, description="1=calm … 10=tilted")
    note: Optional[str] = None


class CheckInOut(BaseModel):
    id: str
    trade_id: Optional[str]
    motive: Optional[str]
    confidence: Optional[int]
    emotional_state: Optional[int]
    note: Optional[str]
    logged_at: Optional[datetime]


@router.post("/", response_model=CheckInOut)
async def create_checkin(
    body: CheckInCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.motive not in MOTIVES:
        raise HTTPException(400, f"motive must be one of {MOTIVES}")
    if body.trade_id:
        r = await db.execute(
            select(Trade).where(Trade.id == body.trade_id, Trade.user_id == current_user.id)
        )
        if not r.scalar_one_or_none():
            raise HTTPException(404, "Trade not found")

    anxiety = max(1, min(5, (body.emotional_state + 1) // 2))
    conf = max(1, min(5, (body.confidence + 1) // 2))
    free = f"motive={body.motive}|state={body.emotional_state}|conf={body.confidence}"
    if body.note:
        free += f"|note={body.note[:200]}"

    log = EmotionalLog(
        user_id=current_user.id,
        trade_id=body.trade_id,
        anxiety=anxiety,
        confidence=conf,
        free_text=free,
        source="post_trade_checkin",
    )
    db.add(log)
    await db.flush()
    return CheckInOut(
        id=log.id,
        trade_id=log.trade_id,
        motive=body.motive,
        confidence=body.confidence,
        emotional_state=body.emotional_state,
        note=body.note,
        logged_at=log.logged_at or datetime.now(timezone.utc),
    )


@router.get("/", response_model=List[CheckInOut])
async def list_checkins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmotionalLog)
        .where(EmotionalLog.user_id == current_user.id)
        .order_by(EmotionalLog.logged_at.desc())
        .limit(50)
    )
    out = []
    for log in result.scalars().all():
        motive = None
        conf = log.confidence
        state = log.anxiety
        note = None
        if log.free_text and "motive=" in log.free_text:
            parts = dict(p.split("=", 1) for p in log.free_text.split("|") if "=" in p)
            motive = parts.get("motive")
            conf = int(parts["conf"]) if parts.get("conf", "").isdigit() else conf
            state = int(parts["state"]) if parts.get("state", "").isdigit() else state
            note = parts.get("note")
        out.append(
            CheckInOut(
                id=log.id,
                trade_id=log.trade_id,
                motive=motive,
                confidence=conf,
                emotional_state=state,
                note=note,
                logged_at=log.logged_at,
            )
        )
    return out


@router.get("/motives/stats")
async def motive_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmotionalLog)
        .where(EmotionalLog.user_id == current_user.id, EmotionalLog.source == "post_trade_checkin")
        .order_by(EmotionalLog.logged_at.desc())
        .limit(200)
    )
    logs = list(result.scalars().all())
    buckets = {}
    for log in logs:
        if not log.free_text or "motive=" not in log.free_text:
            continue
        parts = dict(p.split("=", 1) for p in log.free_text.split("|") if "=" in p)
        motive = parts.get("motive", "other")
        buckets.setdefault(motive, {"count": 0, "with_trade": 0, "wins": 0, "losses": 0, "pnl": 0.0})
        buckets[motive]["count"] += 1
        if log.trade_id:
            tr = await db.execute(select(Trade).where(Trade.id == log.trade_id))
            trade = tr.scalar_one_or_none()
            if trade and trade.net_pnl is not None:
                buckets[motive]["with_trade"] += 1
                pnl = float(trade.net_pnl)
                buckets[motive]["pnl"] += pnl
                if pnl > 0:
                    buckets[motive]["wins"] += 1
                elif pnl < 0:
                    buckets[motive]["losses"] += 1
    lines = []
    for motive, b in buckets.items():
        wt = b["with_trade"]
        if wt:
            loss_rate = round(100 * b["losses"] / wt)
            lines.append(
                {
                    "motive": motive,
                    "count": b["count"],
                    "linked_trades": wt,
                    "loss_rate_pct": loss_rate,
                    "total_pnl": round(b["pnl"], 2),
                    "insight": f'Your data: "{motive}" linked trades lost {loss_rate}% of the time.'
                    if wt >= 3
                    else "Need more linked check-ins for a stable rate.",
                }
            )
    return {"motives": lines, "message": "Subjective motives correlated with real outcomes."}
