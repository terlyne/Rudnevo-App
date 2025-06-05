from datetime import datetime
from pydantic import BaseModel, EmailStr


class ReviewBase(BaseModel):
    """Базовая схема отзыва"""
    name: str
    email: EmailStr
    review: str


class ReviewCreate(ReviewBase):
    """Схема создания отзыва"""
    pass


class ReviewInDB(ReviewBase):
    """Схема отзыва из БД"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
