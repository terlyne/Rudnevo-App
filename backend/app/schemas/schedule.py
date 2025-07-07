from datetime import date
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict


class ScheduleBase(BaseModel):
    """Базовая схема расписания"""

    title: str
    shift_number: int
    description: str | None = None
    college_name: str
    room_number: str
    start_date: date
    end_date: date


class ScheduleCreate(ScheduleBase):
    """Схема создания расписания"""

    pass


class ScheduleUpdate(ScheduleBase):
    """Схема обновления расписания"""

    title: str | None = None
    shift_number: int | None = None
    description: str | None = None
    college_name: str | None = None
    room_number: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ScheduleInDB(ScheduleBase):
    """Схема расписания из БД"""

    id: int

    model_config = ConfigDict(from_attributes=True)


class ScheduleTemplateBase(BaseModel):
    college_id: int
    college_name: str
    schedule_data: Dict[str, Any]
    is_active: bool = True


class ScheduleTemplateCreate(ScheduleTemplateBase):
    pass


class ScheduleTemplateUpdate(ScheduleTemplateBase):
    college_id: int | None = None
    college_name: str | None = None
    schedule_data: Dict[str, Any] | None = None
    is_active: bool | None = None


class ScheduleTemplateInDB(ScheduleTemplateBase):
    id: int
    html_content: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ScheduleUploadResponse(BaseModel):
    status: str
    data: list[dict[str, Any]]
