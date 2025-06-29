from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_URL: str
    # Секретный ключ Flask приложения
    SECRET_KEY: str
    # Настройки для обновления токенов
    AUTO_REFRESH_TOKENS: bool
    REFRESH_TOKEN_EXPIRE_DAYS: int

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


settings = Settings()
