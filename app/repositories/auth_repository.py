from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_organization(self, organization_id: int) -> Organization | None:
        return self.db.query(Organization).filter(Organization.id == organization_id).first()

    def create_user(self, *, first_name: str, last_name: str, email: str, hashed_password: str, organization_id: int) -> User:
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

    def list_organizations(self) -> list[Organization]:
        return self.db.query(Organization).order_by(Organization.id.asc()).all()
