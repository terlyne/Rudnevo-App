from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud import review as review_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewInDB

router = APIRouter()


@router.get("/", response_model=list[ReviewInDB])
async def read_reviews(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_session)
):
    """Получить список отзывов"""
    return await review_crud.get_reviews(db, skip=skip, limit=limit)


@router.post("/", response_model=ReviewInDB)
async def create_review(
    *, db: AsyncSession = Depends(get_async_session), review_in: ReviewCreate
):
    """Создать отзыв"""
    return await review_crud.create_review(db=db, review_in=review_in)


@router.put("/{review_id}", response_model=ReviewInDB)
async def update_review(
    *,
    db: AsyncSession = Depends(get_async_session),
    review_in: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """Обновление состояния отзыва"""
    return await review_crud.update_review(db=db, review_in=review_in)


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Удалить отзыв (только для администраторов)"""
    if not await review_crud.delete_review(db=db, review_id=review_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден."
        )
    return {"ok": True}
