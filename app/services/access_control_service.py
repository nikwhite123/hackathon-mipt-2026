"""Ensure prediction requests target the authenticated user's organization."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.schemas import PredictRequest


class AccessControlService:
    """Compare request organization_id with the user's organization code in the DB."""

    def ensure_prediction_access(self, payload: PredictRequest, current_user: User, db: Session) -> str:
        """Return the canonical organization code or raise HTTP 403."""
        organization = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
        if organization is None or not organization.code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User organization is not configured",
            )

        requested_code = str(payload.organization_id)
        if requested_code != str(organization.code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to another organization is forbidden",
            )

        return str(organization.code)
