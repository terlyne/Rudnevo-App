from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class ReviewBase(BaseModel):
    """Базовая схема отзыва"""

    name: str
    email: EmailStr
    review: str
    is_hidden: bool = True


class ReviewCreate(ReviewBase):
    """Схема создания отзыва"""

    pass

    model_config = ConfigDict(extra="ignore")


class ReviewUpdate(BaseModel):
    """Схема обновления отзыва (только состояние)"""

    is_hidden: bool


class ReviewInDB(ReviewBase):
    """Схема отзыва из БД"""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True
