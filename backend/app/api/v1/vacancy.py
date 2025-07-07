from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.deps import get_current_recruiter, get_current_superuser, get_current_vacancy_user, get_current_user_optional
from app.crud import vacancy as vacancy_crud, student as student_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.vacancy import VacancyCreate, VacancyUpdate, VacancyResponse

# Публичный роутер для открытых эндпоинтов
public_router = APIRouter()

# Административный роутер для закрытых эндпоинтов
admin_router = APIRouter()


# === ПУБЛИЧНЫЕ ЭНДПОИНТЫ ===

@public_router.get("/", response_model=list[VacancyResponse])
async def read_public_vacancies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
):
    """Получить список публичных вакансий (открытый эндпоинт)"""
    return await vacancy_crud.get_vacancies(db, skip=skip, limit=limit, include_hidden=False)


@public_router.get("/{vacancy_id}", response_model=VacancyResponse)
async def read_public_vacancy(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_id: int,
):
    """Получить публичную вакансию по ID"""
    vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена.")
    
    if vacancy.is_hidden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена.")
    
    return vacancy


# === АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ ===

@admin_router.get("/", response_model=list[VacancyResponse])
async def read_all_vacancies(
    skip: int = 0,
    limit: int = 100,
    show_hidden: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_vacancy_user),
):
    """Получить список всех вакансий (включая скрытые) - только для авторизованных пользователей с правами"""
    if show_hidden:
        # Супер-администраторы видят АБСОЛЮТНО ВСЕ вакансии всех работодателей
        if current_user.is_superuser:
            return await vacancy_crud.get_vacancies(db, skip=skip, limit=limit, include_hidden=True)
        
        # Работодатели видят ТОЛЬКО СВОИ вакансии (как публичные, так и скрытые)
        elif current_user.is_recruiter:
            return await vacancy_crud.get_vacancies(db, skip=skip, limit=limit, recruiter_id=current_user.id, include_hidden=True)
        
        else:
            # Обычные администраторы не имеют доступа к скрытым вакансиям
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав на просмотр скрытых вакансий")
    
    # Публичные вакансии (для всех авторизованных пользователей)
    return await vacancy_crud.get_vacancies(db, skip=skip, limit=limit, include_hidden=False)


@admin_router.get("/{vacancy_id}", response_model=VacancyResponse)
async def read_vacancy_admin(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_id: int,
    current_user: User = Depends(get_current_vacancy_user),
):
    """Получить вакансию по ID (включая скрытые) - только для авторизованных пользователей с правами"""
    vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена.")
    
    # Если вакансия скрыта — проверяем права доступа
    if vacancy.is_hidden:
        # Супер-администраторы могут видеть любую вакансию
        if current_user.is_superuser:
            return vacancy
        
        # Работодатели могут видеть только свои вакансии
        elif current_user.is_recruiter and vacancy.recruiter_id == current_user.id:
            return vacancy
        
        else:
            # Обычные администраторы не имеют доступа к скрытым вакансиям
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав на просмотр скрытых вакансий")
    
    return vacancy


@admin_router.get("/{vacancy_id}/statistics")
async def get_vacancy_statistics(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_id: int,
    current_user: User = Depends(get_current_vacancy_user),
):
    """Получить статистику вакансии"""
    vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена."
        )

    # Супер-администратор может видеть статистику любой вакансии
    if current_user.is_superuser:
        pass
    # Рекрутер может видеть статистику только своих вакансий
    elif current_user.is_recruiter:
        if vacancy.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на просмотр статистики этой вакансии.",
            )
    else:
        # Обычный администратор не имеет доступа к вакансиям
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на просмотр статистики вакансий.",
        )

    # Получаем количество заявок
    total_applications = await student_crud.get_students_count_by_vacancy(
        db, vacancy_id
    )

    # Получаем заявки по статусам
    new_applications = await student_crud.get_students(
        db, vacancy_id=vacancy_id, status="new"
    )
    in_review_applications = await student_crud.get_students(
        db, vacancy_id=vacancy_id, status="in_review"
    )
    invited_applications = await student_crud.get_students(
        db, vacancy_id=vacancy_id, status="invited"
    )
    rejected_applications = await student_crud.get_students(
        db, vacancy_id=vacancy_id, status="rejected"
    )

    # Рассчитываем конверсию (приглашенные / общее количество)
    conversion_rate = (
        (len(invited_applications) / total_applications * 100)
        if total_applications > 0
        else 0
    )

    return {
        "vacancy_id": vacancy_id,
        "total_applications": total_applications,
        "new_applications": len(new_applications),
        "in_review_applications": len(in_review_applications),
        "invited_applications": len(invited_applications),
        "rejected_applications": len(rejected_applications),
        "conversion_rate": round(conversion_rate, 2),
        "required_amount": vacancy.required_amount,
        "is_full": total_applications >= vacancy.required_amount,
    }


@admin_router.post("/", response_model=VacancyResponse)
async def create_vacancy(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_in: VacancyCreate,
    current_user: User = Depends(get_current_vacancy_user),
):
    """Создание вакансии (только для рекрутеров и супер-администраторов)"""
    if not current_user.is_recruiter and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на создание вакансий.",
        )

    # Валидация зарплаты
    if vacancy_in.salary_from is not None and vacancy_in.salary_to is not None:
        if vacancy_in.salary_from >= vacancy_in.salary_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Зарплата 'до' должна быть больше зарплаты 'от'.",
            )

    # Создаем вакансию с recruiter_id
    from app.models.vacancy import Vacancy

    vacancy_data = vacancy_in.model_dump()
    vacancy_data["recruiter_id"] = current_user.id

    db_vacancy = Vacancy(**vacancy_data)
    db.add(db_vacancy)
    await db.commit()
    await db.refresh(db_vacancy)

    return db_vacancy


@admin_router.put("/{vacancy_id}", response_model=VacancyResponse)
async def update_vacancy(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_id: int,
    vacancy_in: VacancyUpdate,
    current_user: User = Depends(get_current_vacancy_user),
):
    """Обновить вакансию (только для рекрутеров и супер-администраторов)"""
    vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)

    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена."
        )

    # Супер-администратор может редактировать любую вакансию
    if current_user.is_superuser:
        pass
    # Рекрутер может редактировать только свои вакансии
    elif current_user.is_recruiter:
        if vacancy.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на редактирование этой вакансии.",
            )
    else:
        # Обычный администратор не имеет доступа к вакансиям
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на редактирование вакансий.",
        )

    # Валидация зарплаты
    if vacancy_in.salary_from is not None and vacancy_in.salary_to is not None:
        if vacancy_in.salary_from >= vacancy_in.salary_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Зарплата 'до' должна быть больше зарплаты 'от'.",
            )

    return await vacancy_crud.update_vacancy(db=db, vacancy_id=vacancy_id, vacancy_in=vacancy_in)


@admin_router.delete("/{vacancy_id}")
async def delete_vacancy(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_id: int,
    current_user: User = Depends(get_current_vacancy_user),
):
    """Удалить вакансию (только для рекрутеров и супер-администраторов)"""
    vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)

    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена."
        )

    # Супер-администратор может удалять любую вакансию
    if current_user.is_superuser:
        pass
    # Рекрутер может удалять только свои вакансии
    elif current_user.is_recruiter:
        if vacancy.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на удаление этой вакансии.",
            )
    else:
        # Обычный администратор не имеет доступа к вакансиям
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на удаление вакансий.",
        )

    if not await vacancy_crud.delete_vacancy(db=db, vacancy_id=vacancy_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена."
        )
    return {"ok": True}
