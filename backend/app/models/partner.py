from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from db.custom_types import (
    created_at,
    updated_at,
)


class Partner(Base):
    """Модель партнера"""

    __tablename__ = "partners"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at] 