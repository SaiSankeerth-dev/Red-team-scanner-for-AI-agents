"""Campaign storage models. Every attempt is persisted: reproducibility is a feature."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    target: Mapped[str] = mapped_column(String(200))
    pack: Mapped[str] = mapped_column(String(100), default="basics")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    attempts: Mapped[list["AttemptRecord"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class AttemptRecord(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    probe_name: Mapped[str] = mapped_column(String(100))
    messages: Mapped[list] = mapped_column(JSON)
    response: Mapped[str] = mapped_column(Text, default="")
    verdict: Mapped[str] = mapped_column(String(20), default="pending")
    notes: Mapped[str] = mapped_column(Text, default="")

    campaign: Mapped[Campaign] = relationship(back_populates="attempts")
