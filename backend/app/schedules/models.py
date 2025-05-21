from sqlalchemy import Text, String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import date, datetime

from core.database import Base, int_pk, str_null_false


# Модель для отдельной строки расписания
class Schedule(Base):
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    shift_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    college_name: Mapped[str] = mapped_column(String(255), nullable=False)
    room_number: Mapped[str_null_false] = mapped_column(String(50))
    start_date: Mapped[date]
    end_date: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
