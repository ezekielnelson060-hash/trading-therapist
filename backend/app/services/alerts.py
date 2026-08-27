"""In-app alerts + optional email (Resend) when tilt spikes."""
from __future__ import annotations
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import logging

from app.core.config import settings
from app.models.teams import Alert
from app.models import User

logger = logging.getLogger(__name__)


async def create_alert(
    db: AsyncSession,
    user_id: str,
    alert_type: str,
    title: str,
    body: str,
    severity: str = "warning",
    email: Optional[str] = None,
) -> Alert:
    since = datetime.now(timezone.utc) - timedelta(hours=2)
    existing = await db.execute(
        select(Alert)
        .where(
            Alert.user_id == user_id,
            Alert.alert_type == alert_type,
            Alert.created_at >= since,
        )
        .limit(1)
    )
    found = existing.scalar_one_or_none()
    if found:
        return found

    alert = Alert(
        user_id=user_id,
        alert_type=alert_type,
        title=title,
        body=body,
        severity=severity,
    )
    db.add(alert)
    await db.flush()

    if email and settings.RESEND_API_KEY:
        sent = await send_email(email, title, body)
        alert.email_sent = sent
        await db.flush()
    return alert


async def send_email(to: str, subject: str, text: str) -> bool:
    if not settings.RESEND_API_KEY:
        return False
    try:
        import httpx

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json={
                    "from": settings.ALERT_FROM_EMAIL,
                    "to": [to],
                    "subject": subject,
                    "text": text,
                },
            )
            if r.status_code >= 400:
                logger.warning("Resend failed: %s %s", r.status_code, r.text)
                return False
            return True
    except Exception as e:
        logger.warning("Email send failed: %s", e)
        return False


async def evaluate_tilt_alerts(db: AsyncSession, user: User, tilt: dict) -> Optional[Alert]:
    score = tilt.get("tilt_score") or 0
    if score < 70:
        return None
    return await create_alert(
        db,
        user.id,
        alert_type="tilt_high",
        title=f"Tilt {score}/100 — HIGH RISK",
        body=(
            f"{tilt.get('recommendation')}\n\n"
            "Your trading behavior is outside your baseline. "
            "Pause recommended. Do not increase risk to recover losses."
        ),
        severity="critical",
        email=user.email,
    )
