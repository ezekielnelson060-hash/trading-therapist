from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from app.core.database import Base


class BrokerConnection(Base):
    __tablename__ = "broker_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    broker: Mapped[str] = mapped_column(String(50), nullable=False)
    account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    account_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    credentials: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_from_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="broker_connections")
    trades: Mapped[list["Trade"]] = relationship("Trade", back_populates="connection", cascade="all, delete-orphan")
