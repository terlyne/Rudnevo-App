from datetime import datetime
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Vacancy(Base):
    """Модель вакансии"""
    __tablename__ = "vacancies"

    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    direction: Mapped[str] = mapped_column(String(100))
    speciality: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str] = mapped_column(Text) # Требования
    work_format: Mapped[str] = mapped_column(String(50))
    start: Mapped[datetime]
    end: Mapped[datetime]
    chart: Mapped[str] = mapped_column(Text) # График стажировки
    contact_person: Mapped[str] = mapped_column(String(200)) # Контактное лицо от компании
    is_hidden: Mapped[bool] = mapped_column(default=False)
    required_amount: Mapped[int] # Нужное кол-во студентов
    
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    recruiter: Mapped["User"] = relationship("User", back_populates="vacancies")
    applications: Mapped[list["Student"]] = relationship("Student", back_populates="vacancy")