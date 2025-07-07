from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from api.deps import get_current_admin_or_superuser, get_current_user_optional
from crud import review as review_crud
from db.session import get_async_session
from models.user import User
from schemas.review import ReviewCreate, ReviewUpdate, ReviewInDB

# Публичный роутер для открытых эндпоинтов
public_router = APIRouter()

# Административный роутер для закрытых эндпоинтов
admin_router = APIRouter()


# === ПУБЛИЧНЫЕ ЭНДПОИНТЫ ===

@public_router.get("/", response_model=list[ReviewInDB])
async def read_public_reviews(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
):
    """Получить список публичных отзывов (открытый эндпоинт)"""
    return await review_crud.get_reviews(db, skip=skip, limit=limit, show_hidden=False)


@public_router.get("/{review_id}", response_model=ReviewInDB)
async def read_public_review(
    review_id: int, db: AsyncSession = Depends(get_async_session)
):
    """Получить публичный отзыв по ID"""
    review = await review_crud.get_review(db=db, review_id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден."
        )
    if review.is_hidden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден."
        )
    return review


# === АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ ===

@admin_router.get("/", response_model=list[ReviewInDB])
async def read_all_reviews(
    skip: int = 0,
    limit: int = 100,
    show_hidden: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Получить список всех отзывов (включая скрытые) - только для администраторов"""
    return await review_crud.get_reviews(db, skip=skip, limit=limit, show_hidden=show_hidden)


@admin_router.get("/{review_id}", response_model=ReviewInDB)
async def read_review_admin(
    review_id: int, 
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Получить отзыв по ID (включая скрытые) - только для администраторов"""
    review = await review_crud.get_review(db=db, review_id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден."
        )
    return review


@admin_router.post("/", response_model=ReviewInDB)
async def create_review(
    *, db: AsyncSession = Depends(get_async_session), review_in: ReviewCreate, current_user: User = Depends(get_current_admin_or_superuser)
):
    """Создать отзыв (только для администраторов)"""
    return await review_crud.create_review(db=db, review_in=review_in)


@admin_router.put("/{review_id}", response_model=ReviewInDB)
async def update_review(
    review_id: int,
    *,
    db: AsyncSession = Depends(get_async_session),
    review_in: ReviewUpdate,
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Обновление состояния отзыва (только для администраторов)"""
    return await review_crud.update_review(db=db, review_id=review_id, review_in=review_in)


@admin_router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Удалить отзыв (только для администраторов)"""
    if not await review_crud.delete_review(db=db, review_id=review_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден."
        )
    return {"ok": True}
