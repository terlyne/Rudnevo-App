from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import TokenData, verify_token
from db.session import get_async_session
from models.user import User
from crud.user import get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)
) -> User:
    """Получить текущего пользователя"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token, "access")
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except ValueError as e:
        raise credentials_exception

    user = await get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)
) -> User | None:
    """Получить текущего пользователя (опционально, возвращает None если не авторизован)"""
    try:
        payload = verify_token(token, "access")
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except ValueError:
        return None

    user = await get_user_by_username(db, username=token_data.username)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Получить текущего активного пользователя"""
    if not current_user.is_registered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Неактивный пользователь."
        )
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_active_user)):
    """Получить текущего супер-администратора"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права супер-администратора."
        )
    return current_user


async def get_current_admin(current_user: User = Depends(get_current_active_user)):
    """Получить текущего администратора (супер-админ или обычный админ)"""
    if current_user.is_superuser:
        return current_user
    if not current_user.is_recruiter:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Требуются права администратора."
    )


async def get_current_recruiter(current_user: User = Depends(get_current_active_user)):
    """Получить текущего рекрутера"""
    if current_user.is_recruiter:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Требуются права работодателя."
    )


async def get_current_admin_or_superuser(current_user: User = Depends(get_current_active_user)):
    """Получить текущего администратора или супер-администратора"""
    # Супер-администраторы всегда имеют доступ
    if current_user.is_superuser:
        return current_user
    # Обычные администраторы (не рекрутеры) имеют доступ
    if not current_user.is_recruiter:
        return current_user
    # Рекрутеры не имеют доступа
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Требуются права администратора или супер-администратора."
    )


async def get_current_vacancy_user(current_user: User = Depends(get_current_active_user)):
    """Получить текущего пользователя для работы с вакансиями (включает работодателей)"""
    # Супер-администраторы всегда имеют доступ
    if current_user.is_superuser:
        return current_user
    # Обычные администраторы имеют доступ
    if not current_user.is_recruiter:
        return current_user
    # Работодатели имеют доступ к вакансиям
    if current_user.is_recruiter:
        return current_user
    # Остальные пользователи не имеют доступа
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Требуются права администратора, супер-администратора или работодателя."
    )
