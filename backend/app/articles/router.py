from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Response,
)
from typing import List, Optional
from core.database import async_session_maker
from users.dependencies import authenticate_user_by_token
from articles import crud
from articles.schemas import ArticleCreate, ArticleUpdate, ArticleResponse

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/", response_model=List[ArticleResponse])
async def get_articles(skip: int = 0, limit: int = 100):
    """Получение списка статей с пагинацией"""
    async with async_session_maker() as session:
        articles = await crud.get_articles(session, skip=skip, limit=limit)
        return articles


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int):
    """Получение статьи по ID"""
    async with async_session_maker() as session:
        article = await crud.get_article(session, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article


@router.get("/{article_id}/image")
async def get_article_image(article_id: int):
    """Получение изображения статьи"""
    async with async_session_maker() as session:
        article = await crud.get_article(session, article_id)
        if not article or not article.image_data:
            raise HTTPException(status_code=404, detail="Image not found")

        content_type = "image/jpeg"
        if article.image_data.startswith(b"\x89PNG\r\n\x1a\n"):
            content_type = "image/png"
        elif article.image_data.startswith(b"GIF87a") or article.image_data.startswith(
            b"GIF89a"
        ):
            content_type = "image/gif"

        return Response(content=article.image_data, media_type=content_type)


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    article: ArticleCreate,
    image: Optional[UploadFile] = File(None),
    current_user=Depends(authenticate_user_by_token),
):
    """Создание новой статьи"""
    async with async_session_maker() as session:
        return await crud.create_article(session, article, image)


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article: ArticleUpdate,
    image: Optional[UploadFile] = File(None),
    current_user=Depends(authenticate_user_by_token),
):
    """Обновление статьи"""
    async with async_session_maker() as session:
        updated_article = await crud.update_article(session, article_id, article, image)
        if not updated_article:
            raise HTTPException(status_code=404, detail="Article not found")
        return updated_article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: int, current_user=Depends(authenticate_user_by_token)
):
    """Удаление статьи"""
    async with async_session_maker() as session:
        if not await crud.delete_article(session, article_id):
            raise HTTPException(status_code=404, detail="Article not found")


@router.patch("/{article_id}/toggle-visibility", response_model=ArticleResponse)
async def toggle_article_visibility(
    article_id: int, current_user=Depends(authenticate_user_by_token)
):
    """Переключение видимости статьи"""
    async with async_session_maker() as session:
        article = await crud.toggle_article_visibility(session, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article
