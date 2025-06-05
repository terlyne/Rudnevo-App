from fastapi import APIRouter

from app.api.v1 import (
    auth,
    users,
    news,
    reviews,
    feedback,
    schedule,
    password
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(password.router, prefix="/password", tags=["password"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])