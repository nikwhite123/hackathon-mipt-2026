"""FSTEC threat registry row."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FstecThreat(Base):
    """Threat reference keyed by threat_code for joins with incidents."""

    __tablename__ = "fstec_threats"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    threat_code: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    source_characteristics: Mapped[str | None] = mapped_column(Text, nullable=True)
    object_of_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidentiality_breach: Mapped[int] = mapped_column(Integer, default=0)
    integrity_breach: Mapped[int] = mapped_column(Integer, default=0)
    availability_breach: Mapped[int] = mapped_column(Integer, default=0)
    date_added: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_modified: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    incidents = relationship("Incident", back_populates="threat")
