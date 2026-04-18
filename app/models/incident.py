"""Normalized incident row for analytics and ML features."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Incident(Base):
    """Incident fact; organization_id and threat_code reference parent rows (FK)."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="RESTRICT"), index=True)
    organization_code: Mapped[str] = mapped_column(String(64), index=True)
    industry: Mapped[str] = mapped_column(String(128), index=True)
    host_count: Mapped[int] = mapped_column(Integer)
    threat_code: Mapped[int] = mapped_column(ForeignKey("fstec_threats.threat_code", ondelete="RESTRICT"), index=True)
    success: Mapped[int] = mapped_column(Integer)
    region: Mapped[str] = mapped_column(String(255), index=True)
    incident_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    regional_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hour: Mapped[int] = mapped_column(Integer, index=True)
    month: Mapped[int] = mapped_column(Integer)
    season: Mapped[str] = mapped_column(String(16), index=True)
    time_of_day: Mapped[str] = mapped_column(String(16), index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, index=True)

    organization = relationship("Organization", back_populates="incidents")
    threat = relationship("FstecThreat", back_populates="incidents")
