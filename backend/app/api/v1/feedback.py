from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.deps import get_current_admin_or_superuser, get_current_user_optional
from app.crud import feedback as feedback_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackInDB, FeedbackResponse, FeedbackUpdate
from app.utils.email import send_feedback_response

# Публичный роутер для открытых эндпоинтов
public_router = APIRouter()

# Административный роутер для закрытых эндпоинтов
admin_router = APIRouter()


# === ПУБЛИЧНЫЕ ЭНДПОИНТЫ ===

@public_router.get("/", response_model=list[FeedbackInDB])
async def read_public_feedbacks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
):
    """Получить список публичных вопросов (открытый эндпоинт)"""
    return await feedback_crud.get_feedbacks(db, skip=skip, limit=limit, show_hidden=False)


@public_router.get("/{feedback_id}", response_model=FeedbackInDB)
async def read_public_feedback(
    feedback_id: int, 
    db: AsyncSession = Depends(get_async_session),
):
    """Получить публичный вопрос по ID"""
    feedback = await feedback_crud.get_feedback(db=db, feedback_id=feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вопрос не найден."
        )
    if feedback.is_hidden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вопрос не найден."
        )
    return feedback


@public_router.post("/", response_model=FeedbackInDB)
async def create_feedback(
    *, db: AsyncSession = Depends(get_async_session), feedback_in: FeedbackCreate
):
    """Создать обратную связь (открытый эндпоинт)"""
    return await feedback_crud.create_feedback(db=db, feedback_in=feedback_in)


# === АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ ===

@admin_router.get("/", response_model=list[FeedbackInDB])
async def read_all_feedbacks(
    skip: int = 0,
    limit: int = 100,
    show_hidden: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Получить список всех вопросов (включая скрытые) - только для администраторов"""
    return await feedback_crud.get_feedbacks(db, skip=skip, limit=limit, show_hidden=show_hidden)


@admin_router.get("/{feedback_id}", response_model=FeedbackInDB)
async def read_feedback_admin(
    feedback_id: int, 
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Получить вопрос по ID (включая скрытые) - только для администраторов"""
    feedback = await feedback_crud.get_feedback(db=db, feedback_id=feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вопрос не найден."
        )
    return feedback


@admin_router.put("/{feedback_id}", response_model=FeedbackInDB)
async def update_feedback(
    feedback_id: int,
    *,
    db: AsyncSession = Depends(get_async_session),
    feedback_in: FeedbackUpdate,
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Обновить обратную связь (только для администраторов)"""
    feedback = await feedback_crud.get_feedback(db=db, feedback_id=feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вопрос не найден."
        )
    
    # Обновляем поля
    update_data = feedback_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feedback, field, value)
    
    await db.commit()
    await db.refresh(feedback)
    return feedback


@admin_router.post("/{feedback_id}/respond")
async def respond_to_feedback(
    *,
    db: AsyncSession = Depends(get_async_session),
    feedback_id: int,
    response: FeedbackResponse,
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Ответить на обратную связь (только для администраторов)"""
    feedback = await feedback_crud.get_feedback(db=db, feedback_id=feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вопрос не найден."
        )

    # Отправляем ответ на email
    await send_feedback_response(
        email_to=feedback.email,
        name=feedback.name,
        response_text=response.response_text,
    )

    return {"ok": True}


@admin_router.post("/{feedback_id}/toggle-visibility", response_model=FeedbackInDB)
async def toggle_feedback_visibility(
    *,
    db: AsyncSession = Depends(get_async_session),
    feedback_id: int,
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Переключить видимость обратной связи (только для администраторов)"""
    feedback = await feedback_crud.toggle_feedback_visibility(db=db, feedback_id=feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вопрос не найден."
        )
    return feedback


@admin_router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Удалить обратную связь (только для администраторов)"""
    if not await feedback_crud.delete_feedback(db=db, feedback_id=feedback_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вопрос не найден."
        )
    return {"ok": True}
