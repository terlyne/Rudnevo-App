from fastapi import APIRouter

from api.v1 import (
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
    partners,
    colleges,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
api_router.include_router(password.router, prefix="/password", tags=["Пароль"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи"])

# Публичные эндпоинты
api_router.include_router(news.public_router, prefix="/news", tags=["Новости (публичные)"])
api_router.include_router(reviews.public_router, prefix="/reviews", tags=["Отзывы (публичные)"])
api_router.include_router(feedback.public_router, prefix="/feedback", tags=["Вопросы (публичные)"])
api_router.include_router(vacancy.public_router, prefix="/vacancies", tags=["Вакансии (публичные)"])
api_router.include_router(colleges.public_router, prefix="/colleges", tags=["Колледжи (публичные)"])
api_router.include_router(partners.public_router, prefix="/partners", tags=["Партнеры (публичные)"])

# Административные эндпоинты
api_router.include_router(news.admin_router, prefix="/admin/news", tags=["Новости (админ)"])
api_router.include_router(reviews.admin_router, prefix="/admin/reviews", tags=["Отзывы (админ)"])
api_router.include_router(feedback.admin_router, prefix="/admin/feedback", tags=["Вопросы (админ)"])
api_router.include_router(vacancy.admin_router, prefix="/admin/vacancies", tags=["Вакансии (админ)"])
api_router.include_router(colleges.admin_router, prefix="/admin/colleges", tags=["Колледжи (админ)"])
api_router.include_router(partners.admin_router, prefix="/admin/partners", tags=["Партнеры (админ)"])

api_router.include_router(schedule.router, prefix="/schedule", tags=["Расписание"])
api_router.include_router(action.router, prefix="/actions", tags=["События"])
api_router.include_router(student.router, prefix="/students", tags=["Студенты"])
