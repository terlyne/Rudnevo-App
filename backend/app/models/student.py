from datetime import date
from sqlalchemy import String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base


class ApplicationStatus(str, enum.Enum):
    """Статусы заявок студентов"""
    NEW = "new"  # Новая
    IN_REVIEW = "in_review"  # В рассмотрении
    INVITED = "invited"  # Приглашён
    REJECTED = "rejected"  # Отказ


class Student(Base):
    """Модель студента для откликов на вакансии"""
    __tablename__ = "students"

    full_name: Mapped[str] = mapped_column(String(200))
    birth_date: Mapped[date]
    speciality: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(20))
    resume_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume_file: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Путь к файлу
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), 
        default=ApplicationStatus.NEW
    )
    
    # Связь с вакансией
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id"))
    vacancy: Mapped["Vacancy"] = relationship("Vacancy", back_populates="applications") 