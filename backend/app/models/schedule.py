from datetime import date
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.db.custom_types import str_null_false


class Schedule(Base):
    """Модель расписания"""

    __tablename__ = "schedules"

    title: Mapped[str] = mapped_column(String(200))
    shift_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    college_name: Mapped[str] = mapped_column(String(255), nullable=False)
    room_number: Mapped[str_null_false] = mapped_column(String(50))
    start_date: Mapped[date]
    end_date: Mapped[date]
