from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.crud import user as user_crud
from app.db.session import get_async_session
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserInDB, UserRegistration, UserInvite
from app.api.deps import get_current_superuser
from app.utils.email import send_registration_email

router = APIRouter()


@router.post("/register", response_model=Token)
async def register_user(
    registration: UserRegistration,
    db: AsyncSession = Depends(get_async_session)
) -> Any:
    """Регистрация администратора по токену из email"""
    try:
        # Проверяем токен и получаем пользователя
        user = await user_crud.verify_registration_token(db, registration.token)
        
        # Проверяем, что email совпадает с тем, что в токене
        if user.email != registration.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Адрес электронной почты не соответствует приглашению."
            )
        
        # Проверяем, что username не занят
        existing_user = await user_crud.get_user_by_username(db, registration.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким именем уже зарегистрирован."
            )
        
        # Обновляем пользователя
        user_update = {
            "username": registration.username,
            "password": registration.password,
            "is_registered": True
        }
        user = await user_crud.update_user(db, user.id, user_update)
        
        # Создаем токен доступа
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "email": user.email},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_async_session),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Аутентификация администратора"""
    user = await user_crud.get_user_by_username(db, form_data.username)
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
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "email": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/invite", response_model=UserInDB)
async def invite_user(
    user_in: UserInvite,
    db: AsyncSession = Depends(get_async_session),
    current_user: Any = Depends(get_current_superuser)
) -> Any:
    """Пригласить нового пользователя (только для супер-администратора)"""
    # Проверяем, что email не занят
    user = await user_crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким адресом электронной почты уже зарегистрирован."
        )
    
    # Создаем нового пользователя только с email
    new_user = UserCreate(
        email=user_in.email,
        is_superuser=False,  # Новый пользователь никогда не может быть суперпользователем
        is_registered=False
    )
    user = await user_crud.create_user(db, new_user)
    
    # Создаем токен для регистрации
    token_expires = timedelta(hours=24)
    token = create_access_token(
        data={"sub": str(user.id), "type": "registration"},
        expires_delta=token_expires
    )
    
    # Отправляем email с приглашением
    await send_registration_email(
        email_to=user.email,
        token=token
    )
    
    return user
