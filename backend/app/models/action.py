from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from db.custom_types import (
    created_at,
    int_pk,
)


class Action(Base):
    """Модель событий"""

    __tablename__ = "actions"

    username: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[created_at]
