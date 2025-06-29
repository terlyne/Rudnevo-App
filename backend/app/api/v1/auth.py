from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from app.crud import user as user_crud
from app.db.session import get_async_session
from app.schemas.token import Token, RefreshToken
from app.schemas.user import UserCreate, UserInDB, UserRegistration, UserInvite
from app.api.deps import get_current_superuser, get_current_active_user
from app.utils.email import send_registration_email

router = APIRouter()


@router.post("/register", response_model=Token)
async def register_user(
    registration: UserRegistration, db: AsyncSession = Depends(get_async_session)
) -> Any:
    """Регистрация администратора по токену из email"""
    try:
        # Проверяем токен и получаем пользователя
        user = await user_crud.verify_registration_token(db, registration.token)

        # Проверяем, что email совпадает с тем, что в токене
        if user.email != registration.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Адрес электронной почты не соответствует приглашению.",
            )

        # Проверяем, что username не занят
        existing_user = await user_crud.get_user_by_username(db, registration.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким именем уже зарегистрирован.",
            )

        # Обновляем пользователя
        user_update = {
            "username": registration.username,
            "password": registration.password,
            "is_registered": True,
        }
        user = await user_crud.update_user(db, user.id, user_update)

        # Создаем токены доступа
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = create_access_token(
            data={"sub": user.username, "email": user.email},
            expires_delta=access_token_expires,
        )
        refresh_token = create_refresh_token(
            data={"sub": user.username, "email": user.email},
            expires_delta=refresh_token_expires,
        )

        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_async_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """Аутентификация администратора"""
    user = await user_crud.get_user_by_username(db, form_data.username)
    if not user:
        user = await user_crud.get_user_by_email(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_registered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не зарегистрирован.",
        )

    # Создаем токены доступа
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": user.username, "email": user.email},
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "email": user.email},
        expires_delta=refresh_token_expires,
    )

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token_data: RefreshToken,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Обновление access токена с помощью refresh токена"""
    try:
        # Проверяем refresh токен
        payload = verify_token(refresh_token_data.refresh_token, "refresh")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный refresh токен.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Проверяем, что пользователь существует
        user = await user_crud.get_user_by_username(db, username=username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Создаем новые токены
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = create_access_token(
            data={"sub": user.username, "email": user.email},
            expires_delta=access_token_expires,
        )
        refresh_token = create_refresh_token(
            data={"sub": user.username, "email": user.email},
            expires_delta=refresh_token_expires,
        )

        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или истекший refresh токен.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/invite", response_model=UserInDB)
async def invite_user(
    user_in: UserInvite,
    db: AsyncSession = Depends(get_async_session),
    current_user: Any = Depends(get_current_superuser),
) -> Any:
    """Пригласить нового пользователя (только для супер-администратора)"""
    # Проверяем, что email не занят
    user = await user_crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует.",
        )

    # Создаем нового пользователя только с email
    new_user = UserCreate(
        email=user_in.email,
        is_superuser=False,  # Новый пользователь никогда не может быть суперпользователем
        is_registered=False,
        is_recruiter=user_in.is_recruiter,
    )
    user = await user_crud.create_user(db, new_user)

    # Создаем токен для регистрации
    token_expires = timedelta(hours=24)
    token = create_access_token(
        data={"sub": str(user.id), "type": "registration"}, expires_delta=token_expires
    )

    # Отправляем email с приглашением
    await send_registration_email(email_to=user.email, token=token)

    return user


@router.post("/resend-invite", response_model=UserInDB)
async def resend_invite(
    user_in: UserInvite,
    db: AsyncSession = Depends(get_async_session),
    current_user: Any = Depends(get_current_superuser),
) -> Any:
    """Повторно отправить приглашение пользователю (только для супер-администратора)"""
    # Проверяем, что пользователь существует
    user = await user_crud.get_user_by_email(db, email=user_in.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким адресом электронной почты не найден.",
        )

    if user.is_registered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже зарегистрирован.",
        )

    # Создаем новый токен для регистрации
    token_expires = timedelta(hours=24)
    token = create_access_token(
        data={"sub": str(user.id), "type": "registration"}, expires_delta=token_expires
    )

    # Отправляем email с приглашением
    await send_registration_email(email_to=user.email, token=token)

    return user


@router.post("/logout")
async def logout():
    """
Выход из системы. Клиент должен удалить токен авторизации.
"""
    return {"message": "Вы успешно вышли из системы. Пожалуйста, удалите токен авторизации на клиенте."}


@router.get("/me")
async def get_current_user_info(
    current_user: Any = Depends(get_current_active_user),
) -> Any:
    """Получить информацию о текущем пользователе"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_superuser": current_user.is_superuser,
        "is_recruiter": current_user.is_recruiter,
        "is_registered": current_user.is_registered,
    }
