from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Optional
import os

from app.api.deps import get_current_admin_or_superuser
from app.crud import college as college_crud
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.college import CollegeCreate, CollegeUpdate, CollegeInDB
from app.utils.files import save_image
from app.core.config import settings

# Публичный роутер для открытых эндпоинтов
public_router = APIRouter()

# Административный роутер для закрытых эндпоинтов
admin_router = APIRouter()


# === ПУБЛИЧНЫЕ ЭНДПОИНТЫ ===

@public_router.get("/", response_model=list[CollegeInDB])
async def read_public_colleges(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
):
    """Получить список публичных колледжей (открытый эндпоинт)"""
    return await college_crud.get_colleges_list(db, skip=skip, limit=limit)


@public_router.get("/{college_id}", response_model=CollegeInDB)
async def get_public_college_by_id(college_id: int, db: AsyncSession = Depends(get_async_session)):
    """Получить публичный колледж по ID"""
    college = await college_crud.get_college(db, college_id)
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Колледж не найден."
        )
    return college


@public_router.get("/{college_id}/image")
async def get_college_image(college_id: int, db: AsyncSession = Depends(get_async_session)):
    """Получить изображение колледжа по ID"""
    college = await college_crud.get_college(db, college_id)
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Колледж не найден."
        )

    if not college.image_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="У колледжа нет изображения."
        )

    # Получаем путь к файлу из URL
    # URL имеет формат /media/colleges/filename.ext
    image_path = os.path.join(settings.MEDIA_ROOT, college.image_url.lstrip("/media/"))

    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Изображение не найдено."
        )

    return FileResponse(image_path)


# === АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ ===

@admin_router.get("/", response_model=list[CollegeInDB])
async def read_all_colleges(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser),
):
    """Получить список всех колледжей - только для администраторов"""
    return await college_crud.get_colleges_list(db, skip=skip, limit=limit)


@admin_router.get("/{college_id}", response_model=CollegeInDB)
async def get_college_by_id_admin(college_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_admin_or_superuser)):
    """Получить колледж по ID - только для администраторов"""
    college = await college_crud.get_college(db, college_id)
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Колледж не найден."
        )
    return college


@admin_router.post("/", response_model=CollegeInDB)
async def create_college_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    name: str = Form(...),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Создать колледж с обязательной загрузкой изображения (только для администраторов)"""
    
    # Сохраняем изображение (обязательно)
    image_url = await save_image(image, "colleges")

    college_in = CollegeCreate(
        name=name, image_url=image_url
    )

    return await college_crud.create_college(db=db, college_in=college_in)


@admin_router.put("/{college_id}", response_model=CollegeInDB)
async def update_college_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    college_id: int,
    name: str = Form(None),
    image: UploadFile | None = File(None),
    remove_image: str = Form(None),
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Обновить колледж с возможностью обновления изображения (только для администраторов)"""
    # Сохраняем новое изображение, если оно предоставлено
    image_url = None
    if image:
        image_url = await save_image(image, "colleges")
    elif remove_image == "true":
        image_url = None

    college_update = CollegeUpdate(
        name=name, image_url=image_url
    )

    college = await college_crud.update_college(db=db, college_id=college_id, college_in=college_update)
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Колледж не найден."
        )
    return college


@admin_router.delete("/{college_id}")
async def delete_college_item(
    *,
    db: AsyncSession = Depends(get_async_session),
    college_id: int,
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Удалить колледж (только для администраторов)"""
    if not await college_crud.delete_college(db=db, college_id=college_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Колледж не найден."
        )
    return {"ok": True} 