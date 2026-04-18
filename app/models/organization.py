"""Tenant organization: display name and external company code for data isolation."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    """Organization directory; incidents.organization_id references id; code kept denormalized on incidents."""

    __tablename__ = 'organizations'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    code: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)

    users = relationship('User', back_populates='organization')
    settings = relationship('OrganizationSettings', back_populates='organization', uselist=False)
    incidents = relationship('Incident', back_populates='organization')
