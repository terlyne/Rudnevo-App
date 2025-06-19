from datetime import datetime
from pydantic import BaseModel, EmailStr


class ActionBase(BaseModel):
    """Базовая схема события"""

    username: str
    action: str


class ActionCreate(ActionBase):
    """Схема создания события"""

    pass


class ActionResponse(ActionBase):
    """Схема ответа события"""

    created_at: datetime


class ActionInDB(ActionBase):
    """Схема события из БД"""

    id: int

    class Config:
        from_attributes = True
