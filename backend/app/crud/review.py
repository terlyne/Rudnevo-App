from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate


async def get_review(db: AsyncSession, review_id: int) -> Review | None:
    """Получить отзыв по ID"""
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()


async def get_reviews(
    db: AsyncSession, skip: int = 0, limit: int = 100, show_hidden: bool = False
) -> list[Review]:
    """Получить список отзывов"""
    query = select(Review)

    if not show_hidden:
        query = query.where(Review.is_approved == True)

    result = await db.execute(
        query.order_by(Review.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def create_review(db: AsyncSession, review_in: ReviewCreate) -> Review:
    """Создать отзыв"""
    db_review = Review(**review_in.model_dump())
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review


async def update_review(
    db: AsyncSession, review_id: int, review_in: ReviewUpdate
) -> Review | None:
    """Обновление отзыва"""
    db_review = await get_review(db, review_id)
    if not db_review:
        return None

    # Обновляем только переданные поля
    update_data = review_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_review, field, value)
    
    await db.commit()
    await db.refresh(db_review)

    return db_review


async def delete_review(db: AsyncSession, review_id: int) -> bool:
    """Удалить отзыв"""
    db_review = await get_review(db, review_id)
    if not db_review:
        return False

    await db.delete(db_review)
    await db.commit()
    return True
