from datetime import date
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


class ScheduleUpdate(BaseModel):
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
