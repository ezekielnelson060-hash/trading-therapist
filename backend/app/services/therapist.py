"""Evidence-based coach — grounded in real trades + tilt signals."""
from typing import List, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a trading behavioral risk coach, not a motivational chatbot.
Your job: stop the trader from repeating the behavior that costs money.

Rules:
- Only cite trades, limits, and events provided in the context. Never invent numbers.
- Prefer: observe → name the pattern → quantify → one concrete rule for next session.
- If they exceeded max trades/day or show revenge/size-up after loss, say so plainly.
- Do not give financial advice on what to buy/sell. Focus on process and risk behavior.
- Open like a reviewer of their data, not a blank chatbot.
"""


def build_context(trades: List[Any], events: List[Any], tilt: Optional[dict] = None) -> str:
    parts = []
    if tilt:
        parts.append(
            f"Tilt score: {tilt.get('tilt_score')}/100 ({tilt.get('state_label')}). "
            f"Recommendation: {tilt.get('recommendation')}"
        )
        signals = tilt.get("signals") or {}
        for s in signals.values():
            if s.get("status") in ("red", "amber"):
                parts.append(f"Signal [{s.get('status')}]: {s.get('label')} — {s.get('detail')}")
    if trades:
        lines = []
        for t in trades[:15]:
            pnl = f"{float(t.net_pnl):+.2f}" if t.net_pnl is not None else "n/a"
            lines.append(f"- {t.symbol} {t.side} size={t.quantity} pnl={pnl}")
        parts.append("Recent real trades:\n" + "\n".join(lines))
    else:
        parts.append("No closed trades in system yet.")
    if events:
        elines = [f"- [{e.event_type}] {e.title}: {e.description}" for e in events[:8]]
        parts.append("Stored behavioral events:\n" + "\n".join(elines))
    return "\n\n".join(parts)


def rule_based_reply(user_message: str, trades: List[Any], events: List[Any], tilt: Optional[dict] = None) -> str:
    msg = (user_message or "").lower()
    bits = []
    n = len(trades or [])
    if n:
        losses = sum(1 for x in trades if x.net_pnl is not None and float(x.net_pnl) < 0)
        bits.append(f"I reviewed your last {n} trades ({losses} losers on record in that window).")
        red_signals = [
            s for s in (tilt.get("signals") or {}).values()
            if s.get("status") in ("red", "amber")
        ] if tilt else []
        if red_signals:
            top = red_signals[0]
            bits.append(
                f"One recurring pattern worth addressing: **{top.get('label')}** — {top.get('detail')}"
            )
            bits.append("Want the estimated cost of this behavior, or a single rule for the next session?")
    if tilt:
        bits.append(
            f"Your current tilt score is **{tilt.get('tilt_score')}/100** ({tilt.get('state_label')}). "
            f"{tilt.get('recommendation')}"
        )
        for s in (tilt.get("signals") or {}).values():
            if s.get("status") == "red":
                bits.append(f"• {s.get('label')}: {s.get('detail')}")
        if tilt.get("do_not_trade"):
            bits.append(
                "Protocol: treat this as a hard pause. Do not increase risk to recover losses."
            )
    if events:
        for e in events[:3]:
            bits.append(f"• {e.title} — {e.description}")
    if not trades:
        bits.append(
            "I don't have closed trades yet. Connect MT5 or upload IBKR Flex so coaching is evidence-based, "
            "not generic advice."
        )
    elif not bits:
        bits.append(
            f"You have {len(trades)} closed trades on record. "
            "Ask about revenge trading, overtrading, or plan adherence and I'll use those numbers."
        )
    if "revenge" in msg or "tilt" in msg or "stop" in msg:
        bits.append(
            "Rule for next session: after any loss, wait at least 20 minutes and keep size at or below baseline. "
            "No 'make it back' trades."
        )
    return "\n\n".join(bits)


async def generate_therapist_reply(
    user_message: str,
    trades: List[Any],
    events: List[Any],
    tilt: Optional[dict] = None,
) -> str:
    context = build_context(trades, events, tilt)
    if settings.OPENAI_API_KEY:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.5,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content or rule_based_reply(
                user_message, trades, events, tilt
            )
        except Exception as e:
            logger.warning("OpenAI therapist failed: %s", e)
    return rule_based_reply(user_message, trades, events, tilt)
