from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.models.student import Student, ApplicationStatus
from app.schemas.student import StudentCreate, StudentUpdate


async def get_student(db: AsyncSession, student_id: int) -> Student | None:
    """Получить студента по ID"""
    result = await db.execute(select(Student).where(Student.id == student_id))
    return result.scalar_one_or_none()


async def get_students(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    vacancy_id: int | None = None,
    status: ApplicationStatus | None = None,
) -> list[Student]:
    """Получить список студентов"""
    query = select(Student)

    if vacancy_id is not None:
        query = query.where(Student.vacancy_id == vacancy_id)

    if status is not None:
        query = query.where(Student.status == status)

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


async def create_student(
    db: AsyncSession, student_in: StudentCreate, resume_file_path: str | None = None
) -> Student:
    """Создать заявку студента"""
    student_data = student_in.model_dump()
    if resume_file_path:
        student_data["resume_file"] = resume_file_path
        # Получаем расширение файла из пути
        file_extension = os.path.splitext(resume_file_path)[1]
        student_data["resume_file_extension"] = file_extension

    db_student = Student(**student_data)
    db.add(db_student)
    await db.commit()
    await db.refresh(db_student)
    return db_student


async def update_student(
    db: AsyncSession,
    student_id: int,
    student_in: StudentUpdate,
) -> Student | None:
    """Обновить данные студента"""
    db_student = await get_student(db, student_id)
    if not db_student:
        return None

    update_data = student_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_student, field, value)

    await db.commit()
    await db.refresh(db_student)
    return db_student


async def bulk_update_status(
    db: AsyncSession, student_ids: list[int], status: ApplicationStatus
) -> int:
    """Массовое обновление статусов студентов"""
    result = await db.execute(select(Student).where(Student.id.in_(student_ids)))
    students = result.scalars().all()

    for student in students:
        student.status = status

    await db.commit()
    return len(students)


async def delete_student(db: AsyncSession, student_id: int) -> bool:
    """Удалить заявку студента"""
    db_student = await get_student(db, student_id)
    if not db_student:
        return False

    await db.delete(db_student)
    await db.commit()
    return True


async def get_students_by_vacancy(
    db: AsyncSession, vacancy_id: int, skip: int = 0, limit: int = 100
) -> list[Student]:
    """Получить всех студентов по вакансии"""
    return await get_students(db=db, skip=skip, limit=limit, vacancy_id=vacancy_id)


async def get_students_count_by_vacancy(db: AsyncSession, vacancy_id: int) -> int:
    """Получить количество заявок на вакансию"""
    result = await db.execute(select(Student).where(Student.vacancy_id == vacancy_id))
    return len(result.scalars().all())
