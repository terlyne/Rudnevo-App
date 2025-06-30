from app.models.base import Base
from app.models.user import User
from app.models.news import News
from app.models.review import Review
from app.models.feedback import Feedback
from app.models.schedule import Schedule, ScheduleTemplate
from app.models.vacancy import Vacancy
from app.models.student import Student, ApplicationStatus

__all__ = [
    "Base",
    "User",
    "News",
    "Review",
    "Feedback",
    "Schedule",
    "ScheduleTemplate",
    "Vacancy",
    "Student",
    "ApplicationStatus",
]
