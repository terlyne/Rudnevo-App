from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feedback import Feedback
from schemas.feedback import FeedbackCreate


async def get_feedback(db: AsyncSession, feedback_id: int) -> Feedback | None:
    """Получить обратную связь по ID"""
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    return result.scalar_one_or_none()


async def get_feedbacks(
    db: AsyncSession, skip: int = 0, limit: int = 100, show_hidden: bool = False
) -> list[Feedback]:
    """Получить список обратной связи"""
    query = select(Feedback)
    if not show_hidden:
        query = query.where(Feedback.is_hidden == False)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


async def create_feedback(db: AsyncSession, feedback_in: FeedbackCreate) -> Feedback:
    """Создать обратную связь"""
    feedback_data = feedback_in.model_dump()
    db_feedback = Feedback(**feedback_data)
    db.add(db_feedback)
    await db.commit()
    await db.refresh(db_feedback)
    return db_feedback


async def delete_feedback(db: AsyncSession, feedback_id: int) -> bool:
    """Удалить обратную связь"""
    db_feedback = await get_feedback(db, feedback_id)
    if not db_feedback:
        return False

    await db.delete(db_feedback)
    await db.commit()
    return True


async def toggle_feedback_visibility(db: AsyncSession, feedback_id: int) -> Feedback | None:
    """Переключить видимость обратной связи"""
    db_feedback = await get_feedback(db, feedback_id)
    if not db_feedback:
        return None

    db_feedback.is_hidden = not db_feedback.is_hidden
    await db.commit()
    await db.refresh(db_feedback)
    return db_feedback
