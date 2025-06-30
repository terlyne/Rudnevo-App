from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class ReviewBase(BaseModel):
    """Базовая схема отзыва"""

    name: str
    email: EmailStr
    review: str
    is_approved: bool = False


class ReviewCreate(ReviewBase):
    """Схема создания отзыва"""

    pass

    model_config = ConfigDict(extra="ignore")


class ReviewUpdate(BaseModel):
    """Схема обновления отзыва (только состояние)"""

    name: str | None = None
    email: EmailStr | None = None
    review: str | None = None
    is_approved: bool | None = None


class ReviewInDB(ReviewBase):
    """Схема отзыва из БД"""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True
