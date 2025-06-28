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
    start: date | None = None
    end: date | None = None
    chart: str
    company_name: str = Field(max_length=200)
    contact_person: str = Field(max_length=200)
    is_hidden: bool = False
    required_amount: int
    
    salary_from: int | None = None
    salary_to: int | None = None
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    metro_station: str | None = Field(None, max_length=100)
    is_internship: bool = False


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
    company_name: str | None = Field(None, max_length=200)
    contact_person: str | None = Field(None, max_length=200)
    is_hidden: bool | None = None
    required_amount: int | None = None
    recruiter_id: int | None = None
    
    salary_from: int | None = None
    salary_to: int | None = None
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    metro_station: str | None = Field(None, max_length=100)
    is_internship: bool | None = None


class VacancyResponse(VacancyBase):
    """Схема вакансии из БД"""

    id: int
    recruiter_id: int
