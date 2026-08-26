"""AI Trading Therapist – OpenAI when keyed, rule-based fallback otherwise."""
from typing import List, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI Trading Therapist. Use CBT principles.
Ground advice in the trader's ACTUAL trade data. Be direct and practical.
Never invent trades. Prefer concrete rules over vague motivation."""


def build_context(trades: List[Any], events: List[Any]) -> str:
    parts = []
    if trades:
        lines = []
        for t in trades[:12]:
            pnl = f"{float(t.net_pnl):+.2f}" if t.net_pnl is not None else "open"
            lines.append(f"- {t.symbol} {t.side} size={t.quantity} pnl={pnl}")
        parts.append("Recent real trades:\n" + "\n".join(lines))
    else:
        parts.append("No trades imported yet.")
    if events:
        elines = [f"- [{e.event_type}] {e.title}" for e in events[:6]]
        parts.append("Open behavioral flags:\n" + "\n".join(elines))
    return "\n\n".join(parts)


async def generate_therapist_reply(user_message: str, trades: List[Any], events: List[Any]) -> str:
    context = build_context(trades, events)
    if settings.OPENAI_API_KEY:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.6,
                max_tokens=450,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}")
    return _rule_based_reply(user_message, trades, events)


def _rule_based_reply(user_message: str, trades: List[Any], events: List[Any]) -> str:
    lower = user_message.lower()
    event_types = [e.event_type for e in events]
    if "revenge" in lower or "revenge_trading" in event_types:
        return (
            "Revenge trading is expensive. After any loss, wait 15–30 minutes, "
            "stand up, and only re-enter if the setup still matches your written plan."
        )
    if "overtrad" in lower or "overtrading" in event_types:
        return (
            "High trade frequency often means emotion, not edge. "
            "Set a hard daily trade limit and treat it as non-negotiable."
        )
    if "size" in lower or "size_increase_after_loss" in event_types:
        return (
            "Increasing size after a loss turns small holes into large ones. "
            "Reset to base size after any losing trade."
        )
    if not trades:
        return (
            "I don't have your real trade data yet. Connect MT5 or upload an IBKR Flex CSV, "
            "then I can coach you on what you actually did."
        )
    return (
        f"I can see {len(trades)} recent trades"
        + (f" and {len(events)} open flags" if events else "")
        + ". Tell me what you're struggling with (revenge, overtrading, fear, FOMO) "
        "and I'll give you a concrete fix grounded in your history."
    )
