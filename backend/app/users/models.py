from sqlalchemy import Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base, int_pk, str_uniq
from werkzeug.security import generate_password_hash, check_password_hash
from core.config import settings
from enum import Enum
from typing import Optional
from datetime import datetime


# Перечисление для роли пользователя в системе
class UserRole(Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"


# Модель таблицы пользователя
class User(Base):
    id: Mapped[int_pk]
    email: Mapped[str_uniq] = mapped_column(
        Text
    )
    username: Mapped[str_uniq] = mapped_column(
        Text, nullable=True,
    )
    password: Mapped[str] = mapped_column(Text, nullable=True)
    role: Mapped[UserRole] = mapped_column(SQLAlchemyEnum(UserRole), default=UserRole.ADMIN)
    # Поле для того, чтобы установить зарегистрирован пользователь или нет (Админ добавляет пользователя, а потом пользователь регистрируется перейдя по адресу в письме отправленному ему на электронную почту)
    is_registered: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    registration_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires: Mapped[Optional[datetime]] = mapped_column(nullable=True)


    def set_password(self, password: str) -> None:
        """Функция для сохранения хэшированного пароля в БД с использованием соли"""
        salted_password = f"{password}{settings.PASSWORD_SALT}"
        self.password = generate_password_hash(salted_password)

    def check_password(self, password: str) -> bool:
        """Функция для проверки соответствия принятого пароля с хэшированным паролем в БД"""
        salted_password = f"{password}{settings.PASSWORD_SALT}"
        return check_password_hash(self.password, salted_password)
