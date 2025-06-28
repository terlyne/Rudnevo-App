from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_or_superuser
from app.crud import review as review_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewInDB

router = APIRouter()


@router.get("/", response_model=list[ReviewInDB])
async def read_reviews(
    skip: int = 0,
    limit: int = 100,
    show_hidden: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Получить список отзывов"""
    # Для всех администраторов (супер-администраторов и обычных администраторов) 
    # показываем все отзывы (включая неодобренные) или по параметру
    return await review_crud.get_reviews(
        db, skip=skip, limit=limit, show_hidden=show_hidden
    )


@router.get("/pending", response_model=list[ReviewInDB])
async def read_pending_reviews(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Получить список неодобренных отзывов (только для администраторов)"""
    return await review_crud.get_reviews(db, skip=skip, limit=limit, show_hidden=True)


@router.get("/{review_id}", response_model=ReviewInDB)
async def read_review(
    review_id: int, db: AsyncSession = Depends(get_async_session)
):
    """Получить отзыв по ID"""
    review = await review_crud.get_review(db=db, review_id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден."
        )
    return review


@router.post("/", response_model=ReviewInDB)
async def create_review(
    *, db: AsyncSession = Depends(get_async_session), review_in: ReviewCreate, current_user: User = Depends(get_current_admin_or_superuser)
):
    """Создать отзыв"""
    return await review_crud.create_review(db=db, review_in=review_in)


@router.put("/{review_id}", response_model=ReviewInDB)
async def update_review(
    review_id: int,
    *,
    db: AsyncSession = Depends(get_async_session),
    review_in: ReviewUpdate,
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Обновление состояния отзыва (только для администраторов)"""
    return await review_crud.update_review(db=db, review_id=review_id, review_in=review_in)


@router.delete("/{review_id}")
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
