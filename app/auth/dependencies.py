from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_token
from app.db.session import get_db
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = decode_token(token)
        email = payload.get('sub')
        organization_id = payload.get('organization_id')
    except ValueError:
        raise credentials_exception

    if email is None or organization_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None or user.organization_id != organization_id:
        raise credentials_exception
    return user
