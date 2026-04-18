"""Auth routes: register, login, OAuth2 token, current user, organization lookup by code."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.auth_repository import AuthRepository
from app.schemas import LoginRequest, OrganizationResponse, TokenResponse, UserLoginResponse, UserRegisterRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix='/auth', tags=['auth'])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Build AuthService bound to the request-scoped database session."""
    return AuthService(AuthRepository(db))


@router.post('/register', response_model=UserResponse, summary='Register user')
def register(payload: UserRegisterRequest, service: AuthService = Depends(get_auth_service)):
    """Register a user against an existing organization code."""
    return service.register(payload)


@router.post('/login', response_model=UserLoginResponse, summary='Login and receive JWT')
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)):
    """Login and return JWT plus user profile (non-OAuth2 clients)."""
    return service.build_login_response(payload)




@router.post('/token', response_model=TokenResponse, summary='OAuth2 token endpoint for Swagger Authorize')
def issue_token(form_data: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends(get_auth_service)):
    """OAuth2 password flow: username is the email; returns bearer token only."""
    payload = LoginRequest(email=form_data.username, password=form_data.password)
    return service.login(payload)


@router.get('/me', response_model=UserResponse, summary='Current user')
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return the authenticated user and organization summary."""
    organization = AuthRepository(db).get_organization(current_user.organization_id)
    return UserResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        organization_id=current_user.organization_id,
        organization_name=organization.name if organization else '',
        organization_code=organization.code if organization else None,
    )


@router.get(
    '/organization/by-code',
    response_model=OrganizationResponse,
    summary='Resolve organization by code (registration only; no org list)',
)
def organization_by_code(code: str = Query(..., min_length=1, max_length=64), db: Session = Depends(get_db)):
    """Resolve a public organization code for registration flows (no org listing)."""
    organization = AuthRepository(db).get_organization_by_code(code)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found')
    if hasattr(OrganizationResponse, 'model_validate'):
        return OrganizationResponse.model_validate(organization)
    return OrganizationResponse.from_orm(organization)
