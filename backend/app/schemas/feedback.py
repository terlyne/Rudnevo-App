from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class FeedbackBase(BaseModel):
    """Базовая схема обратной связи"""
    name: str
    email: EmailStr
    message: str

class FeedbackCreate(FeedbackBase):
    """Схема создания обратной связи"""
    pass

class FeedbackResponse(BaseModel):
    """Схема ответа на обратную связь"""
    response_text: str

class FeedbackInDB(FeedbackBase):
    """Схема обратной связи из БД"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True