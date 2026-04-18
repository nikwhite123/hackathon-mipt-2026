"""Registration and login business logic (JWT, organization lookup by code)."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.auth.security import create_access_token, get_password_hash, verify_password
from app.repositories.auth_repository import AuthRepository
from app.schemas import LoginRequest, TokenResponse, UserLoginResponse, UserRegisterRequest, UserResponse


class AuthService:
    """Coordinates AuthRepository with security helpers (hashing, tokens)."""

    def __init__(self, repository: AuthRepository):
        self.repository = repository

    def register(self, payload: UserRegisterRequest) -> UserResponse:
        """Register against an organization code; email is normalized in the schema."""
        if self.repository.get_user_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User with this email already exists')

        organization = self.repository.get_organization_by_code(payload.organization_code)
        if organization is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found')

        user = self.repository.create_user(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email),
            hashed_password=get_password_hash(payload.password),
            organization_id=organization.id,
        )
        return UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            organization_id=user.organization_id,
            organization_name=organization.name,
            organization_code=organization.code if organization else None,
        )

    def login(self, payload: LoginRequest) -> TokenResponse:
        """Return only access_token (OAuth2-style /auth/token)."""
        user = self.repository.get_user_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password')

        access_token = create_access_token(subject=user.email, organization_id=user.organization_id)
        return TokenResponse(access_token=access_token)

    def build_login_response(self, payload: LoginRequest) -> UserLoginResponse:
        """Access token plus user profile for POST /auth/login."""
        token = self.login(payload)
        user = self.repository.get_user_by_email(payload.email)
        assert user is not None
        organization = self.repository.get_organization(user.organization_id)
        return UserLoginResponse(
            access_token=token.access_token,
            token_type=token.token_type,
            user=UserResponse(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                organization_id=user.organization_id,
                organization_name=organization.name if organization else '',
                organization_code=organization.code if organization else None,
            ),
        )
