from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.vacancy import Vacancy
from schemas.vacancy import VacancyCreate, VacancyUpdate


async def get_vacancy(db: AsyncSession, vacancy_id: int) -> Vacancy | None:
    """Получить вакансию по ID"""
    result = await db.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
    return result.scalar_one_or_none()


async def get_vacancies(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    recruiter_id: int | None = None,
    include_hidden: bool = False,
) -> list[Vacancy]:
    """Получить список вакансий"""
    query = select(Vacancy)

    if not include_hidden:
        query = query.where(Vacancy.is_hidden == False)

    if recruiter_id is not None:
        query = query.where(Vacancy.recruiter_id == recruiter_id)

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


async def create_vacancy(db: AsyncSession, vacancy_in: VacancyCreate) -> Vacancy:
    """Создать вакансию"""
    db_vacancy = Vacancy(**vacancy_in.model_dump())
    db.add(db_vacancy)
    await db.commit()
    await db.refresh(db_vacancy)
    return db_vacancy


async def update_vacancy(
    db: AsyncSession,
    vacancy_id: int,
    vacancy_in: VacancyUpdate,
) -> Vacancy | None:
    """Обновить вакансию"""
    db_vacancy = await get_vacancy(db, vacancy_id)
    if not db_vacancy:
        return None

    update_data = vacancy_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_vacancy, field, value)

    await db.commit()
    await db.refresh(db_vacancy)
    return db_vacancy


async def delete_vacancy(db: AsyncSession, vacancy_id: int) -> bool:
    """Удалить вакансию"""
    db_vacancy = await get_vacancy(db, vacancy_id)
    if not db_vacancy:
        return False

    await db.delete(db_vacancy)
    await db.commit()
    return True
