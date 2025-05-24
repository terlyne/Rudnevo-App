from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base, int_pk, str_uniq
from werkzeug.security import generate_password_hash, check_password_hash
from core.config import settings


# Модель таблицы пользователя
class User(Base):
    id: Mapped[int_pk]
    email: Mapped[str_uniq] = mapped_column(
        Text
    )
    username: Mapped[str_uniq] = mapped_column(
        Text
    )
    password: Mapped[str] = mapped_column(Text)
    # Поле для того, чтобы установить зарегистрирован пользователь или нет (Админ добавляет пользователя, а потом пользователь регистрируется перейдя по адресу в письме отправленному ему на электроннцю почту)
    is_registered: Mapped[bool] = mapped_column(nullable=False, server_default=False)


    def set_password(self, password: str) -> None:
        """Функция для сохранения хэшированного пароля в БД с использованием соли"""
        salted_password = f"{password}{settings.PASSWORD_SALT}"
        self.password = generate_password_hash(salted_password)

    def check_password(self, password: str) -> bool:
        """Функция для проверки соответствия принятого пароля с хэшированным паролем в БД"""
        salted_password = f"{password}{settings.PASSWORD_SALT}"
        return check_password_hash(self.password, salted_password)
