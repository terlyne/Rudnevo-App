from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from db.custom_types import (
    created_at,
    updated_at,
)


class College(Base):
    """Модель колледжа"""

    __tablename__ = "colleges"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at] 