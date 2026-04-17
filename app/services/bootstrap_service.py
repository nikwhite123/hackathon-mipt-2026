from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Organization
from app.repositories.data_repository import DataRepository


class BootstrapService:
    def __init__(self, repository: DataRepository):
        self.repository = repository

    def seed_organizations(self, db: Session) -> None:
        has_orgs = db.query(Organization).first() is not None
        if has_orgs:
            return

        incidents = self.repository.load_incidents()
        codes = sorted({str(code) for code in incidents["organization_code"].dropna().astype(str).tolist()})
        for code in codes:
            db.add(Organization(name=f"Организация {code}", code=code))
        db.commit()
