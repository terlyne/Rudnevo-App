from typing import Any
from pydantic import PostgresDsn, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    # Основные настройки
    PROJECT_NAME: str
    VERSION: str
    API_V1_STR: str
    SERVER_HOST: str
    FRONTEND_URL: str

    # Настройки администратора
    ADMIN_EMAIL: EmailStr

    # Настройки базы данных
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None
    DB_ECHO: bool

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: str | None, info: Any) -> Any:
        if isinstance(v, str):
            return v

        values = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=values.get("POSTGRES_DB") or "",
        )

    # Настройки JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Настройки почты
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    MAIL_USE_CREDENTIALS: bool
    MAIL_VALIDATE_CERTS: bool

    # Настройки медиафайлов
    MEDIA_ROOT: Path = Path("media")
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB для файлов резюме
    ALLOWED_IMAGE_TYPES: set[str] = {
        "image/jpeg",
        "image/jpg",
        "image/pjpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/octet-stream",
    }
    ALLOWED_RESUME_TYPES: set[str] = {
        # PDF документы
        "application/pdf",
        # Microsoft Office документы
        "application/msword",  # .doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/vnd.ms-excel",  # .xls
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-powerpoint",  # .ppt
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
        # Текстовые форматы
        "text/plain",  # .txt
        "text/rtf",  # .rtf
        "text/html",  # .html, .htm
        "text/markdown",  # .md
        # OpenDocument форматы
        "application/vnd.oasis.opendocument.text",  # .odt
        "application/vnd.oasis.opendocument.spreadsheet",  # .ods
        "application/vnd.oasis.opendocument.presentation",  # .odp
        # Другие популярные форматы
        "application/rtf",  # .rtf (альтернативный MIME тип)
        "application/x-rtf",  # .rtf (еще один альтернативный MIME тип)
    }

    # CORS
    CORS_ORIGINS: list[str]

    @field_validator("SQLALCHEMY_DATABASE_URI")
    def validate_database_url(cls, v: str | None) -> str:
        if not v:
            raise ValueError("Database URL is required")
        return str(v)  # Ensure we return a string

    @field_validator("SECRET_KEY")
    def validate_secret_key(cls, v: str | None) -> str:
        if not v:
            raise ValueError("Secret key is required")
        if len(v) < 32:
            raise ValueError("Secret key should be at least 32 characters long")
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


settings = Settings()
