from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from core.database import async_session_maker
from users.dependencies import authenticate_user_by_token
from schedules import crud
from schedules.schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("/", response_model=List[ScheduleResponse])
async def get_schedules(skip: int = 0, limit: int = 100):
    async with async_session_maker() as session:
        schedules = await crud.get_schedules(session, skip=skip, limit=limit)
        return schedules


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int):
    async with async_session_maker() as session:
        schedule = await crud.get_schedule(session, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return schedule


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule: ScheduleCreate, current_user=Depends(authenticate_user_by_token)
):
    async with async_session_maker() as session:
        return await crud.create_schedule(session, schedule)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule: ScheduleUpdate,
    current_user=Depends(authenticate_user_by_token),
):
    async with async_session_maker() as session:
        updated_schedule = await crud.update_schedule(session, schedule_id, schedule)
        if not updated_schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return updated_schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int, current_user=Depends(authenticate_user_by_token)
):
    async with async_session_maker() as session:
        if not await crud.delete_schedule(session, schedule_id):
            raise HTTPException(status_code=404, detail="Schedule not found")


@router.patch("/{schedule_id}/toggle-visibility", response_model=ScheduleResponse)
async def toggle_schedule_visibility(
    schedule_id: int, current_user=Depends(authenticate_user_by_token)
):
    async with async_session_maker() as session:
        schedule = await crud.toggle_schedule_visibility(session, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return schedule
