from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Optional
import os

from app.api.deps import get_current_admin_or_superuser, get_current_user_optional
from app.crud import news as news_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.news import NewsCreate, NewsUpdate, NewsInDB
from app.utils.files import save_image
from app.core.config import settings

# Публичный роутер для открытых эндпоинтов
public_router = APIRouter()

# Административный роутер для закрытых эндпоинтов
admin_router = APIRouter()


# === ПУБЛИЧНЫЕ ЭНДПОИНТЫ ===

@public_router.get("/", response_model=list[NewsInDB])
async def read_public_news(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
):
    """Получить список публичных новостей (открытый эндпоинт)"""
    return await news_crud.get_news_list(db, skip=skip, limit=limit, show_hidden=False)


@public_router.get("/{news_id}", response_model=NewsInDB)
async def get_public_news_by_id(news_id: int, db: AsyncSession = Depends(get_async_session)):
    """Получить публичную новость по ID"""
    news = await news_crud.get_news(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )
    if news.is_hidden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )
    return news


@public_router.get("/{news_id}/image")
async def get_news_image(news_id: int, db: AsyncSession = Depends(get_async_session)):
    """Получить изображение новости по ID"""
    news = await news_crud.get_news(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )

    if not news.image_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="У новости нет изображения."
        )

    # Получаем путь к файлу из URL
    # URL имеет формат /media/news/filename.ext
    image_path = os.path.join(settings.MEDIA_ROOT, news.image_url.lstrip("/media/"))

    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Изображение не найдено."
        )

    return FileResponse(image_path)


# === АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ ===

@admin_router.get("/", response_model=list[NewsInDB])
async def read_all_news(
    skip: int = 0,
    limit: int = 100,
    show_hidden: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Получить список всех новостей (включая скрытые) - только для администраторов"""
    return await news_crud.get_news_list(db, skip=skip, limit=limit, show_hidden=show_hidden)


@admin_router.get("/{news_id}", response_model=NewsInDB)
async def get_news_by_id_admin(news_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_admin_or_superuser)):
    """Получить новость по ID (включая скрытые) - только для администраторов"""
    news = await news_crud.get_news(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )
    return news


@admin_router.post("/", response_model=NewsInDB)
async def create_news_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    title: str = Form(...),
    content: str = Form(...),
    is_hidden: bool = Form(False),
    image: Union[UploadFile, None, str] = File(None),
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Создать новость с возможностью загрузки изображения (только для администраторов)"""
    if isinstance(image, str) and image == "":
        image = None
    
    # Сохраняем изображение, если оно предоставлено
    image_url = None
    if image:
        image_url = await save_image(image, "news")

    news_in = NewsCreate(
        title=title, content=content, image_url=image_url, is_hidden=is_hidden
    )

    return await news_crud.create_news(db=db, news_in=news_in)


@admin_router.put("/{news_id}", response_model=NewsInDB)
async def update_news_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    news_id: int,
    title: str = Form(None),
    content: str = Form(None),
    is_hidden: bool = Form(None),
    image: UploadFile | None = File(None),
    remove_image: str = Form(None),
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Обновить новость с возможностью обновления изображения (только для администраторов)"""
    # Сохраняем новое изображение, если оно предоставлено
    image_url = None
    if image:
        image_url = await save_image(image, "news")
    elif remove_image == "true":
        image_url = None

    news_update = NewsUpdate(
        title=title, content=content, image_url=image_url, is_hidden=is_hidden
    )

    news = await news_crud.update_news(db=db, news_id=news_id, news_in=news_update)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )
    return news


@admin_router.delete("/{news_id}")
async def delete_news_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    news_id: int,
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Удалить новость (только для администраторов)"""
    if not await news_crud.delete_news(db=db, news_id=news_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )
    return {"ok": True}


@admin_router.post("/{news_id}/toggle-visibility", response_model=NewsInDB)
async def toggle_news_visibility(
    *,
    db: AsyncSession = Depends(get_async_session),
    news_id: int,
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Переключить видимость новости (только для администраторов)"""
    news = await news_crud.toggle_news_visibility(db=db, news_id=news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )
    return news
