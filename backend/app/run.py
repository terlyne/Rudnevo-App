import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import timedelta
import uvicorn

from app.core.config import settings
from app.api.v1 import api_router
from app.db.session import engine, async_session_maker, get_async_session
from app.models import Base
from app.crud.user import get_user_by_email, create_user
from app.schemas.user import UserCreate
from app.core.security import create_registration_token
from app.utils.email import send_registration_email
from app.utils.task_scheduler import run_periodic_task, actions_weekly_cleanup

import logging
logging.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер жизненного цикла приложения.
    Выполняется при запуске и остановке.
    """
    # Удаляем все таблицы и создаем их заново при запуске
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Запуск задачи очистки таблицы с событиями
    async def start_background_tasks():
        async for db in get_async_session():
            asyncio.create_task(run_periodic_task(db, actions_weekly_cleanup))

    asyncio.create_task(start_background_tasks())

    # Создаем директории для медиафайлов
    media_root = Path(settings.MEDIA_ROOT)
    (media_root / "news").mkdir(parents=True, exist_ok=True)
    (media_root / "resumes").mkdir(parents=True, exist_ok=True)

    # Создаем начального пользователя только с email
    async with async_session_maker() as session:
        admin = await get_user_by_email(session, settings.ADMIN_EMAIL)
        if not admin:
            # Создаем пользователя только с email, is_superuser=True и is_recruiter=True
            user_in = UserCreate(
                email=settings.ADMIN_EMAIL,
                is_superuser=True,
                is_recruiter=True,  # Супер-пользователь должен иметь все права
            )
            admin = await create_user(session, user_in)

            # Создаем токен для регистрации
            token_expires = timedelta(hours=24)
            token = create_registration_token(
                data={"sub": str(admin.id)},
                expires_delta=token_expires,
            )

            # Отправляем email с приглашением
            await send_registration_email(email_to=admin.email, token=token)

    yield

    # Очистка ресурсов при остановке
    await engine.dispose()


# Создаем экземпляр FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Настраиваем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы
app.mount("/media", StaticFiles(directory="media"), name="media")

# Подключаем роутеры
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0")