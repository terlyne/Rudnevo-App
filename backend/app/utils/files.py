import os
import uuid

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from app.core.config import settings


async def save_image(
    file: UploadFile,
    folder: str,
    max_size: int | None = None
) -> str:
    """
    Сохранить изображение в указанную папку.
    Возвращает URL для доступа к изображению.
    """
    if not file.content_type in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невалидный тип изображения."
        )
    
    max_size = max_size or settings.MAX_IMAGE_SIZE
    content = await file.read()
    
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Изображение слишком большое."
        )
    
    # Создаем директорию, если её нет
    folder_path = settings.MEDIA_ROOT / folder
    folder_path.mkdir(parents=True, exist_ok=True)
    
    # Генерируем уникальное имя файла
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = folder_path / filename
    
    # Оптимизируем и сохраняем изображение
    try:
        image = Image.open(file.file)
        image.save(file_path, optimize=True, quality=85)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невалидное изображение."
        )
    
    # Возвращаем URL для доступа к изображению
    return f"/media/{folder}/{filename}"


async def delete_file(file_path: str) -> bool:
    """Удалить файл"""
    try:
        full_path = settings.MEDIA_ROOT / file_path.lstrip("/media/")
        if full_path.exists():
            full_path.unlink()
            return True
    except Exception:
        pass
    return False
