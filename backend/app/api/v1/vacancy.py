from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud import vacancy as vacancy_crud, student as student_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.vacancy import VacancyCreate, VacancyUpdate, VacancyResponse

router = APIRouter()

@router.get("/", response_model=list[VacancyResponse])
async def read_vacancies(
    skip: int = 0,
    limit: int = 100,
    show_hidden: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Получить список вакансий"""
    if not current_user.is_recruiter:
        # Для обычных пользователей показываем только не скрытые вакансии
        return await vacancy_crud.get_vacancies(
            db,
            skip=skip,
            limit=limit,
            include_hidden=False
        )
    else:
        # Для работодателей показываем их вакансии (включая скрытые)
        return await vacancy_crud.get_vacancies(
            db,
            skip=skip,
            limit=limit,
            recruiter_id=current_user.id,
            include_hidden=show_hidden
        )


@router.get("/public", response_model=list[VacancyResponse])
async def read_public_vacancies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
):
    """Получить список доступных вакансий (публичный эндпоинт)"""
    return await vacancy_crud.get_vacancies(
        db,
        skip=skip,
        limit=limit,
        include_hidden=False
    )


@router.get("/all", response_model=list[VacancyResponse])
async def read_all_vacancies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Получить все вакансии (только для суперпользователей)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала."
        )
    
    return await vacancy_crud.get_vacancies(
        db,
        skip=skip,
        limit=limit,
        include_hidden=True
    )


@router.get("/{vacancy_id}", response_model=VacancyResponse)
async def read_vacancy(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Получить вакансию по ID"""
    vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена."
        )
    
    # Если вакансия скрыта, проверяем права доступа
    if vacancy.is_hidden:
        if not current_user.is_recruiter and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на просмотр этой вакансии."
            )
        
        # Если работодатель, проверяем что это его вакансия
        if current_user.is_recruiter and not current_user.is_superuser:
            if vacancy.recruiter_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="У вас нет прав на просмотр этой вакансии."
                )
    
    return vacancy


@router.get("/public/{vacancy_id}", response_model=VacancyResponse)
async def read_public_vacancy(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_id: int,
):
    """Получить вакансию по ID (публичный эндпоинт)"""
    vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена."
        )
    
    # Проверяем что вакансия не скрыта
    if vacancy.is_hidden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена."
        )
    
    return vacancy


@router.get("/{vacancy_id}/statistics")
async def get_vacancy_statistics(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Получить статистику вакансии"""
    if not current_user.is_recruiter and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на просмотр статистики."
        )
    
    vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена."
        )
    
    # Проверяем права доступа
    if current_user.is_recruiter and not current_user.is_superuser:
        if vacancy.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на просмотр статистики этой вакансии."
            )
    
    # Получаем количество заявок
    total_applications = await student_crud.get_students_count_by_vacancy(db, vacancy_id)
    
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
    conversion_rate = (len(invited_applications) / total_applications * 100) if total_applications > 0 else 0
    
    return {
        "vacancy_id": vacancy_id,
        "total_applications": total_applications,
        "new_applications": len(new_applications),
        "in_review_applications": len(in_review_applications),
        "invited_applications": len(invited_applications),
        "rejected_applications": len(rejected_applications),
        "conversion_rate": round(conversion_rate, 2),
        "required_amount": vacancy.required_amount,
        "is_full": total_applications >= vacancy.required_amount
    }


@router.post("/", response_model=VacancyResponse)
async def create_vacancy(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_in: VacancyCreate,
    current_user: User = Depends(get_current_active_user),
):
    """Создание вакансии (только для работодателей)"""
    if not current_user.is_recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала."
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


@router.put("/{vacancy_id}", response_model=VacancyResponse)
async def update_vacancy(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_id: int,
    vacancy_in: VacancyUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """Обновить вакансию"""
    vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена."
        )
    
    # Проверка что пользователь является владельцем или суперпользователем
    if vacancy.recruiter_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете редактировать эту вакансию."
        )
    
    updated_vacancy = await vacancy_crud.update_vacancy(
        db=db,
        vacancy_id=vacancy_id,
        vacancy_in=vacancy_in,
    )
    
    return updated_vacancy


@router.delete("/{vacancy_id}")
async def delete_vacancy(
    *,
    db: AsyncSession = Depends(get_async_session),
    vacancy_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Удалить вакансию"""
    vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена."
        )
    
    if vacancy.recruiter_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете удалить эту вакансию."
        )
    
    await vacancy_crud.delete_vacancy(db=db, vacancy_id=vacancy_id)
    return {"ok": True}