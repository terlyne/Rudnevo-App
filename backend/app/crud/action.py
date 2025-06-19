from datetime import datetime
from sqlalchemy import select, desc, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action
from app.schemas.action import ActionCreate 



async def get_actions(
    db: AsyncSession,
    limit: int = 10
) -> list[Action]:
    """Получить последние N событий (по умолчанию 10)"""
    result = await db.execute(
        select(Action)
        .order_by(desc(Action.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def create_action(
    db: AsyncSession,
    action_in: ActionCreate
) -> Action:
    """Создание события"""
    action_db = Action(**action_in.model_dump())
    db.add(action_db)
    await db.commit()
    await db.refresh(action_db)
    return action_db


async def delete_actions(db: AsyncSession) -> bool:
    """Удалить все события кроме последних 10 (если есть хотя бы 10 событий)"""
    last_actions = await get_actions(db, limit=10)
    
    if len(last_actions) < 10:
        return False
    
    last_action_ids = [action.id for action in last_actions]

    await db.execute(
        delete(Action)
        .where(Action.id.not_in(last_action_ids))
    )
    await db.commit()
    return True