from typing import Any, Dict, Optional, Union, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.schedule import Schedule, ScheduleTemplate
from schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleTemplateCreate, ScheduleTemplateUpdate

import logging

logger = logging.getLogger(__name__)


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


# Функции для работы с шаблонами расписаний
async def get_schedule_template(db: AsyncSession, template_id: int) -> ScheduleTemplate | None:
    """Получить шаблон по ID"""
    result = await db.execute(select(ScheduleTemplate).where(ScheduleTemplate.id == template_id))
    return result.scalar_one_or_none()


async def get_schedule_template_by_college_id(
    db: AsyncSession, college_id: int
) -> Optional[ScheduleTemplate]:
    """
    Получить шаблон по college_id (первый активный при наличии дубликатов)
    """
    result = await db.execute(
        select(ScheduleTemplate)
        .where(ScheduleTemplate.college_id == college_id)
        .where(ScheduleTemplate.is_active == True)
        .order_by(ScheduleTemplate.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_active_schedule_templates(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[ScheduleTemplate]:
    """Получить все активные шаблоны"""
    result = await db.execute(
        select(ScheduleTemplate)
        .where(ScheduleTemplate.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def create_schedule_template(db: AsyncSession, template_in: ScheduleTemplateCreate) -> ScheduleTemplate:
    """Создать шаблон"""
    db_template = ScheduleTemplate(**template_in.model_dump())
    db.add(db_template)
    await db.commit()
    await db.refresh(db_template)
    return db_template


async def create_schedule_templates_multi(
    db: AsyncSession, templates: List[ScheduleTemplateCreate]
) -> List[ScheduleTemplate]:
    """Создать несколько шаблонов"""
    db_objs = []
    for template in templates:
        db_obj = ScheduleTemplate(**template.model_dump())
        db.add(db_obj)
        db_objs.append(db_obj)
    
    await db.commit()
    for obj in db_objs:
        await db.refresh(obj)
    
    return db_objs


async def update_schedule_template(
    db: AsyncSession, template_id: int, template_in: ScheduleTemplateUpdate
) -> ScheduleTemplate | None:
    """Обновить шаблон"""
    db_template = await get_schedule_template(db, template_id)
    if not db_template:
        return None

    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_template, field, value)

    await db.commit()
    await db.refresh(db_template)
    return db_template


async def delete_schedule_template(db: AsyncSession, template_id: int) -> bool:
    """Удалить шаблон"""
    logger.info(f"=== CRUD delete_schedule_template ===")
    logger.info(f"Template ID: {template_id}")
    
    try:
        db_template = await get_schedule_template(db, template_id)
        logger.info(f"Found template: {db_template is not None}")
        
        if not db_template:
            logger.warning(f"Template {template_id} not found in database")
            return False

        logger.info(f"Deleting template {template_id} from database")
        await db.delete(db_template)
        await db.commit()
        logger.info(f"Template {template_id} deleted successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in CRUD delete_schedule_template: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def deactivate_schedule_templates_by_college_id(
    db: AsyncSession, college_id: int
) -> None:
    await db.execute(
        update(ScheduleTemplate)
        .where(ScheduleTemplate.college_id == college_id)
        .values(is_active=False)
    )
    await db.commit()


async def delete_all_schedule_templates(db: AsyncSession) -> None:
    """Удалить все шаблоны расписаний"""
    await db.execute(delete(ScheduleTemplate))
    await db.commit()
