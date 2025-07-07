from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Optional
import os

from app.api.deps import get_current_admin_or_superuser, get_current_user_optional
from app.crud import partner as partner_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.partner import PartnerCreate, PartnerUpdate, PartnerInDB
from app.utils.files import save_image
from app.core.config import settings

# Публичный роутер для открытых эндпоинтов
public_router = APIRouter()

# Административный роутер для закрытых эндпоинтов
admin_router = APIRouter()


# === ПУБЛИЧНЫЕ ЭНДПОИНТЫ ===

@public_router.get("/", response_model=list[PartnerInDB])
async def read_public_partners(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
):
    """Получить список публичных партнеров (открытый эндпоинт)"""
    return await partner_crud.get_partners_list(db, skip=skip, limit=limit, show_hidden=False)


@public_router.get("/{partner_id}", response_model=PartnerInDB)
async def get_public_partner_by_id(partner_id: int, db: AsyncSession = Depends(get_async_session)):
    """Получить публичного партнера по ID"""
    partner = await partner_crud.get_partner(db, partner_id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партнер не найден."
        )
    if not partner.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партнер не найден."
        )
    return partner


@public_router.get("/{partner_id}/image")
async def get_partner_image(partner_id: int, db: AsyncSession = Depends(get_async_session)):
    """Получить изображение партнера по ID"""
    partner = await partner_crud.get_partner(db, partner_id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партнер не найден."
        )

    if not partner.image_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="У партнера нет изображения."
        )

    # Получаем путь к файлу из URL
    # URL имеет формат /media/partners/filename.ext
    image_path = os.path.join(settings.MEDIA_ROOT, partner.image_url.lstrip("/media/"))

    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Изображение не найдено."
        )

    return FileResponse(image_path)


# === АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ ===

@admin_router.get("/", response_model=list[PartnerInDB])
async def read_all_partners(
    skip: int = 0,
    limit: int = 100,
    show_hidden: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Получить список всех партнеров (включая скрытые) - только для администраторов"""
    return await partner_crud.get_partners_list(db, skip=skip, limit=limit, show_hidden=show_hidden)


@admin_router.get("/{partner_id}", response_model=PartnerInDB)
async def get_partner_by_id_admin(partner_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_admin_or_superuser)):
    """Получить партнера по ID (включая скрытые) - только для администраторов"""
    partner = await partner_crud.get_partner(db, partner_id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партнер не найден."
        )
    return partner


@admin_router.post("/", response_model=PartnerInDB)
async def create_partner_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    name: str = Form(...),
    description: str = Form(None),
    is_active: bool = Form(True),
    image: Union[UploadFile, None, str] = File(None),
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Создать партнера с возможностью загрузки изображения (только для администраторов)"""
    if isinstance(image, str) and image == "":
        image = None
    
    # Сохраняем изображение, если оно предоставлено
    image_url = None
    if image:
        image_url = await save_image(image, "partners")

    partner_in = PartnerCreate(
        name=name, description=description, image_url=image_url, is_active=is_active
    )

    return await partner_crud.create_partner(db=db, partner_in=partner_in)


@admin_router.put("/{partner_id}", response_model=PartnerInDB)
async def update_partner_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    partner_id: int,
    name: str = Form(None),
    description: str = Form(None),
    is_active: bool = Form(None),
    image: UploadFile | None = File(None),
    remove_image: str = Form(None),
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Обновить партнера с возможностью обновления изображения (только для администраторов)"""
    # Сохраняем новое изображение, если оно предоставлено
    image_url = None
    if image:
        image_url = await save_image(image, "partners")
    elif remove_image == "true":
        image_url = None

    partner_update = PartnerUpdate(
        name=name, description=description, image_url=image_url, is_active=is_active
    )

    partner = await partner_crud.update_partner(db=db, partner_id=partner_id, partner_in=partner_update)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партнер не найден."
        )
    return partner


@admin_router.delete("/{partner_id}")
async def delete_partner_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    partner_id: int,
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Удалить партнера (только для администраторов)"""
    if not await partner_crud.delete_partner(db=db, partner_id=partner_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партнер не найден."
        )
    return {"ok": True}


@admin_router.post("/{partner_id}/toggle-visibility", response_model=PartnerInDB)
async def toggle_partner_visibility(
    *,
    db: AsyncSession = Depends(get_async_session),
    partner_id: int,
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Переключить видимость партнера (только для администраторов)"""
    partner = await partner_crud.toggle_partner_visibility(db=db, partner_id=partner_id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партнер не найден."
        )
    return partner 