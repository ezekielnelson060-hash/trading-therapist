"""Per-trade behavioral verdict — not a plain journal row."""
from __future__ import annotations
from typing import Any, List, Dict, Optional


def annotate_trades(trades: List[Any], plan: Optional[Any] = None) -> List[Dict]:
    if not trades:
        return []

    chrono = sorted(trades, key=lambda t: t.entry_time or t.exit_time)
    prev = None
    streak_loss = 0
    by_id: Dict[str, Dict] = {}

    for t in chrono:
        flags = []
        severity = "green"
        verdict = "DISCIPLINED"

        pnl = float(t.net_pnl) if t.net_pnl is not None else None
        minutes_after_prev = None
        if prev and prev.exit_time and t.entry_time:
            try:
                delta = t.entry_time - prev.exit_time
                minutes_after_prev = max(0, int(delta.total_seconds() // 60))
            except Exception:
                minutes_after_prev = None

        if prev is not None and prev.net_pnl is not None and float(prev.net_pnl) < 0:
            streak_loss += 1
        elif prev is not None and prev.net_pnl is not None and float(prev.net_pnl) >= 0:
            streak_loss = 0

        if streak_loss >= 2 and minutes_after_prev is not None and minutes_after_prev < 15:
            flags.append("Fast re-entry after loss streak")
            severity = "red"
            verdict = "BEHAVIORAL BREAK"

        if streak_loss >= 1 and minutes_after_prev is not None and minutes_after_prev < 5:
            flags.append("Impulsive re-entry (<5m after prior close)")
            severity = "red"
            verdict = "BEHAVIORAL BREAK"

        if prev is not None and prev.quantity and t.quantity:
            try:
                if float(t.quantity) > float(prev.quantity) * 1.4 and (
                    prev.net_pnl is not None and float(prev.net_pnl) < 0
                ):
                    flags.append("Size up after loss")
                    severity = "red"
                    verdict = "BEHAVIORAL BREAK"
            except Exception:
                pass

        if not flags and pnl is not None and pnl < 0:
            flags.append("Loss within normal process")
        if not flags and pnl is not None and pnl >= 0:
            flags.append("Win · process not flagged")

        by_id[t.id] = {
            "id": t.id,
            "symbol": t.symbol,
            "side": t.side,
            "quantity": float(t.quantity) if t.quantity is not None else None,
            "net_pnl": pnl,
            "entry_time": t.entry_time.isoformat() if t.entry_time else None,
            "exit_time": t.exit_time.isoformat() if t.exit_time else None,
            "status": t.status,
            "source": getattr(t, "source", None),
            "minutes_after_prev": minutes_after_prev,
            "loss_streak_before": streak_loss,
            "flags": flags,
            "verdict": verdict,
            "severity": severity,
            "before": {
                "risk": "elevated" if severity == "red" else "normal",
                "frequency": "fast" if minutes_after_prev is not None and minutes_after_prev < 10 else "normal",
                "tilt_hint": severity,
            },
        }
        prev = t

    return [by_id[t.id] for t in trades if t.id in by_id]
