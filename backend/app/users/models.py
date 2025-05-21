from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base, int_pk, str_uniq
from werkzeug.security import generate_password_hash, check_password_hash
from core.config import settings


# Модель таблицы пользователя
class User(Base):
    id: Mapped[int_pk]
    email: Mapped[str_uniq] = mapped_column(
        String(255)
    )  # Максимальное кол-во символов email - 255
    username: Mapped[str_uniq] = mapped_column(
        String(255)
    )  # Максимальное кол-во символов username - 255
    password: Mapped[str] = mapped_column(Text, nullable=False)

    def set_password(self, password: str) -> None:
        """Функция для сохранения хэшированного пароля в БД с использованием соли"""
        salted_password = f"{password}{settings.PASSWORD_SALT}"
        self.password = generate_password_hash(salted_password)

    def check_password(self, password: str) -> bool:
        """Функция для проверки соответствия принятого пароля с хэшированным паролем в БД"""
        salted_password = f"{password}{settings.PASSWORD_SALT}"
        return check_password_hash(self.password, salted_password)
