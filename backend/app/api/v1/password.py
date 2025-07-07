from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_active_user
from core.security import verify_password
from crud import user as user_crud
from db.session import get_async_session
from models.user import User
from schemas.password import PasswordChange, PasswordReset, PasswordResetConfirm
from utils.email import send_reset_password_email

router = APIRouter()


@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset, db: AsyncSession = Depends(get_async_session)
):
    """Запрос на сброс пароля"""
    user = await user_crud.get_user_by_email(db, email=password_reset.email)
    if not user:
        # Не сообщаем, что email не существует (безопасность)
        return {
            "message": "Письмо для сброса пароля было отправлено, если пользователь с таким адресом существует."
        }

    # Создаем токен для сброса пароля
    token_expires = timedelta(hours=24)
    token = user_crud.create_password_reset_token(user, expires_delta=token_expires)

    # Отправляем email
    await send_reset_password_email(
        email_to=user.email,
        token=token,
        username=user.username or "пользователь",  # Если username еще не задан
    )

    return {
        "message": "Письмо для сброса пароля было отправлено, если пользователь с таким адресом существует."
    }


@router.post("/reset-password")
async def reset_password(
    password_reset: PasswordResetConfirm, db: AsyncSession = Depends(get_async_session)
):
    """Подтверждение сброса пароля"""
    try:
        user = await user_crud.verify_password_reset_token(
            db, token=password_reset.token
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или просроченный токен.",
        )

    # Обновляем пароль
    user_update = {"password": password_reset.new_password}
    user = await user_crud.update_user(db, user.id, user_update)

    return {"message": "Пароль был успешно обновлен."}


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Изменение пароля авторизованным администратором"""
    if not verify_password(
        password_change.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Неправильный пароль."
        )

    # Обновляем пароль
    user_update = {"password": password_change.new_password}
    await user_crud.update_user(db, current_user.id, user_update)

    return {"message": "Пароль был успешно обновлен."}
