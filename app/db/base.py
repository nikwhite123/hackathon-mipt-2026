"""Declarative SQLAlchemy base for ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for SQLAlchemy 2 mapped classes."""
