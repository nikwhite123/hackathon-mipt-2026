"""CRUD for organization settings (region, industry, hosts, technologies) stored as JSON."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models import OrganizationSettings, User
from app.schemas import OrganizationSettingsRequest, OrganizationSettingsResponse


class OrganizationSettingsService:
    """At most one organization_settings row per user's organization_id."""

    def upsert_for_user(self, payload: OrganizationSettingsRequest, current_user: User, db: Session) -> OrganizationSettingsResponse:
        """Create or update settings for the current user's organization."""
        settings = (
            db.query(OrganizationSettings)
            .filter(OrganizationSettings.organization_id == current_user.organization_id)
            .first()
        )

        if settings is None:
            settings = OrganizationSettings(organization_id=current_user.organization_id)
            db.add(settings)

        settings.region = payload.region
        settings.industry = payload.industry
        settings.host_count = payload.host_count
        settings.technologies = json.dumps(payload.technologies, ensure_ascii=False)

        db.commit()
        db.refresh(settings)
        return self._to_response(settings)

    def get_for_user(self, current_user: User, db: Session) -> OrganizationSettingsResponse | None:
        """Return None when the user has not saved settings yet."""
        settings = (
            db.query(OrganizationSettings)
            .filter(OrganizationSettings.organization_id == current_user.organization_id)
            .first()
        )
        return None if settings is None else self._to_response(settings)

    @staticmethod
    def _to_response(settings: OrganizationSettings) -> OrganizationSettingsResponse:
        """Parse technologies JSON string into a list for the API response."""
        return OrganizationSettingsResponse(
            organization_id=settings.organization_id,
            region=settings.region,
            industry=settings.industry,
            host_count=settings.host_count,
            technologies=json.loads(settings.technologies or "[]"),
        )
