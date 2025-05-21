from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from schedules.models import Schedule
from schedules.schemas import ScheduleCreate, ScheduleUpdate
from typing import List


async def get_schedule(session: AsyncSession, schedule_id: int) -> Optional[Schedule]:
    """Получение расписания по ID"""
    result = await session.execute(select(Schedule).where(Schedule.id == schedule_id))
    return result.scalar_one_or_none()


async def get_schedules(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Schedule]:
    """
    Получает список расписаний
    """
    query = select(Schedule).offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def create_schedule(session: AsyncSession, schedule: ScheduleCreate) -> Schedule:
    """Создание нового расписания"""
    db_schedule = Schedule(**schedule.model_dump())
    session.add(db_schedule)
    await session.commit()
    await session.refresh(db_schedule)
    return db_schedule


async def update_schedule(
    session: AsyncSession, schedule_id: int, schedule: ScheduleUpdate
) -> Optional[Schedule]:
    """Обновление расписания"""
    update_data = schedule.model_dump(exclude_unset=True)
    if not update_data:
        return None

    stmt = update(Schedule).where(Schedule.id == schedule_id).values(**update_data)
    await session.execute(stmt)
    await session.commit()

    result = await session.execute(select(Schedule).where(Schedule.id == schedule_id))
    return result.scalar_one_or_none()


async def delete_schedule(session: AsyncSession, schedule_id: int) -> bool:
    """Удаление расписания"""
    stmt = delete(Schedule).where(Schedule.id == schedule_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def toggle_schedule_visibility(
    session: AsyncSession, schedule_id: int
) -> Optional[Schedule]:
    """Переключение видимости расписания"""
    schedule = await get_schedule(session, schedule_id)
    if not schedule:
        return None

    schedule.is_hidden = not schedule.is_hidden
    await session.commit()
    await session.refresh(schedule)
    return schedule
