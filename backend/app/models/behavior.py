from sqlalchemy import String, DateTime, Numeric, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
import uuid

from app.core.database import Base


class BehavioralEvent(Base):
    __tablename__ = "behavioral_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="behavioral_events")


class EmotionalLog(Base):
    __tablename__ = "emotional_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("trades.id", ondelete="SET NULL"), nullable=True)
    anxiety: Mapped[Optional[int]] = mapped_column(nullable=True)
    confidence: Mapped[Optional[int]] = mapped_column(nullable=True)
    fear: Mapped[Optional[int]] = mapped_column(nullable=True)
    greed: Mapped[Optional[int]] = mapped_column(nullable=True)
    free_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(30), default="prompt")
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="emotional_logs")


class TradingPlan(Base):
    __tablename__ = "trading_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), default="Default Plan")
    max_trades_per_day: Mapped[Optional[int]] = mapped_column(nullable=True)
    max_risk_per_trade: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    max_daily_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    allowed_symbols: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    other_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="trading_plans")
