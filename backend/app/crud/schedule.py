from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


async def get_schedule(db: AsyncSession, schedule_id: int) -> Schedule | None:
    """Получить расписание по ID"""
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    return result.scalar_one_or_none()


async def get_schedules(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Schedule]:
    """Получить список расписаний"""
    result = await db.execute(
        select(Schedule).order_by(Schedule.start_date.asc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def create_schedule(db: AsyncSession, schedule_in: ScheduleCreate) -> Schedule:
    """Создать расписание"""
    db_schedule = Schedule(
        title=schedule_in.title,
        shift_number=schedule_in.shift_number,
        description=schedule_in.description,
        college_name=schedule_in.college_name,
        room_number=schedule_in.room_number,
        start_date=schedule_in.start_date,
        end_date=schedule_in.end_date,
    )
    db.add(db_schedule)
    await db.commit()
    await db.refresh(db_schedule)
    return db_schedule


async def update_schedule(
    db: AsyncSession, schedule_id: int, schedule_in: ScheduleUpdate
) -> Schedule | None:
    """Обновить расписание"""
    db_schedule = await get_schedule(db, schedule_id)
    if not db_schedule:
        return None

    update_data = schedule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_schedule, field, value)

    await db.commit()
    await db.refresh(db_schedule)
    return db_schedule


async def delete_schedule(db: AsyncSession, schedule_id: int) -> bool:
    """Удалить расписание"""
    db_schedule = await get_schedule(db, schedule_id)
    if not db_schedule:
        return False

    await db.delete(db_schedule)
    await db.commit()
    return True
