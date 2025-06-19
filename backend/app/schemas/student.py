from datetime import date
from pydantic import BaseModel, ConfigDict, Field

from app.models.student import ApplicationStatus


class StudentBase(BaseModel):
    """Базовая схема студента"""

    full_name: str = Field(max_length=200)
    birth_date: date
    speciality: str = Field(max_length=200)
    phone: str = Field(max_length=20)
    resume_link: str | None = Field(None, max_length=500)
    resume_file: str | None = Field(None, max_length=500)


class StudentCreate(BaseModel):
    """Схема создания заявки студента"""

    full_name: str = Field(max_length=200)
    birth_date: date
    speciality: str = Field(max_length=200)
    phone: str = Field(max_length=20)
    resume_link: str | None = Field(None, max_length=500)
    vacancy_id: int

    model_config = ConfigDict(extra="ignore")


class StudentUpdate(BaseModel):
    """Схема обновления студента"""

    full_name: str | None = Field(None, max_length=200)
    birth_date: date | None = None
    speciality: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=20)
    resume_link: str | None = Field(None, max_length=500)
    resume_file: str | None = Field(None, max_length=500)
    status: ApplicationStatus | None = None


class StudentResponse(StudentBase):
    """Схема студента из БД"""

    id: int
    status: ApplicationStatus
    vacancy_id: int


class StudentBulkStatusUpdate(BaseModel):
    """Схема массового обновления статусов"""

    student_ids: list[int]
    status: ApplicationStatus
