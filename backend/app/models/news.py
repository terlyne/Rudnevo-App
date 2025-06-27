from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.db.custom_types import (
    created_at,
    updated_at,
)


class News(Base):
    """Модель новости"""

    __tablename__ = "news"

    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_hidden: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
