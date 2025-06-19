from fastapi import APIRouter

from app.api.v1 import (
    auth,
    users,
    news,
    reviews,
    feedback,
    schedule,
    password,
    action,
    vacancy,
    student,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
api_router.include_router(password.router, prefix="/password", tags=["Пароль"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи"])
api_router.include_router(news.router, prefix="/news", tags=["Новости"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Отзывы"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["Вопросы"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["Расписание"])
api_router.include_router(action.router, prefix="/actions", tags=["События"])
api_router.include_router(vacancy.router, prefix="/vacancies", tags=["Вакансии"])
api_router.include_router(student.router, prefix="/students", tags=["Студенты"])
