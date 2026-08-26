"""Parse IBKR Flex Query CSV into trade dicts."""
from __future__ import annotations
import csv
import io
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple


def _norm(h: str) -> str:
    return re.sub(r"[^a-z0-9]", "", h.strip().lower())


ALIASES = {
    "symbol": ["symbol"],
    "side": ["buysell", "side", "buy/sell"],
    "quantity": ["quantity", "qty", "shares"],
    "price": ["tradeprice", "price", "avgprice"],
    "datetime": ["datetime", "date/time", "tradedate", "date"],
    "commission": ["ibcommission", "commission"],
    "pnl": ["realizedpl", "realizedpnl", "pnl"],
    "exchid": ["exchid", "execid", "tradeid"],
}


def parse_flex_csv(content: str | bytes, account_id: str = "flex") -> Tuple[List[Dict[str, Any]], List[str]]:
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig", errors="replace")
    lines = content.splitlines()
    start = 0
    for i, line in enumerate(lines):
        lower = line.lower()
        if "symbol" in lower and ("quantity" in lower or "qty" in lower or "buy" in lower):
            start = i
            break
    reader = csv.reader(io.StringIO("\n".join(lines[start:])))
    try:
        headers = next(reader)
    except StopIteration:
        return [], ["Empty CSV"]

    nh = [_norm(h) for h in headers]
    trades = []
    warnings = []
    seen = set()

    def get(row, field):
        for a in ALIASES.get(field, []):
            for i, n in enumerate(nh):
                if a in n or n == a:
                    if i < len(row) and row[i].strip():
                        return row[i].strip()
        return None

    for idx, row in enumerate(reader, start=2):
        if not row or all(not c.strip() for c in row):
            continue
        symbol = get(row, "symbol")
        qty_s = get(row, "quantity")
        price_s = get(row, "price")
        if not symbol or not qty_s or not price_s:
            continue
        try:
            qty = abs(Decimal(qty_s.replace(",", "")))
            price = Decimal(price_s.replace(",", "").replace("$", ""))
        except (InvalidOperation, ValueError):
            warnings.append(f"Row {idx}: bad qty/price")
            continue
        side_raw = (get(row, "side") or "BUY").upper()
        side = "buy" if side_raw in ("BUY", "BOT", "B") else "sell"
        dt_s = get(row, "datetime") or ""
        try:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y%m%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"):
                try:
                    dt = datetime.strptime(dt_s, fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue
            else:
                dt = datetime.now(timezone.utc)
        except Exception:
            dt = datetime.now(timezone.utc)
        commission = Decimal("0")
        if get(row, "commission"):
            try:
                commission = Decimal(get(row, "commission").replace(",", ""))
            except Exception:
                pass
        pnl = None
        if get(row, "pnl"):
            try:
                pnl = Decimal(get(row, "pnl").replace(",", ""))
            except Exception:
                pass
        exec_id = get(row, "exchid") or f"flexrow{idx}_{symbol}_{dt.strftime('%Y%m%d%H%M%S')}"
        external_id = f"ibkr_{account_id}_{exec_id}"
        if external_id in seen:
            continue
        seen.add(external_id)
        net = (pnl + commission) if pnl is not None else pnl
        trades.append({
            "external_id": external_id,
            "position_id": None,
            "symbol": symbol.upper(),
            "side": side,
            "quantity": qty,
            "entry_price": price,
            "exit_price": price,
            "entry_time": dt,
            "exit_time": dt,
            "gross_pnl": pnl,
            "commission": commission,
            "swap": Decimal("0"),
            "net_pnl": net if net is not None else pnl,
            "stop_loss": None,
            "take_profit": None,
            "status": "closed",
            "source": "auto",
            "raw_data": {"row": idx},
        })
    if not trades:
        warnings.append("No trade rows found.")
    return trades, warnings
