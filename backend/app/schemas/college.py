from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CollegeBase(BaseModel):
    """Базовая схема колледжа"""

    name: str
    image_url: str


class CollegeCreate(CollegeBase):
    """Схема создания колледжа"""

    pass


class CollegeUpdate(BaseModel):
    """Схема обновления колледжа"""

    name: str | None = None
    image_url: str | None = None


class CollegeInDB(CollegeBase):
    """Схема колледжа из БД"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 