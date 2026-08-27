"""Tilt Engine — personal baseline + tilt score + interventions.
Core product: stop the behavior that is costing money.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Trade, BehavioralEvent, TradingPlan


def _pnl(t: Trade) -> float:
    if t.net_pnl is not None:
        return float(t.net_pnl)
    if t.gross_pnl is not None:
        return float(t.gross_pnl)
    return 0.0


def _qty(t: Trade) -> float:
    return float(t.quantity or 0)


async def _load_closed(db: AsyncSession, user_id: str, limit: int = 200) -> List[Trade]:
    result = await db.execute(
        select(Trade)
        .where(Trade.user_id == user_id, Trade.status == "closed")
        .order_by(Trade.entry_time.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def _load_plan(db: AsyncSession, user_id: str) -> Optional[TradingPlan]:
    result = await db.execute(
        select(TradingPlan)
        .where(TradingPlan.user_id == user_id, TradingPlan.active == True)  # noqa: E712
        .order_by(TradingPlan.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def compute_baseline(trades: List[Trade]) -> Dict[str, Any]:
    if len(trades) < 5:
        return {
            "ready": False,
            "message": "Need at least 5 closed trades to build your personal baseline.",
            "sample_size": len(trades),
        }
    ordered = sorted([t for t in trades if t.entry_time], key=lambda t: t.entry_time)
    split = max(5, len(ordered) * 2 // 3)
    base = ordered[:split]
    by_day: Dict[str, int] = {}
    for t in base:
        day = t.entry_time.date().isoformat()
        by_day[day] = by_day.get(day, 0) + 1
    tpd = list(by_day.values()) or [0]
    qtys = [_qty(t) for t in base if _qty(t) > 0]
    gaps: List[float] = []
    for i in range(1, len(ordered[:split])):
        a, b = ordered[i - 1], ordered[i]
        if a.entry_time and b.entry_time:
            gaps.append((b.entry_time - a.entry_time).total_seconds() / 60.0)
    gaps = [g for g in gaps if 0 < g < 24 * 60]
    symbols: Dict[str, int] = {}
    for t in base:
        if t.symbol:
            symbols[t.symbol] = symbols.get(t.symbol, 0) + 1
    top_symbols = sorted(symbols, key=symbols.get, reverse=True)[:5]
    hours = [t.entry_time.hour for t in base if t.entry_time]
    return {
        "ready": True,
        "sample_size": len(base),
        "trades_per_day_median": float(median(tpd)) if tpd else 0,
        "trades_per_day_p75": float(sorted(tpd)[int(len(tpd) * 0.75)]) if tpd else 0,
        "avg_quantity": sum(qtys) / len(qtys) if qtys else 0,
        "median_minutes_between_entries": float(median(gaps)) if gaps else None,
        "preferred_symbols": top_symbols,
        "typical_hours_utc": sorted(set(hours))[:12] if hours else [],
    }


def _today_trades(trades: List[Trade], now: datetime) -> List[Trade]:
    start = now.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    out = []
    for t in trades:
        ts = t.entry_time
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= start:
            out.append(t)
    return out


def compute_tilt(trades, baseline, plan, events):
    now = datetime.now(timezone.utc)
    today = _today_trades(trades, now)
    signals = {}
    score = 0.0

    streak = 0
    for t in trades:
        if _pnl(t) < 0:
            streak += 1
        else:
            break
    if streak >= 3:
        signals["consecutive_losses"] = {"status": "red", "label": "Consecutive losses", "detail": f"{streak} losses in a row"}
        score += min(25, streak * 8)
    elif streak == 2:
        signals["consecutive_losses"] = {"status": "amber", "label": "Consecutive losses", "detail": "2 losses in a row"}
        score += 10
    else:
        signals["consecutive_losses"] = {"status": "green", "label": "Consecutive losses", "detail": "OK"}

    max_day = None
    if plan and getattr(plan, "max_trades_per_day", None):
        max_day = plan.max_trades_per_day
    elif baseline.get("ready"):
        max_day = int(baseline.get("trades_per_day_p75") or 0) + 2

    if max_day and len(today) > max_day:
        signals["overtrading"] = {"status": "red", "label": "Overtrading", "detail": f"{len(today)} trades today vs limit/baseline ~{max_day}"}
        score += 20
    elif max_day and len(today) >= max(1, max_day - 1):
        signals["overtrading"] = {"status": "amber", "label": "Overtrading", "detail": f"{len(today)} trades today (approaching {max_day})"}
        score += 10
    else:
        signals["overtrading"] = {"status": "green", "label": "Overtrading", "detail": f"{len(today)} trades today"}

    risk_status, risk_detail = "green", "No size escalation detected"
    if len(trades) >= 2:
        last, prev = trades[0], trades[1]
        if _pnl(prev) < 0 and _qty(last) > 0 and _qty(prev) > 0:
            ratio = _qty(last) / _qty(prev)
            if ratio >= 1.5:
                risk_status, risk_detail = "red", f"Size {ratio:.1f}x after a loss"
                score += 20
            elif ratio >= 1.2:
                risk_status, risk_detail = "amber", f"Size {ratio:.1f}x after a loss"
                score += 10
    signals["risk_escalation"] = {"status": risk_status, "label": "Risk escalation", "detail": risk_detail}

    revenge, revenge_detail = "green", "No rapid re-entry after loss"
    if len(trades) >= 2:
        last, prev = trades[0], trades[1]
        if _pnl(prev) < 0 and last.entry_time and prev.exit_time:
            et, xt = last.entry_time, prev.exit_time
            if et.tzinfo is None:
                et = et.replace(tzinfo=timezone.utc)
            if xt.tzinfo is None:
                xt = xt.replace(tzinfo=timezone.utc)
            mins = (et - xt).total_seconds() / 60.0
            if 0 <= mins <= 15:
                revenge, revenge_detail = "red", f"Re-entered {mins:.0f} min after a loss"
                score += 22
            elif 0 <= mins <= 30:
                revenge, revenge_detail = "amber", f"Re-entered {mins:.0f} min after a loss"
                score += 12
    signals["revenge_trading"] = {"status": revenge, "label": "Revenge trading", "detail": revenge_detail}

    plan_status, plan_detail = "green", "No active plan constraints"
    if plan and getattr(plan, "allowed_symbols", None):
        allowed = {s.upper() for s in (plan.allowed_symbols or [])}
        if allowed and today:
            bad = [t for t in today if t.symbol and t.symbol.upper() not in allowed]
            if bad:
                plan_status, plan_detail = "red", f"{len(bad)} trade(s) outside allowed symbols"
                score += 15
            else:
                plan_detail = "Symbols within plan"
    signals["plan_adherence"] = {"status": plan_status, "label": "Plan adherence", "detail": plan_detail}

    pace_status, pace_detail = "green", "Pace normal or insufficient data"
    if baseline.get("ready") and baseline.get("median_minutes_between_entries") and len(today) >= 3:
        med = baseline["median_minutes_between_entries"]
        today_sorted = sorted([t for t in today if t.entry_time], key=lambda t: t.entry_time)
        gaps = []
        for i in range(1, len(today_sorted)):
            gaps.append((today_sorted[i].entry_time - today_sorted[i - 1].entry_time).total_seconds() / 60.0)
        if gaps:
            avg_gap = sum(gaps) / len(gaps)
            if med > 0 and avg_gap < med / 3:
                pace_status = "red"
                pace_detail = f"Entering ~{med / max(avg_gap, 0.1):.1f}x faster than your baseline"
                score += 15
            elif med > 0 and avg_gap < med / 2:
                pace_status, pace_detail = "amber", "Faster pace than your baseline"
                score += 8
            else:
                pace_detail = "Pace near your baseline"
    signals["pace"] = {"status": pace_status, "label": "Trade pace", "detail": pace_detail}

    score = max(0, min(100, int(round(score))))
    if score >= 70:
        state, state_label, color = "PAUSED_RECOMMENDED", "HIGH RISK", "red"
        recommendation = "Stop trading. Take at least 30-60 minutes away from the platform."
    elif score >= 40:
        state, state_label, color = "ELEVATED", "ELEVATED", "amber"
        recommendation = "Slow down. No new risk until you review your plan and last losses."
    else:
        state, state_label, color = "CONTROLLED", "CONTROLLED", "green"
        recommendation = "Behavior within your baseline. Stick to the plan."

    return {
        "tilt_score": score,
        "state": state,
        "state_label": state_label,
        "color": color,
        "recommendation": recommendation,
        "signals": signals,
        "today_trades": len(today),
        "do_not_trade": score >= 70,
    }


def daily_autopsy(trades, baseline, plan, tilt):
    now = datetime.now(timezone.utc)
    today = _today_trades(trades, now)
    pnl = sum(_pnl(t) for t in today)
    planned_max = plan.max_trades_per_day if plan and plan.max_trades_per_day else None
    adherence = None
    if planned_max and planned_max > 0:
        adherence = max(0, min(100, int(100 * (1 - max(0, len(today) - planned_max) / planned_max))))
    problems = []
    for sig in (tilt.get("signals") or {}).values():
        if sig.get("status") in ("red", "amber"):
            problems.append({"severity": sig["status"], "title": sig.get("label"), "detail": sig.get("detail")})
    unplanned_cost = None
    if planned_max and len(today) > planned_max:
        extra_sorted = sorted([t for t in today if t.entry_time], key=lambda t: t.entry_time)[planned_max:]
        unplanned_cost = sum(_pnl(t) for t in extra_sorted)
    return {
        "date": now.date().isoformat(),
        "pnl": round(pnl, 2),
        "trades": len(today),
        "planned_max": planned_max,
        "plan_adherence_pct": adherence,
        "problems": problems,
        "unplanned_trades_pnl_estimate": round(unplanned_cost, 2) if unplanned_cost is not None else None,
        "tomorrow_rule": (
            f"Maximum {planned_max} trades. After a loss >1R, wait 20 minutes before next entry."
            if planned_max
            else "Define max trades/day in your constitution. After a loss, wait 20 minutes."
        ),
        "tilt_score": tilt.get("tilt_score"),
        "recommendation": tilt.get("recommendation"),
    }


def cost_of_behavior(trades, events):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)
    event_trade_ids = set()
    for e in events:
        det = e.detected_at
        if det and det.tzinfo is None:
            det = det.replace(tzinfo=timezone.utc)
        if det and det < cutoff:
            continue
        if e.event_type in ("revenge_trading", "size_increase_after_loss", "overtrading"):
            for tid in (e.trade_ids or []):
                event_trade_ids.add(tid)
    leakage = sum(_pnl(t) for t in trades if t.id in event_trade_ids)
    return {
        "window_days": 30,
        "estimated_behavioral_leakage": round(leakage, 2),
        "note": "Estimate from trades linked to revenge/size-up/overtrading flags — not a guarantee of alternate P&L.",
        "flagged_trade_count": len(event_trade_ids),
    }


def weekly_report(trades, events, baseline):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    week = []
    for t in trades:
        ts = t.entry_time
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= week_ago:
            week.append(t)
    pnl = sum(_pnl(t) for t in week)

    def _in_week(e):
        det = e.detected_at
        if not det:
            return False
        if det.tzinfo is None:
            det = det.replace(tzinfo=timezone.utc)
        return det >= week_ago

    revenge = sum(1 for e in events if e.event_type == "revenge_trading" and _in_week(e))
    overtrade = sum(1 for e in events if e.event_type == "overtrading" and _in_week(e))
    biggest = "None flagged"
    if revenge:
        biggest = "Entering soon after a loss (revenge pattern)"
    elif overtrade:
        biggest = "Overtrading vs your plan/baseline"
    return {
        "window_days": 7,
        "trades": len(week),
        "pnl": round(pnl, 2),
        "revenge_flags": revenge,
        "overtrading_flags": overtrade,
        "headline": "P&L is not the headline — behavior is.",
        "biggest_behavioral_leak": biggest,
        "message": f"{len(week)} trades this week · revenge flags {revenge} · overtrading flags {overtrade}",
    }


async def full_behavioral_snapshot(db: AsyncSession, user_id: str) -> Dict[str, Any]:
    trades = await _load_closed(db, user_id)
    plan = await _load_plan(db, user_id)
    baseline = compute_baseline(trades)
    ev_result = await db.execute(
        select(BehavioralEvent)
        .where(BehavioralEvent.user_id == user_id)
        .order_by(BehavioralEvent.detected_at.desc())
        .limit(30)
    )
    events = list(ev_result.scalars().all())
    tilt = compute_tilt(trades, baseline, plan, events)
    autopsy = daily_autopsy(trades, baseline, plan, tilt)
    constitution = None
    if plan:
        rules = plan.other_rules or {}
        constitution = {
            "max_trades_per_day": plan.max_trades_per_day,
            "risk_per_trade_pct": float(plan.max_risk_per_trade) if plan.max_risk_per_trade is not None else None,
            "max_daily_loss": float(plan.max_daily_loss) if plan.max_daily_loss is not None else None,
            "allowed_symbols": plan.allowed_symbols or [],
            "name": getattr(plan, "name", None) or "Active plan",
            "cooldown_minutes_after_loss": rules.get("cooldown_minutes_after_loss"),
            "max_consecutive_losses_before_stop": rules.get("max_consecutive_losses_before_stop"),
            "no_risk_increase_after_loss": rules.get("no_risk_increase_after_loss", True),
        }
    return {
        "baseline": baseline,
        "tilt": tilt,
        "autopsy": autopsy,
        "constitution": constitution,
        "cost_of_behavior": cost_of_behavior(trades, events),
        "weekly": weekly_report(trades, events, baseline),
        "total_closed_trades": len(trades),
        "message": (
            "Behavioral risk view from your real trades — not what you intended to do."
            if trades
            else "Connect MT5/IBKR or import trades to build your baseline and tilt score."
        ),
    }
