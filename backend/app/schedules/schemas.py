from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class ScheduleBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=255, description="Название расписания"
    )
    shift_number: int = Field(..., ge=1, le=2, description="Номер смены (1 или 2)")
    description: Optional[str] = Field(None, description="Описание расписания")
    college_name: str = Field(
        ..., min_length=1, max_length=255, description="Название колледжа"
    )
    room_number: str = Field(
        ..., min_length=1, max_length=50, description="Номер аудитории"
    )
    start_date: date = Field(..., description="Дата начала")
    end_date: date = Field(..., description="Дата окончания")


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(ScheduleBase):
    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Название расписания"
    )
    shift_number: Optional[int] = Field(
        None, ge=1, le=2, description="Номер смены (1 или 2)"
    )
    description: Optional[str] = Field(None, description="Описание расписания")
    college_name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Название колледжа"
    )
    room_number: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Номер аудитории"
    )
    start_date: Optional[date] = Field(None, description="Дата начала")
    end_date: Optional[date] = Field(None, description="Дата окончания")


class ScheduleResponse(ScheduleBase):
    id: int

    class Config:
        from_attributes = True
