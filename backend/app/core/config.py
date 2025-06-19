from typing import Any
from pydantic import PostgresDsn, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    # Основные настройки
    PROJECT_NAME: str = "Rudnevo API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SERVER_HOST: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5000"
    
    # Настройки администратора
    ADMIN_EMAIL: EmailStr = "sheyynovd@gmail.com"
    
    # Настройки базы данных
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "rudnevo_db"
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None
    DB_ECHO: bool = False

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
            path=values.get('POSTGRES_DB') or ''
        )

    # Настройки JWT
    SECRET_KEY: str = "your-secret-key-for-jwt-here" # Изменить при деплое!!!!!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # Настройки почты
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = True
    
    # Настройки медиафайлов
    MEDIA_ROOT: Path = Path("media")
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB для файлов резюме
    ALLOWED_IMAGE_TYPES: set[str] = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp"
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
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


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
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()
