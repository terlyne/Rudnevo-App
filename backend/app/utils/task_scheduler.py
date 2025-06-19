import asyncio
from typing import Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession


async def run_periodic_task(
    db: AsyncSession,
    task_func: Callable[[AsyncSession], Awaitable[None]],
    interval_seconds: int = 60 * 60 * 24 * 7,
):
    """Запускает задачу периодически с указанным интервалом"""
    while True:
        await asyncio.sleep(interval_seconds)
        await task_func(db)


async def actions_weekly_cleanup(db: AsyncSession):
    """Запускает еженедельную очистку"""
    from app.crud.action import delete_actions

    await run_periodic_task(db, delete_actions)
