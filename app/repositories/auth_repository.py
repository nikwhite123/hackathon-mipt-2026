"""User and organization persistence within a single SQLAlchemy session."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User


class AuthRepository:
    """CRUD for User and Organization lookups."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        """Find user by email (case-insensitive)."""
        normalized = email.strip().lower()
        return self.db.query(User).filter(func.lower(User.email) == normalized).first()

    def get_organization(self, organization_id: int) -> Organization | None:
        """Organization by numeric primary key."""
        return self.db.query(Organization).filter(Organization.id == organization_id).first()

    def get_organization_by_code(self, code: str) -> Organization | None:
        """Organization by unique string enterprise code."""
        normalized = code.strip()
        if not normalized:
            return None
        return self.db.query(Organization).filter(Organization.code == normalized).first()

    def create_user(self, *, first_name: str, last_name: str, email: str, hashed_password: str, organization_id: int) -> User:
        """Create a user and commit the transaction."""
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=hashed_password,
            organization_id=organization_id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
