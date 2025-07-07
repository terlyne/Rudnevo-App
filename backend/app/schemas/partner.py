from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PartnerBase(BaseModel):
    """Базовая схема партнера"""

    name: str
    description: str | None = None
    image_url: str | None = None
    is_active: bool = True


class PartnerCreate(PartnerBase):
    """Схема создания партнера"""

    pass


class PartnerUpdate(BaseModel):
    """Схема обновления партнера"""

    name: str | None = None
    description: str | None = None
    image_url: str | None = None
    is_active: bool | None = None


class PartnerInDB(PartnerBase):
    """Схема партнера из БД"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 