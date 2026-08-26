from sqlalchemy import String, DateTime, Numeric, Text, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
import uuid

from app.core.database import Base


class Trade(Base):
    """Normalized trade record. Source of truth for behavioral analytics."""
    __tablename__ = "trades"
    __table_args__ = (
        UniqueConstraint("user_id", "connection_id", "external_id", name="uq_trade_external"),
        Index("idx_trades_user_entry_time", "user_id", "entry_time"),
        Index("idx_trades_user_symbol", "user_id", "symbol"),
        Index("idx_trades_user_exit_time", "user_id", "exit_time"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("broker_connections.id", ondelete="SET NULL"), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    entry_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    exit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    gross_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    commission: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    swap: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    net_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    stop_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    take_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    risk_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="closed")
    source: Mapped[str] = mapped_column(String(20), default="auto")
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="trades")
    connection: Mapped[Optional["BrokerConnection"]] = relationship("BrokerConnection", back_populates="trades")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("broker_connections.id", ondelete="SET NULL"), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    unrealized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
