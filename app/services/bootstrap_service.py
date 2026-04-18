"""Seed reference data and organizations on startup or via scripts."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Organization
from app.repositories.data_repository import DataRepository


class BootstrapService:
    """Thin orchestration of DataRepository for initial DB population."""

    def __init__(self, repository: DataRepository):
        self.repository = repository

    def seed_reference_data(self, db: Session) -> None:
        """Fill incidents and fstec_threats from files when tables are empty."""
        self.repository.seed_domain_tables(db)

    def seed_organizations(self, db: Session) -> None:
        """Insert organizations for unique codes found in the incident dataset."""
        has_orgs = db.query(Organization).first() is not None
        if has_orgs:
            return

        incidents = self.repository.load_incidents(db=db)
        codes = sorted({str(code) for code in incidents["organization_code"].dropna().astype(str).tolist()})
        for code in codes:
            db.add(Organization(name=f"Organization {code}", code=code))
        db.commit()
