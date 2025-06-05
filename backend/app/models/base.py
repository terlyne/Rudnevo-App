from sqlalchemy.orm import (
    DeclarativeBase,
    declared_attr,
    Mapped,
)

from app.db.custom_types import int_pk


class Base(DeclarativeBase):
    """Базовая модель, которая хранит в себе метаданные."""
    id: Mapped[int_pk]

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"