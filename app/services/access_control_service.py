from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.schemas import PredictRequest


class AccessControlService:
    def ensure_prediction_access(self, payload: PredictRequest, current_user: User, db: Session) -> str:
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
