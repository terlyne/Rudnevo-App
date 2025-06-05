from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.schemas.review import ReviewCreate


async def get_review(
    db: AsyncSession,
    review_id: int
) -> Review | None:
    """Получить отзыв по ID"""
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()


async def get_reviews(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> list[Review]:
    """Получить список отзывов"""
    result = await db.execute(
        select(Review)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def create_review(
    db: AsyncSession,
    review_in: ReviewCreate
) -> Review:
    """Создать отзыв"""
    db_review = Review(**review_in.model_dump())
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review


async def delete_review(
    db: AsyncSession,
    review_id: int
) -> bool:
    """Удалить отзыв"""
    db_review = await get_review(db, review_id)
    if not db_review:
        return False

    await db.delete(db_review)
    await db.commit()
    return True 