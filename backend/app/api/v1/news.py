from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import os

from app.api.deps import get_current_active_user
from app.crud import news as news_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.news import NewsCreate, NewsUpdate, NewsInDB
from app.utils.files import save_image
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=list[NewsInDB])
async def read_news(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Получить список новостей"""
    # Для администраторов показываем все новости (включая скрытые)
    show_hidden = current_user.is_superuser
    return await news_crud.get_news_list(
        db, skip=skip, limit=limit, show_hidden=show_hidden
    )


@router.get("/hidden", response_model=list[NewsInDB])
async def read_hidden_news(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Получить список скрытых новостей (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )

    return await news_crud.get_news_list(db, skip=skip, limit=limit, show_hidden=True)


@router.get("/{news_id}", response_model=NewsInDB)
async def get_news_by_id(news_id: int, db: AsyncSession = Depends(get_async_session)):
    """Получить новость по ID"""
    news = await news_crud.get_news(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )
    return news


@router.post("/", response_model=NewsInDB)
async def create_news_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    title: str = Form(...),
    content: str = Form(...),
    is_hidden: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user)
):
    """Создать новость с возможностью загрузки изображения (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )

    # Сохраняем изображение, если оно предоставлено
    image_url = None
    if image:
        image_url = await save_image(image, "news")

    news_in = NewsCreate(
        title=title, content=content, image_url=image_url, is_hidden=is_hidden
    )

    return await news_crud.create_news(db=db, news_in=news_in)


@router.put("/{news_id}", response_model=NewsInDB)
async def update_news_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    news_id: int,
    title: str = Form(None),
    content: str = Form(None),
    is_hidden: bool = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user)
):
    """Обновить новость с возможностью обновления изображения (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )

    # Сохраняем новое изображение, если оно предоставлено
    image_url = None
    if image:
        image_url = await save_image(image, "news")

    news_update = NewsUpdate(
        title=title, content=content, image_url=image_url, is_hidden=is_hidden
    )

    news = await news_crud.update_news(db=db, news_id=news_id, news_in=news_update)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )
    return news


@router.delete("/{news_id}")
async def delete_news_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    news_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Удалить новость (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )
    if not await news_crud.delete_news(db=db, news_id=news_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )
    return {"ok": True}


@router.post("/{news_id}/toggle-visibility", response_model=NewsInDB)
async def toggle_news_visibility(
    *,
    db: AsyncSession = Depends(get_async_session),
    news_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Переключить видимость новости (только для администраторов)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на выполнение данного функционала.",
        )
    news = await news_crud.toggle_news_visibility(db=db, news_id=news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена."
        )
    return news


@router.get("/{news_id}/image")
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
