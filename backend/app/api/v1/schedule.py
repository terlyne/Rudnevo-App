from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud import schedule as schedule_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleInDB

router = APIRouter()


@router.get("/", response_model=list[ScheduleInDB])
async def read_schedules(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_session)
):
    """Получить список расписаний"""
    return await schedule_crud.get_schedules(db, skip=skip, limit=limit)


@router.post("/", response_model=ScheduleInDB)
async def create_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_in: ScheduleCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Создать расписание (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )
    return await schedule_crud.create_schedule(db=db, schedule_in=schedule_in)


@router.put("/{schedule_id}", response_model=ScheduleInDB)
async def update_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_id: int,
    schedule_in: ScheduleUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Обновить расписание (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )
    schedule = await schedule_crud.update_schedule(
        db=db, schedule_id=schedule_id, schedule_in=schedule_in
    )
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Расписание не найдено."
        )
    return schedule


@router.delete("/{schedule_id}")
async def delete_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Удалить расписание (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )
    if not await schedule_crud.delete_schedule(db=db, schedule_id=schedule_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Расписание не найдено."
        )
    return {"ok": True}
