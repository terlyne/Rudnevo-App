from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.config import settings


async def get_user(
    db: AsyncSession,
    user_id: int
) -> User | None:
    """Получить пользователя по ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Получить пользователя по email"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Получить пользователя по username"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> list[User]:
    """Получить список пользователей"""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Создать пользователя"""
    db_obj = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password) if user_in.password else None,
        is_superuser=user_in.is_superuser,
        is_registered=user_in.is_registered
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_user(
    db: AsyncSession,
    user_id: int,
    update_data: Dict[str, Any]
) -> Optional[User]:
    """Обновить пользователя"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    
    # Обновляем поля пользователя
    for field, value in update_data.items():
        if field == "password":
            setattr(user, "hashed_password", get_password_hash(value))
        else:
            setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(
    db: AsyncSession,
    user_id: int
) -> bool:
    """Удалить пользователя"""
    db_user = await get_user(db, user_id)
    if not db_user:
        return False

    await db.delete(db_user)
    await db.commit()
    return True


async def set_user_registered(db: AsyncSession, user_id: int) -> User | None:
    """Подтвердить регистрацию пользователя"""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None
    
    db_user.is_registered = True
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> User | None:
    """Аутентифицировать пользователя"""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_password_reset_token(user: User, expires_delta: timedelta = None) -> str:
    """Создать токен для сброса пароля"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode = {
        "exp": expire,
        "sub": str(user.id),
        "type": "password_reset"
    }
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


async def verify_password_reset_token(
    db: AsyncSession,
    token: str
) -> User:
    """Проверить токен сброса пароля и вернуть пользователя"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "password_reset":
            raise ValueError("Неверный тип токена")
        user_id = int(payload.get("sub"))
    except (jwt.JWTError, ValueError):
        raise ValueError("Недействительный токен")
    
    user = await get_user(db, user_id)
    if not user:
        raise ValueError("Пользователь не найден")
    
    return user


async def verify_registration_token(
    db: AsyncSession,
    token: str
) -> User:
    """Проверить токен регистрации и вернуть пользователя"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "registration":
            raise ValueError("Неверный тип токена")
        user_id = int(payload.get("sub"))
    except (jwt.JWTError, ValueError):
        raise ValueError("Недействительный токен")
    
    user = await get_user(db, user_id)
    if not user:
        raise ValueError("Пользователь не найден")
    
    if user.is_registered:
        raise ValueError("Пользователь уже зарегистрирован")
    
    return user 