from sqlalchemy.future import select
from core.database import async_session_maker
from articles.models import Article
from articles.schemas import ArticleCreate, ArticleUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from fastapi import UploadFile


async def get_all_articles():
    """Получение всех новостей"""
    async with async_session_maker() as session:
        result = await session.execute(select(Article))
        articles = result.scalars().all()

        return articles


async def get_article_by_id(article_id: int):
    """Получение новости по ID"""
    async with async_session_maker() as session:
        stmt = select(Article).where(Article.id == article_id)
        result = await session.execute(stmt)
        article = result.scalar_one_or_none()

        return article


async def get_article_image(session: AsyncSession, article_id: int) -> Optional[bytes]:
    """Получение изображения статьи"""
    article = await get_article(session, article_id)
    if not article or not article.image_data:
        return None
    return article.image_data


async def get_articles(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Article]:
    """Получение списка статей с пагинацией"""
    result = await session.execute(select(Article).offset(skip).limit(limit))
    return result.scalars().all()


async def get_article(session: AsyncSession, article_id: int) -> Optional[Article]:
    """Получение статьи по ID"""
    result = await session.execute(select(Article).where(Article.id == article_id))
    return result.scalar_one_or_none()


async def create_article(
    session: AsyncSession, article: ArticleCreate, image: Optional[UploadFile] = None
) -> Article:
    """Создание новой статьи"""
    image_data = None
    if image:
        image_data = await image.read()

    db_article = Article(
        title=article.title,
        content=article.content,
        image_data=image_data,
        is_hidden=article.is_hidden,
    )

    session.add(db_article)
    await session.commit()
    await session.refresh(db_article)
    return db_article


async def update_article(
    session: AsyncSession,
    article_id: int,
    article: ArticleUpdate,
    image: Optional[UploadFile] = None,
) -> Optional[Article]:
    """Обновление статьи"""
    db_article = await get_article(session, article_id)
    if not db_article:
        return None

    update_data = article.model_dump(exclude_unset=True)

    if image:
        update_data["image_data"] = await image.read()

    for key, value in update_data.items():
        setattr(db_article, key, value)

    await session.commit()
    await session.refresh(db_article)
    return db_article


async def delete_article(session: AsyncSession, article_id: int) -> bool:
    """Удаление статьи"""
    article = await get_article(session, article_id)
    if not article:
        return False

    await session.delete(article)
    await session.commit()
    return True


async def toggle_article_visibility(
    session: AsyncSession, article_id: int
) -> Optional[Article]:
    """Переключение видимости статьи"""
    article = await get_article(session, article_id)
    if not article:
        return None

    article.is_hidden = not article.is_hidden
    await session.commit()
    await session.refresh(article)
    return article
