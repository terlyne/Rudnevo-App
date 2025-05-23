from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base, int_pk, str_null_false


# Модель таблицы вопроса
class Question(Base):
    id: Mapped[int_pk]
    name: Mapped[str_null_false] = mapped_column(Text)
    email: Mapped[str_null_false] = mapped_column(Text)
    question: Mapped[str_null_false] = mapped_column(Text)