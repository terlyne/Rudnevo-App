from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News
from app.schemas.news import NewsCreate, NewsUpdate


async def get_news_list(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    show_hidden: bool = False
) -> list[News]:
    """Получить список новостей"""
    query = select(News)
    
    if not show_hidden:
        query = query.where(News.is_hidden == False)
    
    result = await db.execute(
        query
        .order_by(News.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_news(db: AsyncSession, news_id: int) -> News | None:
    """Получить новость по ID"""
    result = await db.execute(select(News).where(News.id == news_id))
    return result.scalar_one_or_none()


async def create_news(db: AsyncSession, news_in: NewsCreate) -> News:
    """Создать новость"""
    db_news = News(**news_in.model_dump())
    db.add(db_news)
    await db.commit()
    await db.refresh(db_news)
    return db_news


async def update_news(
    db: AsyncSession,
    news_id: int,
    news_in: NewsUpdate
) -> News | None:
    """Обновить новость"""
    db_news = await get_news(db, news_id)
    if not db_news:
        return None

    update_data = news_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_news, field, value)

    await db.commit()
    await db.refresh(db_news)
    return db_news


async def delete_news(db: AsyncSession, news_id: int) -> bool:
    """Удалить новость"""
    db_news = await get_news(db, news_id)
    if not db_news:
        return False

    await db.delete(db_news)
    await db.commit()
    return True


async def toggle_news_visibility(db: AsyncSession, news_id: int) -> News | None:
    """Переключить видимость новости"""
    db_news = await get_news(db, news_id)
    if not db_news:
        return None
    
    db_news.is_hidden = not db_news.is_hidden
    await db.commit()
    await db.refresh(db_news)
    return db_news