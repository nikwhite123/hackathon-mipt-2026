"""Organization infrastructure parameters for UI and prediction input."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrganizationSettings(Base):
    """technologies is stored as JSON text."""

    __tablename__ = "organization_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), unique=True, index=True)
    region: Mapped[str] = mapped_column(String(64))
    industry: Mapped[str] = mapped_column(String(64))
    host_count: Mapped[int] = mapped_column(Integer)
    technologies: Mapped[str] = mapped_column(Text, default="[]")

    organization = relationship("Organization", back_populates="settings")
