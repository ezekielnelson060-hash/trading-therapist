from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import ChatSession, ChatMessage, Trade, User, BehavioralEvent
from app.services.therapist import generate_therapist_reply
from app.services.tilt import full_behavioral_snapshot

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    related_trade_count: int = 0
    related_events: List[str] = []
    llm_used: bool = False
    tilt_score: Optional[int] = None


@router.post("/", response_model=ChatResponse)
async def chat_with_therapist(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = None
    if body.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == body.session_id,
                ChatSession.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()

    if not session:
        session = ChatSession(user_id=current_user.id, title=body.message[:60])
        db.add(session)
        await db.flush()

    db.add(ChatMessage(session_id=session.id, role="user", content=body.message))

    trades_result = await db.execute(
        select(Trade)
        .where(Trade.user_id == current_user.id)
        .order_by(Trade.entry_time.desc())
        .limit(15)
    )
    recent_trades = list(trades_result.scalars().all())

    events_result = await db.execute(
        select(BehavioralEvent)
        .where(
            BehavioralEvent.user_id == current_user.id,
            BehavioralEvent.acknowledged == False,
        )
        .order_by(BehavioralEvent.detected_at.desc())
        .limit(8)
    )
    recent_events = list(events_result.scalars().all())

    snap = await full_behavioral_snapshot(db, current_user.id)
    tilt = snap.get("tilt")

    from app.core.config import settings

    llm_used = bool(settings.OPENAI_API_KEY)

    reply = await generate_therapist_reply(
        body.message, recent_trades, recent_events, tilt=tilt
    )

    db.add(ChatMessage(session_id=session.id, role="assistant", content=reply))
    await db.flush()

    return ChatResponse(
        session_id=session.id,
        reply=reply,
        related_trade_count=len(recent_trades),
        related_events=[e.title for e in recent_events if e.title],
        llm_used=llm_used,
        tilt_score=tilt.get("tilt_score") if tilt else None,
    )


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .limit(20)
    )
    return [
        {"id": s.id, "title": s.title, "created_at": s.created_at}
        for s in result.scalars().all()
    ]
