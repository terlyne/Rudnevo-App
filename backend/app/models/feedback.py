from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.db.custom_types import created_at


class Feedback(Base):
    """Модель обратной связи"""

    __tablename__ = "feedbacks"

    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))
    message: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[created_at]
