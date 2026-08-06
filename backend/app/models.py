from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default="customer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    # Manual admin-set status for now -- no ID-verification vendor wired up yet. See
    # LAUNCH_CHECKLIST.md: real KYC/AML requires an actual licensed provider and legal review.
    kyc_status: Mapped[str] = mapped_column(String(20), default="not_started")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    swaps: Mapped[list["Swap"]] = relationship(back_populates="user")
    balances: Mapped[list["Balance"]] = relationship(back_populates="user")


class AccountToken(Base):
    __tablename__ = "account_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(32))
    token_hash: Mapped[str] = mapped_column(String(64), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Balance(Base):
    __tablename__ = "balances"
    __table_args__ = (UniqueConstraint("user_id", "asset", name="uq_balance_user_asset"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    asset: Mapped[str] = mapped_column(String(12))
    amount: Mapped[float] = mapped_column(Numeric(24, 8), default=0)
    user: Mapped[User] = relationship(back_populates="balances")


class Swap(Base):
    __tablename__ = "swaps"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    from_asset: Mapped[str] = mapped_column(String(12))
    to_asset: Mapped[str] = mapped_column(String(12))
    amount: Mapped[float] = mapped_column(Numeric(24, 8))
    amount_received: Mapped[float] = mapped_column(Numeric(24, 8))
    fee: Mapped[float] = mapped_column(Numeric(24, 8))
    status: Mapped[str] = mapped_column(String(24), default="pending")
    provider_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user: Mapped[User] = relationship(back_populates="swaps")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(80))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
