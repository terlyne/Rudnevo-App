import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Класс конфигурации приложения"""

    # Параметры для БД
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # Параметры для JWT токена
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Параметр для хранения пути к файлу .env
    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"
        )
    )

    # Соль для пароля
    PASSWORD_SALT: str

    # Параметры для отправки сообщений с приглашениями на регистрацию
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str


def get_db_url():
    """Функция для получения строки подключения к БД"""
    return f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"


settings = Settings()
