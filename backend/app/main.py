import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database import engine, Base
from users.router import router as users_router
from articles.router import router as articles_router
from schedules.router import router as schedules_router
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1", "http://localhost"], # При деплое поменять на нормальный хост, домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def create_tables():
    """Создает все таблицы в базе данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # Удаляем все таблицы перед запуском приложения, надо будет потом убрать (добавил для тестирования)
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы созданы")


app.include_router(users_router, prefix="/api")
app.include_router(articles_router, prefix="/api")
app.include_router(schedules_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Бэкенд для Руднево"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
