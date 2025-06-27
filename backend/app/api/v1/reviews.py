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
    skip: int = 0,
    limit: int = 100,
    show_hidden: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Получить список отзывов"""
    # Для администраторов показываем все отзывы (включая неодобренные) или по параметру
    # Для обычных пользователей только одобренные отзывы
    if current_user.is_superuser:
        show_hidden_param = show_hidden
    else:
        show_hidden_param = False
    
    return await review_crud.get_reviews(
        db, skip=skip, limit=limit, show_hidden=show_hidden_param
    )


@router.get("/pending", response_model=list[ReviewInDB])
async def read_pending_reviews(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Получить список неодобренных отзывов (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )

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
    *, db: AsyncSession = Depends(get_async_session), review_in: ReviewCreate
):
    """Создать отзыв"""
    return await review_crud.create_review(db=db, review_in=review_in)


@router.put("/{review_id}", response_model=ReviewInDB)
async def update_review(
    review_id: int,
    *,
    db: AsyncSession = Depends(get_async_session),
    review_in: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """Обновление состояния отзыва (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )
    return await review_crud.update_review(db=db, review_id=review_id, review_in=review_in)


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Удалить отзыв (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )
    if not await review_crud.delete_review(db=db, review_id=review_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден."
        )
    return {"ok": True}
