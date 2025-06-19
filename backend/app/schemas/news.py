from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NewsBase(BaseModel):
    """Базовая схема новости"""

    title: str
    content: str
    image_url: str | None = None
    is_hidden: bool = False


class NewsCreate(NewsBase):
    """Схема создания новости"""

    pass


class NewsUpdate(BaseModel):
    """Схема обновления новости"""

    title: str | None = None
    content: str | None = None
    image_url: str | None = None
    is_hidden: bool | None = None


class NewsInDB(NewsBase):
    """Схема новости из БД"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
