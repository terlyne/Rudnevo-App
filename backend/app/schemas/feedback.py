from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class FeedbackBase(BaseModel):
    """Базовая схема обратной связи"""

    name: str
    email: EmailStr
    message: str
    is_hidden: bool = False


class FeedbackCreate(FeedbackBase):
    """Схема создания обратной связи"""

    pass


class FeedbackUpdate(BaseModel):
    """Схема обновления обратной связи"""

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    message: Optional[str] = None
    is_hidden: Optional[bool] = None


class FeedbackResponse(BaseModel):
    """Схема ответа на обратную связь"""

    response_text: str


class FeedbackInDB(FeedbackBase):
    """Схема обратной связи из БД"""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True
