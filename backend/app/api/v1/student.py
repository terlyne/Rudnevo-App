from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Union
from datetime import date
import os

from api.deps import get_current_vacancy_user
from crud import student as student_crud, vacancy as vacancy_crud
from db.session import get_async_session
from models.user import User
from models.student import ApplicationStatus
from schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentBulkStatusUpdate,
)
from utils.files import save_upload_file
from core.config import settings

router = APIRouter()


@router.post("/apply", response_model=StudentResponse)
async def apply_for_vacancy(
    *,
    db: AsyncSession = Depends(get_async_session),
    full_name: str = Form(..., description="ФИО студента"),
    birth_date: date = Form(..., description="Дата рождения в формате YYYY-MM-DD"),
    speciality: str = Form(..., description="Специальность/профессия"),
    phone: str = Form(..., description="Контактный номер телефона"),
    resume_link: Optional[str] = Form(
        None, description="Ссылка на резюме (опционально)"
    ),
    vacancy_id: int = Form(..., description="ID вакансии"),
    resume_file: Union[UploadFile, None, str] = File(
        None, description="Файл резюме (опционально)"
    ),
):
    """Подать заявку на вакансию (публичный эндпоинт)

    Резюме можно предоставить одним из способов:
    - Только ссылка на резюме (resume_link)
    - Только файл резюме (resume_file)
    - И ссылка, и файл
    - Без резюме (оба поля пустые)
    """
    if isinstance(resume_file, str) and resume_file == "":
        resume_file = None

    # Создаем объект StudentCreate
    student_in = StudentCreate(
        full_name=full_name,
        birth_date=birth_date,
        speciality=speciality,
        phone=phone,
        resume_link=resume_link,
        vacancy_id=vacancy_id,
    )

    # Проверяем существование вакансии
    vacancy = await vacancy_crud.get_vacancy(db, student_in.vacancy_id)
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена."
        )

    # Проверяем что вакансия не скрыта
    if vacancy.is_hidden:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вакансия недоступна для подачи заявок.",
        )

    # Проверяем количество уже поданных заявок
    current_applications = await student_crud.get_students_count_by_vacancy(
        db, student_in.vacancy_id
    )
    if current_applications >= vacancy.required_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Достигнуто максимальное количество заявок на эту вакансию.",
        )

    # Обрабатываем файл резюме если он загружен
    resume_file_path = None
    if resume_file:
        # Проверяем тип файла
        if resume_file.content_type not in settings.ALLOWED_RESUME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неподдерживаемый тип файла. Разрешены: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, RTF, HTML, MD, ODT, ODS, ODP",
            )

        resume_file_path = await save_upload_file(resume_file, "resumes")

    # Создаем студента с путем к файлу
    return await student_crud.create_student(
        db=db, student_in=student_in, resume_file_path=resume_file_path
    )


@router.get("/", response_model=list[StudentResponse])
async def read_students(
    skip: int = 0,
    limit: int = 100,
    vacancy_id: Optional[int] = None,
    status: Optional[ApplicationStatus] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_vacancy_user),
):
    """Получить список студентов (только для рекрутеров и супер-администраторов)"""
    # Супер-администратор может видеть все заявки
    if current_user.is_superuser:
        return await student_crud.get_students(
            db=db, skip=skip, limit=limit, vacancy_id=vacancy_id, status=status
        )
    
    # Рекрутер может видеть только заявки на свои вакансии
    if current_user.is_recruiter:
        if vacancy_id:
            # Проверяем что вакансия принадлежит рекрутеру
            vacancy = await vacancy_crud.get_vacancy(db, vacancy_id)
            if not vacancy or vacancy.recruiter_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="У вас нет прав на просмотр заявок на эту вакансию.",
                )
        else:
            # Получаем все вакансии рекрутера
            vacancies = await vacancy_crud.get_vacancies(
                db, recruiter_id=current_user.id
            )
            vacancy_ids = [v.id for v in vacancies]
            if not vacancy_ids:
                return []

            # Получаем заявки только на вакансии рекрутера
            students = []
            for vid in vacancy_ids:
                vacancy_students = await student_crud.get_students_by_vacancy(
                    db, vid, skip, limit
                )
                students.extend(vacancy_students)
            return students[:limit]
    
    # Обычный администратор не имеет доступа к заявкам
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="У вас нет прав на просмотр заявок.",
    )


@router.get("/{student_id}", response_model=StudentResponse)
async def read_student(
    *,
    db: AsyncSession = Depends(get_async_session),
    student_id: int,
    current_user: User = Depends(get_current_vacancy_user),
):
    """Получить детали студента (только для рекрутеров и супер-администраторов)"""
    student = await student_crud.get_student(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена."
        )

    # Супер-администратор может видеть любую заявку
    if current_user.is_superuser:
        return student

    # Рекрутер может видеть только заявки на свои вакансии
    if current_user.is_recruiter:
        vacancy = await vacancy_crud.get_vacancy(db, student.vacancy_id)
        if not vacancy or vacancy.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на просмотр этой заявки.",
            )
        return student

    # Обычный администратор не имеет доступа к заявкам
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="У вас нет прав на просмотр заявок.",
    )


@router.get("/{student_id}/resume-file")
async def resume_file(
    *,
    db: AsyncSession = Depends(get_async_session),
    student_id: int,
    current_user: User = Depends(get_current_vacancy_user),
):
    """Отправка файла резюме студента (только для рекрутеров и супер-администраторов)"""
    student = await student_crud.get_student(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена."
        )

    # Супер-администратор может скачать любое резюме
    if current_user.is_superuser:
        pass
    # Рекрутер может скачать только резюме с заявок на свои вакансии
    elif current_user.is_recruiter:
        vacancy = await vacancy_crud.get_vacancy(db, student.vacancy_id)
        if not vacancy or vacancy.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на скачивание этого резюме.",
            )
    else:
        # Обычный администратор не имеет доступа к заявкам
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на скачивание резюме.",
        )

    if not student.resume_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Файл резюме не найден."
        )

    # Получаем путь к файлу из URL
    file_path = os.path.join(settings.MEDIA_ROOT, student.resume_file.lstrip("/media/"))

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Файл резюме не найден."
        )

    # Используем сохраненное расширение файла или получаем из пути
    file_extension = student.resume_file_extension or os.path.splitext(file_path)[1]
    if not file_extension:
        file_extension = ".pdf"  # fallback
    
    # Определяем правильный MIME тип на основе расширения
    mime_types = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".txt": "text/plain",
        ".rtf": "text/rtf",
        ".html": "text/html",
        ".htm": "text/html",
        ".md": "text/markdown",
        ".odt": "application/vnd.oasis.opendocument.text",
        ".ods": "application/vnd.oasis.opendocument.spreadsheet",
        ".odp": "application/vnd.oasis.opendocument.presentation"
    }
    
    media_type = mime_types.get(file_extension.lower(), "application/octet-stream")

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=f"resume_{student.full_name.replace(' ', '_')}{file_extension}",
    )


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    *,
    db: AsyncSession = Depends(get_async_session),
    student_id: int,
    student_in: StudentUpdate,
    current_user: User = Depends(get_current_vacancy_user),
):
    """Обновить данные студента (только для рекрутеров и супер-администраторов)"""
    student = await student_crud.get_student(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена."
        )

    # Супер-администратор может редактировать любую заявку
    if current_user.is_superuser:
        pass
    # Рекрутер может редактировать только заявки на свои вакансии
    elif current_user.is_recruiter:
        vacancy = await vacancy_crud.get_vacancy(db, student.vacancy_id)
        if not vacancy or vacancy.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на редактирование этой заявки.",
            )
    else:
        # Обычный администратор не имеет доступа к заявкам
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на редактирование заявок.",
        )

    updated_student = await student_crud.update_student(
        db=db,
        student_id=student_id,
        student_in=student_in,
    )

    return updated_student


@router.post("/bulk-status-update")
async def bulk_update_student_status(
    *,
    db: AsyncSession = Depends(get_async_session),
    bulk_update: StudentBulkStatusUpdate,
    current_user: User = Depends(get_current_vacancy_user),
):
    """Массовое обновление статусов студентов (только для рекрутеров и супер-администраторов)"""
    # Супер-администратор может обновлять любые заявки
    if current_user.is_superuser:
        pass
    # Рекрутер может обновлять только заявки на свои вакансии
    elif current_user.is_recruiter:
        for student_id in bulk_update.student_ids:
            student = await student_crud.get_student(db, student_id)
            if student:
                vacancy = await vacancy_crud.get_vacancy(db, student.vacancy_id)
                if not vacancy or vacancy.recruiter_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"У вас нет прав на обновление заявки {student_id}.",
                    )
    else:
        # Обычный администратор не имеет доступа к заявкам
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на массовое обновление статусов.",
        )

    updated_count = await student_crud.bulk_update_status(
        db=db, student_ids=bulk_update.student_ids, status=bulk_update.status
    )

    return {"updated_count": updated_count}


@router.delete("/{student_id}")
async def delete_student(
    *,
    db: AsyncSession = Depends(get_async_session),
    student_id: int,
    current_user: User = Depends(get_current_vacancy_user),
):
    """Удалить заявку студента (только для супер-администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на удаление заявок.",
        )

    student = await student_crud.get_student(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена."
        )

    await student_crud.delete_student(db=db, student_id=student_id)
    return {"ok": True}


