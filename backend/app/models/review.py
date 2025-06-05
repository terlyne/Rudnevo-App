from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.db.custom_types import (
    created_at
)

class Review(Base):
    """Модель отзыва"""
    __tablename__ = "reviews"

    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))
    review: Mapped[str] = mapped_column(Text)
    rating: Mapped[int] = mapped_column(default=5)
    created_at: Mapped[created_at]