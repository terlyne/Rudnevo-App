from models.base import Base
from models.user import User
from models.news import News
from models.review import Review
from models.feedback import Feedback
from models.schedule import Schedule, ScheduleTemplate
from models.vacancy import Vacancy
from models.student import Student, ApplicationStatus
from models.partner import Partner
from models.college import College

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
    "Partner",
    "College",
]
