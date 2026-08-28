"""Day 1–30 onboarding drip."""
from __future__ import annotations
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings
from app.models import User
from app.services.alerts import send_email

logger = logging.getLogger(__name__)

DRIP: Dict[int, Tuple[str, str]] = {
    1: (
        "Your strategy isn't the problem",
        "Welcome to TiltShield.\n\nMost platforms show P&L. We watch the part of trading they ignore: you.\n\n1) Connect MT5 or IBKR (or demo data)\n2) Set your Trading Constitution\n3) Open State for your first Tilt Score\n\n— TiltShield\n",
    ),
    2: (
        "Know your normal",
        "TiltShield builds a model of how YOU trade.\n\nAfter closed trades we learn frequency, pace, symbols.\nYour Constitution is the anchor until baseline is ready.\n\n— TiltShield\n",
    ),
    3: (
        "Connect real data",
        "Manual journaling rewrites history.\n\nConnect MT5 or upload IBKR Flex on Data — or load the demo sequence to see tilt spike.\n\n— TiltShield\n",
    ),
    5: (
        "Observe → Detect → Intervene",
        "When tilt rises we recommend a pause. Acknowledge or override (logged).\nThat record matters for you and for prop risk desks.\n\n— TiltShield\n",
    ),
    7: (
        "Week 1 check-in",
        "Did you break your rules after a loss this week?\n\nOpen Weekly. Focus for week 2: after the second consecutive loss, wait 30 minutes.\n\n— TiltShield\n",
    ),
    10: (
        "Motives become data",
        "Use Check-in: Planned / FOMO / Revenge / Boredom.\nOver time we correlate motives with outcomes.\n\n— TiltShield\n",
    ),
    14: (
        "Two weeks of behavior",
        "Baseline, tilt signals, daily autopsy.\nIf tilt is often elevated, shrink max trades/day before adding risk.\n\n— TiltShield\n",
    ),
    21: (
        "Intervention is the product",
        "Journals explain after the session. TiltShield interrupts during it.\nProp desks ask: who is deteriorating right now?\n\n— TiltShield\n",
    ),
    30: (
        "Day 30 — the category",
        "Behavioral risk management:\n1) Know your normal\n2) Know when you're breaking it\n3) Know what to do next\n\n— TiltShield\n",
    ),
}


async def maybe_send_drip(db: AsyncSession, user: User) -> Optional[int]:
    if not settings.RESEND_API_KEY or not user.email:
        return None
    created = user.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if not created:
        return None
    days = (datetime.now(timezone.utc) - created).days + 1
    sent = getattr(user, "drip_emails_sent", None) or 0
    candidates = sorted(d for d in DRIP if d <= days and d > sent)
    if not candidates:
        return None
    day = candidates[0]
    subject, body = DRIP[day]
    ok = await send_email(user.email, f"[TiltShield] {subject}", body)
    if ok:
        user.drip_emails_sent = day
        user.last_drip_email_at = datetime.now(timezone.utc)
        await db.flush()
        logger.info("Drip day %s sent to %s", day, user.email)
        return day
    return None
