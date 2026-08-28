from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, generate_connection_token, hash_token
from app.models import User, BrokerConnection

router = APIRouter()


class BrokerConnectRequest(BaseModel):
    broker: str
    account_id: Optional[str] = None
    account_name: Optional[str] = None


class BrokerConnectionOut(BaseModel):
    id: str
    broker: str
    account_id: Optional[str]
    account_name: Optional[str]
    status: str
    api_token: Optional[str] = None
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.post("/connect", response_model=BrokerConnectionOut)
async def connect_broker(
    body: BrokerConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    supported = {
        "mt5", "ibkr", "ctrader", "tradingview", "ninjatrader",
        "csv", "generic", "binance", "bybit",
    }
    if body.broker.lower() not in supported:
        raise HTTPException(400, f"Unsupported broker. Supported: {sorted(supported)}")

    raw_token = generate_connection_token()
    token_hash = hash_token(raw_token)

    conn = BrokerConnection(
        user_id=current_user.id,
        broker=body.broker.lower(),
        account_id=body.account_id,
        account_name=body.account_name or f"{body.broker} account",
        credentials={"token_hash": token_hash},
        status="active",
    )
    db.add(conn)
    await db.flush()
    await db.refresh(conn)
    return BrokerConnectionOut(
        id=conn.id,
        broker=conn.broker,
        account_id=conn.account_id,
        account_name=conn.account_name,
        status=conn.status,
        api_token=raw_token,
        last_synced_at=conn.last_synced_at,
    )


@router.get("/", response_model=List[BrokerConnectionOut])
async def list_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BrokerConnection).where(BrokerConnection.user_id == current_user.id)
    )
    return [
        BrokerConnectionOut(
            id=c.id,
            broker=c.broker,
            account_id=c.account_id,
            account_name=c.account_name,
            status=c.status,
            last_synced_at=c.last_synced_at,
        )
        for c in result.scalars().all()
    ]


@router.post("/{connection_id}/rotate-token", response_model=BrokerConnectionOut)
async def rotate_token(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.id == connection_id,
            BrokerConnection.user_id == current_user.id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(404, "Connection not found")
    raw_token = generate_connection_token()
    conn.credentials = {**(conn.credentials or {}), "token_hash": hash_token(raw_token)}
    await db.flush()
    return BrokerConnectionOut(
        id=conn.id,
        broker=conn.broker,
        account_id=conn.account_id,
        account_name=conn.account_name,
        status=conn.status,
        api_token=raw_token,
        last_synced_at=conn.last_synced_at,
    )


@router.post("/{connection_id}/sync")
async def trigger_sync(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.id == connection_id,
            BrokerConnection.user_id == current_user.id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(404, "Connection not found")
    return {
        "message": f"Sync triggered for {conn.broker}",
        "connection_id": connection_id,
        "status": "queued",
    }
