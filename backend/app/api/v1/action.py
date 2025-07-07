from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud import action as action_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.action import ActionCreate, ActionResponse


router = APIRouter()


@router.get("/", response_model=list[ActionResponse])
async def read_last_actions(
    db: AsyncSession = Depends(get_async_session),
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
):
    """Получить список последних событий"""
    return await action_crud.get_actions(db, limit=limit)


@router.post("/", response_model=ActionResponse)
async def create_action(
    action_in: ActionCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Создать новое событие"""
    return await action_crud.create_action(db=db, action_in=action_in)
