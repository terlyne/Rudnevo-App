from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_superuser
from app.crud import user as user_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.user import UserInDB
from app.core.security import create_access_token, create_registration_token
from app.utils.email import send_registration_email
from datetime import timedelta

router = APIRouter()


@router.get("/me", response_model=UserInDB)
async def read_user_me(current_user: User = Depends(get_current_active_user)):
    """Получить текущего пользователя"""
    return current_user


@router.get("/", response_model=list[UserInDB])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_superuser),
):
    """Получить список пользователей (только для супер-администраторов)"""
    users = await user_crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserInDB)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_superuser),
):
    """Получить пользователя по ID (только для супер-администраторов)"""
    user = await user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден."
        )
    return user


@router.delete("/{user_id}")
async def delete_user(
    *,
    db: AsyncSession = Depends(get_async_session),
    user_id: int,
    current_user: User = Depends(get_current_superuser)
):
    """Удалить пользователя (только для супер-администраторов)"""
    if not await user_crud.delete_user(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден."
        )
    return {"ok": True}
