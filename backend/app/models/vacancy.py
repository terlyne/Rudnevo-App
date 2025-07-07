from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Vacancy(Base):
    """Модель вакансии"""

    __tablename__ = "vacancies"

    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    direction: Mapped[str] = mapped_column(String(100))
    speciality: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str] = mapped_column(Text)  # Требования
    work_format: Mapped[str] = mapped_column(String(50))
    start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # Опциональная дата начала
    end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # Опциональная дата окончания
    chart: Mapped[str] = mapped_column(Text)  # График стажировки
    company_name: Mapped[str] = mapped_column(String(200))  # Название компании
    contact_person: Mapped[str] = mapped_column(
        String(200)
    )  # Контактное лицо от компании
    is_hidden: Mapped[bool] = mapped_column(default=False)
    required_amount: Mapped[int]  # Нужное кол-во студентов
    
    # Новые поля для вакансий
    salary_from: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Зарплата от
    salary_to: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Зарплата до
    address: Mapped[str | None] = mapped_column(Text, nullable=True)  # Адрес
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Город
    metro_station: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Станция метро
    is_internship: Mapped[bool] = mapped_column(default=False)  # Флаг стажировки

    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    recruiter: Mapped["User"] = relationship("User", back_populates="vacancies")
    applications: Mapped[list["Student"]] = relationship(
        "Student", back_populates="vacancy"
    )
