from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class IBKRFillPayload(BaseModel):
    account_id: str
    api_key: Optional[str] = None
    exec_id: str
    order_id: Optional[str] = None
    symbol: str
    side: str
    quantity: float
    price: float
    trade_time: str
    commission: float = 0.0
    realized_pnl: Optional[float] = None


class IBKRHistoryPayload(BaseModel):
    account_id: str
    api_key: Optional[str] = None
    fills: List[IBKRFillPayload] = []


class IBKRClosedTradePayload(BaseModel):
    account_id: str
    api_key: Optional[str] = None
    external_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    entry_time: str
    exit_time: str
    gross_pnl: Optional[float] = None
    commission: float = 0.0
    net_pnl: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None


def parse_ibkr_time(time_str: str) -> datetime:
    time_str = time_str.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d %H:%M:%S"):
        try:
            dt = datetime.strptime(time_str.replace("Z", ""), fmt.replace("Z", ""))
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def normalize_closed_trade(payload: IBKRClosedTradePayload) -> Dict[str, Any]:
    side = payload.side.lower()
    if side in ("buy", "long", "bot"):
        side = "buy"
    else:
        side = "sell"
    net = payload.net_pnl
    if net is None and payload.gross_pnl is not None:
        net = payload.gross_pnl + payload.commission
    return {
        "external_id": f"ibkr_{payload.account_id}_{payload.external_id}",
        "position_id": None,
        "symbol": payload.symbol.upper(),
        "side": side,
        "quantity": Decimal(str(payload.quantity)),
        "entry_price": Decimal(str(payload.entry_price)),
        "exit_price": Decimal(str(payload.exit_price)),
        "entry_time": parse_ibkr_time(payload.entry_time),
        "exit_time": parse_ibkr_time(payload.exit_time),
        "gross_pnl": Decimal(str(payload.gross_pnl)) if payload.gross_pnl is not None else None,
        "commission": Decimal(str(payload.commission)),
        "swap": Decimal("0"),
        "net_pnl": Decimal(str(net)) if net is not None else None,
        "stop_loss": None,
        "take_profit": None,
        "status": "closed",
        "source": "auto",
        "raw_data": payload.model_dump(),
    }
