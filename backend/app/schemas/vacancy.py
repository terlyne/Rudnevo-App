from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class VacancyBase(BaseModel):
    """Базовая схема вакансии"""

    title: str
    description: str
    direction: str = Field(max_length=100)
    speciality: str
    requirements: str
    work_format: str = Field(max_length=50)
    start: date
    end: date
    chart: str
    contact_person: str = Field(max_length=200)
    is_hidden: bool = False
    required_amount: int


class VacancyCreate(VacancyBase):
    """Схема создания вакансии"""

    pass


class VacancyUpdate(BaseModel):
    """Схема обновления вакансии"""

    title: str | None = None
    description: str | None = None
    direction: str | None = Field(None, max_length=100)
    speciality: str | None = None
    requirements: str | None = None
    work_format: str | None = Field(None, max_length=50)
    start: date | None = None
    end: date | None = None
    chart: str | None = None
    contact_person: str | None = Field(None, max_length=200)
    is_hidden: bool | None = None
    required_amount: int | None = None
    recruiter_id: int | None = None


class VacancyResponse(VacancyBase):
    """Схема вакансии из БД"""

    id: int
    recruiter_id: int
