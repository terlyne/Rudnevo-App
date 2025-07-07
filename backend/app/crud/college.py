from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.college import College
from schemas.college import CollegeCreate, CollegeUpdate


async def get_colleges_list(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[College]:
    """Получить список колледжей"""
    query = select(College)

    result = await db.execute(
        query.order_by(College.name.asc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def get_college(db: AsyncSession, college_id: int) -> College | None:
    """Получить колледж по ID"""
    result = await db.execute(select(College).where(College.id == college_id))
    return result.scalar_one_or_none()


async def get_college_by_name(db: AsyncSession, college_name: str) -> College | None:
    """Получить колледж по названию"""
    result = await db.execute(select(College).where(College.name == college_name))
    return result.scalar_one_or_none()


async def create_college(db: AsyncSession, college_in: CollegeCreate) -> College:
    """Создать колледж"""
    db_college = College(**college_in.model_dump())
    db.add(db_college)
    await db.commit()
    await db.refresh(db_college)
    return db_college


async def update_college(
    db: AsyncSession, college_id: int, college_in: CollegeUpdate
) -> College | None:
    """Обновить колледж"""
    db_college = await get_college(db, college_id)
    if not db_college:
        return None

    update_data = college_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "image_url":
            setattr(db_college, field, value)
        elif value is not None:
            setattr(db_college, field, value)

    await db.commit()
    await db.refresh(db_college)
    return db_college


async def delete_college(db: AsyncSession, college_id: int) -> bool:
    """Удалить колледж"""
    db_college = await get_college(db, college_id)
    if not db_college:
        return False

    await db.delete(db_college)
    await db.commit()
    return True 