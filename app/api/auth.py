from __future__ import annotations

from fastapi import APIRouter, Depends
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
    return AuthService(AuthRepository(db))


@router.post('/register', response_model=UserResponse, summary='Регистрация пользователя')
def register(payload: UserRegisterRequest, service: AuthService = Depends(get_auth_service)):
    return service.register(payload)


@router.post('/login', response_model=UserLoginResponse, summary='Логин пользователя и получение JWT')
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)):
    return service.build_login_response(payload)




@router.post('/token', response_model=TokenResponse, summary='OAuth2 token endpoint for Swagger Authorize')
def issue_token(form_data: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends(get_auth_service)):
    payload = LoginRequest(email=form_data.username, password=form_data.password)
    return service.login(payload)


@router.get('/me', response_model=UserResponse, summary='Текущий пользователь')
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    organization = AuthRepository(db).get_organization(current_user.organization_id)
    return UserResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        organization_id=current_user.organization_id,
        organization_name=organization.name if organization else '',
    )


@router.get('/organizations', response_model=list[OrganizationResponse], summary='Список организаций')
def list_organizations(db: Session = Depends(get_db)):
    organizations = AuthRepository(db).list_organizations()
    return [OrganizationResponse.model_validate(org) for org in organizations]
