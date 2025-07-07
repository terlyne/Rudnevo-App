from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from models.base import Base
from db.custom_types import str_uniq


class User(Base):
    """Модель пользователя"""

    __tablename__ = "users"

    email: Mapped[str_uniq] = mapped_column(String(100), index=True)
    username: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )
    hashed_password: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_registered: Mapped[bool] = mapped_column(default=False)
    is_recruiter: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    vacancies: Mapped[list["Vacancy"]] = relationship(
        "Vacancy", back_populates="recruiter"
    )
