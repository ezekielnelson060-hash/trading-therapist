from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timezone
import logging

from app.core.database import get_db
from app.core.security import resolve_connection_by_token, get_current_user, generate_connection_token, hash_token
from app.models import Trade, BrokerConnection, User
from app.connectors.mt5 import MT5DealPayload, normalize_deal
from app.connectors.ibkr import IBKRClosedTradePayload, normalize_closed_trade
from app.connectors.ibkr_flex import parse_flex_csv
from app.services.behavioral import analyze_new_trade

router = APIRouter()
logger = logging.getLogger(__name__)


async def upsert_trade(db, user_id, connection_id, trade_data):
    external_id = trade_data.get("external_id")
    if external_id:
        result = await db.execute(
            select(Trade).where(
                Trade.user_id == user_id,
                Trade.external_id == external_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing, False

    trade = Trade(user_id=user_id, connection_id=connection_id, **{
        k: v for k, v in trade_data.items()
        if k in {
            "external_id", "position_id", "symbol", "side", "quantity",
            "entry_price", "exit_price", "entry_time", "exit_time",
            "gross_pnl", "commission", "swap", "net_pnl",
            "stop_loss", "take_profit", "status", "source", "raw_data",
        }
    })
    db.add(trade)
    await db.flush()
    return trade, True


@router.post("/mt5/webhook")
async def mt5_webhook(
    payload: MT5DealPayload,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    api_key = x_api_key or getattr(payload, "api_key", None)
    if not api_key:
        raise HTTPException(401, "Missing API key")
    conn = await resolve_connection_by_token(api_key, db)
    if not conn:
        raise HTTPException(401, "Invalid API key")

    trade_data = normalize_deal(payload)
    trade, created = await upsert_trade(db, conn.user_id, conn.id, trade_data)
    conn.last_synced_at = datetime.now(timezone.utc)
    conn.status = "active"
    await db.flush()

    events = []
    if created:
        events = await analyze_new_trade(db, conn.user_id, trade)

    return {
        "status": "ok",
        "created": created,
        "trade_id": trade.id,
        "behavioral_events": [{"type": e.event_type, "title": e.title} for e in events],
    }


@router.post("/ibkr/webhook")
async def ibkr_webhook(
    payload: IBKRClosedTradePayload,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    api_key = x_api_key or payload.api_key
    if not api_key:
        raise HTTPException(401, "Missing API key")
    conn = await resolve_connection_by_token(api_key, db)
    if not conn:
        raise HTTPException(401, "Invalid API key")

    trade_data = normalize_closed_trade(payload)
    trade, created = await upsert_trade(db, conn.user_id, conn.id, trade_data)
    conn.last_synced_at = datetime.now(timezone.utc)
    await db.flush()

    events = []
    if created:
        events = await analyze_new_trade(db, conn.user_id, trade)

    return {
        "status": "ok",
        "created": created,
        "trade_id": trade.id,
        "behavioral_events": [{"type": e.event_type, "title": e.title} for e in events],
    }


@router.post("/ibkr/flex-upload")
async def ibkr_flex_upload(
    file: UploadFile = File(...),
    account_id: str = Form("flex"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw = await file.read()
    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 15MB)")

    trade_dicts, warnings = parse_flex_csv(raw, account_id=account_id)

    result = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.user_id == current_user.id,
            BrokerConnection.broker == "ibkr",
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raw_token = generate_connection_token()
        conn = BrokerConnection(
            user_id=current_user.id,
            broker="ibkr",
            account_id=account_id,
            account_name=f"IBKR Flex {account_id}",
            credentials={"token_hash": hash_token(raw_token)},
            status="active",
        )
        db.add(conn)
        await db.flush()

    created_count = 0
    for trade_data in trade_dicts:
        trade, created = await upsert_trade(db, current_user.id, conn.id, trade_data)
        if created:
            created_count += 1
            await analyze_new_trade(db, current_user.id, trade)

    conn.last_synced_at = datetime.now(timezone.utc)
    await db.flush()

    return {
        "status": "ok",
        "filename": file.filename,
        "parsed": len(trade_dicts),
        "created": created_count,
        "warnings": warnings[:20],
        "connection_id": conn.id,
    }


@router.post("/ctrader/webhook")
async def ctrader_webhook(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    from app.connectors.generic import GenericClosedTrade, normalize_generic

    api_key = x_api_key or payload.get("api_key")
    if not api_key:
        raise HTTPException(401, "Missing API key")
    conn = await resolve_connection_by_token(api_key, db)
    if not conn:
        raise HTTPException(401, "Invalid API key")
    try:
        body = GenericClosedTrade(**{**payload, "source": "ctrader"})
    except Exception as e:
        raise HTTPException(400, f"Invalid payload: {e}")
    trade_data = normalize_generic(body, "ctrader")
    trade, created = await upsert_trade(db, conn.user_id, conn.id, trade_data)
    conn.last_synced_at = datetime.now(timezone.utc)
    conn.status = "active"
    await db.flush()
    events = []
    if created:
        events = await analyze_new_trade(db, conn.user_id, trade)
    return {
        "status": "ok",
        "created": created,
        "trade_id": trade.id,
        "behavioral_events": [{"type": e.event_type, "title": e.title} for e in events],
    }


@router.post("/tradingview/webhook")
async def tradingview_webhook(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    from app.connectors.generic import TradingViewAlert, normalize_tradingview

    api_key = x_api_key or payload.get("api_key")
    if not api_key:
        raise HTTPException(401, "Missing API key")
    conn = await resolve_connection_by_token(api_key, db)
    if not conn:
        raise HTTPException(401, "Invalid API key")
    body = TradingViewAlert(**payload)
    trade_data = normalize_tradingview(body)
    trade, created = await upsert_trade(db, conn.user_id, conn.id, trade_data)
    conn.last_synced_at = datetime.now(timezone.utc)
    await db.flush()
    events = []
    if created:
        events = await analyze_new_trade(db, conn.user_id, trade)
    return {"status": "ok", "created": created, "trade_id": trade.id, "behavioral_events": len(events)}


@router.post("/ninjatrader/webhook")
async def ninjatrader_webhook(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    from app.connectors.generic import GenericClosedTrade, normalize_generic

    api_key = x_api_key or payload.get("api_key")
    if not api_key:
        raise HTTPException(401, "Missing API key")
    conn = await resolve_connection_by_token(api_key, db)
    if not conn:
        raise HTTPException(401, "Invalid API key")
    body = GenericClosedTrade(**{**payload, "source": "ninjatrader"})
    trade_data = normalize_generic(body, "ninjatrader")
    trade, created = await upsert_trade(db, conn.user_id, conn.id, trade_data)
    conn.last_synced_at = datetime.now(timezone.utc)
    await db.flush()
    events = []
    if created:
        events = await analyze_new_trade(db, conn.user_id, trade)
    return {"status": "ok", "created": created, "trade_id": trade.id}


@router.post("/csv/upload")
async def generic_csv_upload(
    file: UploadFile = File(...),
    broker_label: str = Form("csv"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.connectors.generic import parse_generic_csv

    raw = await file.read()
    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 15MB)")
    trade_dicts, warnings = parse_generic_csv(raw)

    result = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.user_id == current_user.id,
            BrokerConnection.broker == broker_label[:40],
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raw_token = generate_connection_token()
        conn = BrokerConnection(
            user_id=current_user.id,
            broker=broker_label[:40] or "csv",
            account_id="csv",
            account_name=f"{broker_label} CSV",
            credentials={"token_hash": hash_token(raw_token)},
            status="active",
        )
        db.add(conn)
        await db.flush()

    created_count = 0
    for trade_data in trade_dicts:
        trade, created = await upsert_trade(db, current_user.id, conn.id, trade_data)
        if created:
            created_count += 1
            await analyze_new_trade(db, current_user.id, trade)
    conn.last_synced_at = datetime.now(timezone.utc)
    await db.flush()
    return {
        "status": "ok",
        "filename": file.filename,
        "parsed": len(trade_dicts),
        "created": created_count,
        "warnings": warnings[:20],
    }


@router.get("/supported")
async def list_supported_brokers():
    return {
        "brokers": [
            {"id": "mt5", "name": "MetaTrader 5", "method": "webhook", "status": "live"},
            {"id": "ibkr", "name": "Interactive Brokers", "method": "flex_csv + webhook", "status": "live"},
            {"id": "ctrader", "name": "cTrader", "method": "webhook", "status": "live"},
            {"id": "tradingview", "name": "TradingView", "method": "webhook", "status": "live"},
            {"id": "ninjatrader", "name": "NinjaTrader", "method": "webhook", "status": "live"},
            {"id": "csv", "name": "Generic CSV", "method": "upload", "status": "live"},
        ],
        "note": "All feeds normalize into the same behavioral engine.",
    }
