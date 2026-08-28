"""Generic closed-trade payloads for cTrader, TradingView, NinjaTrader, CSV."""
from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
import csv
import io


class GenericClosedTrade(BaseModel):
    api_key: Optional[str] = None
    symbol: str
    side: str
    quantity: float
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    net_pnl: Optional[float] = None
    commission: Optional[float] = 0
    external_id: Optional[str] = None
    source: str = "generic"


class TradingViewAlert(BaseModel):
    api_key: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = "buy"
    quantity: Optional[float] = 1
    price: Optional[float] = None
    pnl: Optional[float] = None
    time: Optional[str] = None
    orderid: Optional[str] = None
    strategy: Optional[str] = None


def normalize_generic(payload: GenericClosedTrade, source: str) -> Dict[str, Any]:
    entry = payload.entry_time or payload.exit_time or datetime.now(timezone.utc)
    exit_t = payload.exit_time or entry
    ext = payload.external_id or f"{source}-{payload.symbol}-{int(entry.timestamp())}-{payload.quantity}"
    return {
        "external_id": ext,
        "symbol": payload.symbol.upper().replace("!", ""),
        "side": payload.side.lower() if payload.side.lower() in ("buy", "sell") else "buy",
        "quantity": Decimal(str(payload.quantity)),
        "entry_price": Decimal(str(payload.entry_price)) if payload.entry_price is not None else None,
        "exit_price": Decimal(str(payload.exit_price)) if payload.exit_price is not None else None,
        "entry_time": entry,
        "exit_time": exit_t,
        "net_pnl": Decimal(str(payload.net_pnl)) if payload.net_pnl is not None else None,
        "commission": Decimal(str(payload.commission or 0)),
        "status": "closed",
        "source": source,
        "raw_data": payload.model_dump(mode="json"),
    }


def normalize_tradingview(payload: TradingViewAlert) -> Dict[str, Any]:
    sym = (payload.symbol or "UNKNOWN").upper()
    t = datetime.now(timezone.utc)
    if payload.time:
        try:
            t = datetime.fromisoformat(payload.time.replace("Z", "+00:00"))
        except Exception:
            pass
    side = (payload.side or "buy").lower()
    if side not in ("buy", "sell"):
        side = "buy"
    qty = payload.quantity or 1
    ext = payload.orderid or f"tv-{sym}-{int(t.timestamp())}"
    return {
        "external_id": str(ext),
        "symbol": sym,
        "side": side,
        "quantity": Decimal(str(qty)),
        "entry_price": Decimal(str(payload.price)) if payload.price is not None else None,
        "exit_price": Decimal(str(payload.price)) if payload.price is not None else None,
        "entry_time": t,
        "exit_time": t,
        "net_pnl": Decimal(str(payload.pnl)) if payload.pnl is not None else None,
        "commission": Decimal("0"),
        "status": "closed",
        "source": "tradingview",
        "raw_data": payload.model_dump(mode="json"),
    }


def parse_generic_csv(raw: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], ["Empty CSV"]
    fields = {f.lower().strip(): f for f in reader.fieldnames}

    def col(*names):
        for n in names:
            if n in fields:
                return fields[n]
        return None

    c_sym = col("symbol", "ticker", "instrument")
    c_side = col("side", "direction", "bs")
    c_qty = col("quantity", "qty", "size", "lots")
    c_entry = col("entry_price", "entry", "open")
    c_exit = col("exit_price", "exit", "close")
    c_et = col("entry_time", "opentime", "open_time")
    c_xt = col("exit_time", "closetime", "close_time", "time")
    c_pnl = col("net_pnl", "pnl", "profit")
    c_comm = col("commission", "fees")
    c_ext = col("external_id", "id", "trade_id")
    if not c_sym:
        return [], ["CSV must include a symbol column"]

    out: List[Dict[str, Any]] = []
    for i, row in enumerate(reader):
        try:
            sym = (row.get(c_sym) or "").strip().upper()
            if not sym:
                continue
            side_raw = (row.get(c_side) or "buy").strip().lower()
            side = "sell" if side_raw in ("sell", "short", "s") else "buy"
            qty = Decimal(str(row.get(c_qty) or "1").replace(",", ""))

            def parse_dt(v):
                if not v:
                    return datetime.now(timezone.utc)
                v = v.strip()
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                    try:
                        return datetime.strptime(v[:19], fmt).replace(tzinfo=timezone.utc)
                    except Exception:
                        continue
                try:
                    return datetime.fromisoformat(v.replace("Z", "+00:00"))
                except Exception:
                    return datetime.now(timezone.utc)

            entry_t = parse_dt(row.get(c_et) if c_et else None)
            exit_t = parse_dt(row.get(c_xt) if c_xt else None)
            pnl = row.get(c_pnl) if c_pnl else None
            ext = (row.get(c_ext) if c_ext else None) or f"csv-{sym}-{i}-{int(exit_t.timestamp())}"
            out.append({
                "external_id": str(ext),
                "symbol": sym,
                "side": side,
                "quantity": qty,
                "entry_price": Decimal(str(row[c_entry])) if c_entry and row.get(c_entry) else None,
                "exit_price": Decimal(str(row[c_exit])) if c_exit and row.get(c_exit) else None,
                "entry_time": entry_t,
                "exit_time": exit_t,
                "net_pnl": Decimal(str(pnl)) if pnl not in (None, "") else None,
                "commission": Decimal(str(row[c_comm])) if c_comm and row.get(c_comm) else Decimal("0"),
                "status": "closed",
                "source": "csv",
                "raw_data": dict(row),
            })
        except Exception as e:
            warnings.append(f"Row {i+1}: {e}")
    return out, warnings
