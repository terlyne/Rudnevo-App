from pydantic import BaseModel, Field
from typing import Optional
from fastapi import UploadFile


class ArticleBase(BaseModel):
    """Базовая схема статьи с общими полями"""

    title: str = Field(
        ..., min_length=1, max_length=255, description="Заголовок статьи"
    )
    content: str = Field(..., min_length=1, description="Содержимое статьи")
    is_hidden: bool = Field(default=False, description="Скрыта ли статья")


class ArticleCreate(ArticleBase):
    """Схема для создания статьи"""

    pass


class ArticleUpdate(BaseModel):
    """Схема для обновления статьи (все поля опциональны)"""

    title: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Заголовок статьи"
    )
    content: Optional[str] = Field(None, min_length=1, description="Содержимое статьи")
    is_hidden: Optional[bool] = Field(None, description="Скрыта ли статья")


class ArticleResponse(ArticleBase):
    """Схема для ответа API"""

    id: int

    class Config:
        from_attributes = True
