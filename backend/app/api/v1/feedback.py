from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud import feedback as feedback_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackInDB, FeedbackResponse
from app.utils.email import send_feedback_response

router = APIRouter()


@router.get("/", response_model=list[FeedbackInDB])
async def read_feedbacks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """Получить список обратной связи (только для администраторов)"""
    return await feedback_crud.get_feedbacks(db, skip=skip, limit=limit)


@router.post("/", response_model=FeedbackInDB)
async def create_feedback(
    *,
    db: AsyncSession = Depends(get_async_session),
    feedback_in: FeedbackCreate
):
    """Создать обратную связь"""
    return await feedback_crud.create_feedback(db=db, feedback_in=feedback_in)


@router.post("/{feedback_id}/respond")
async def respond_to_feedback(
    *,
    db: AsyncSession = Depends(get_async_session),
    feedback_id: int,
    response: FeedbackResponse,
    current_user: User = Depends(get_current_active_user)
):
    """Ответить на обратную связь (только для администраторов)"""
    feedback = await feedback_crud.get_feedback(db=db, feedback_id=feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вопрос не найден."
        )
    
    # Отправляем ответ на email
    await send_feedback_response(
        email_to=feedback.email,
        name=feedback.name,
        response_text=response.response_text
    )
    
    return {"ok": True}


@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """Удалить обратную связь (только для администраторов)"""
    if not await feedback_crud.delete_feedback(db=db, feedback_id=feedback_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вопрос не найден."
        )
    return {"ok": True}
