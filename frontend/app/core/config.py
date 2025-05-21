import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    # URL нашего API
    BACKEND_URL: str


    # Параметр для хранения пути к файлу .env
    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"
        )
    )

settings = Config()