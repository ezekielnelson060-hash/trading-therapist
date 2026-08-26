from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class MT5DealPayload(BaseModel):
    api_key: Optional[str] = None
    ticket: str
    symbol: str
    side: str
    volume: float
    price: float
    profit: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    time: str
    entry: str = "out"
    position_id: Optional[str] = None
    comment: Optional[str] = None


class MT5HistoryPayload(BaseModel):
    api_key: Optional[str] = None
    deals: list[MT5DealPayload] = []


def parse_mt5_time(time_str: str) -> datetime:
    time_str = time_str.strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(time_str.replace("Z", ""), fmt.replace("Z", ""))
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def normalize_deal(payload: MT5DealPayload) -> Dict[str, Any]:
    side = payload.side.lower()
    if side in ("buy", "0"):
        side = "buy"
    else:
        side = "sell"
    t = parse_mt5_time(payload.time)
    net = payload.profit + payload.commission + payload.swap
    return {
        "external_id": f"mt5_{payload.ticket}",
        "position_id": payload.position_id,
        "symbol": payload.symbol.upper(),
        "side": side,
        "quantity": Decimal(str(payload.volume)),
        "entry_price": Decimal(str(payload.price)),
        "exit_price": Decimal(str(payload.price)),
        "entry_time": t,
        "exit_time": t,
        "gross_pnl": Decimal(str(payload.profit)),
        "commission": Decimal(str(payload.commission)),
        "swap": Decimal(str(payload.swap)),
        "net_pnl": Decimal(str(net)),
        "stop_loss": None,
        "take_profit": None,
        "status": "closed",
        "source": "auto",
        "raw_data": payload.model_dump(),
    }
