from datetime import datetime, timedelta
import jwt
from typing import Optional
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from users.crud import get_user_by_email_or_username
from users.models import User
from core.config import settings


# Для автоматического извлечения токена из заголовка Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def create_registration_token(email: str) -> str:
    """Создает токен для регистрации"""
    data = {
        "sub": email,
        "exp": datetime.now() + timedelta(days=settings.REGISTRATION_TOKEN_EXPIRE_DAYS)
    }
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def verify_registration_token(token: str) -> Optional[str]:
    """Проверяет токен регистрации и возвращает email"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None



def create_jwt_token(user: User) -> str:
    """Функция для создания JWT токена"""
    data = {
        "sub": user.username,  # subject - уникальный идентификатор пользователя
        "user_id": user.id,  # ID пользователя
        "email": user.email,  # Email пользователя
        "exp": datetime.now()
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload=data, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


async def get_user_from_token(token: str) -> User:
    """Функция для получения пользователя по токену"""
    try:
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        payload = jwt.decode(
            token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await get_user_by_email_or_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
