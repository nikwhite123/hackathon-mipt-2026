from __future__ import annotations

from fastapi import HTTPException, status

from app.auth.security import create_access_token, get_password_hash, verify_password
from app.repositories.auth_repository import AuthRepository
from app.schemas import LoginRequest, TokenResponse, UserLoginResponse, UserRegisterRequest, UserResponse


class AuthService:
    def __init__(self, repository: AuthRepository):
        self.repository = repository

    def register(self, payload: UserRegisterRequest) -> UserResponse:
        if self.repository.get_user_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User with this email already exists')

        organization = self.repository.get_organization(payload.organization_id)
        if organization is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found')

        user = self.repository.create_user(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            organization_id=payload.organization_id,
        )
        return UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            organization_id=user.organization_id,
            organization_name=organization.name,
        )

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.repository.get_user_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password')

        access_token = create_access_token(subject=user.email, organization_id=user.organization_id)
        return TokenResponse(access_token=access_token)

    def build_login_response(self, payload: LoginRequest) -> UserLoginResponse:
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
            ),
        )
