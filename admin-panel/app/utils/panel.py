from flask import request, redirect, url_for, session
from functools import wraps
from api.client import api_client


def login_required(f):
    """Декоратор для проверки авторизации"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "access_token" not in session:
            return redirect(url_for("auth.login"))
        
        # Проверяем, что токен действителен
        try:
            current_user = get_current_user()
            if not current_user:
                return redirect(url_for("auth.login"))
        except Exception:
            return redirect(url_for("auth.login"))
        
        return f(*args, **kwargs)

    return decorated_function


def recruiter_restricted(f):
    """Декоратор для ограничения доступа работодателей к определенным страницам"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if current_user and current_user.get("is_recruiter") and not current_user.get("is_superuser"):
            return redirect(url_for("panel.vacancies_list"))
        return f(*args, **kwargs)

    return decorated_function


def admin_restricted(f):
    """Декоратор для ограничения доступа обычных администраторов к вакансиям и пользователям"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if current_user and not current_user.get("is_superuser") and not current_user.get("is_recruiter"):
            return redirect(url_for("panel.home"))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    """Получить текущего пользователя"""
    try:
        return api_client.get_current_user()
    except Exception as e:
        # Если токен истек, очищаем сессию
        from flask import session
        if "access_token" in session:
            session.pop("access_token")
        if "refresh_token" in session:
            session.pop("refresh_token")
        return None


def get_navigation_elements() -> dict[str, dict]:
    current_user = get_current_user()
    if not current_user:
        return {}

    current_endpoint = request.endpoint

    # Базовые элементы для всех пользователей
    nav_items = {
        "panel.home": "Главная",
        "panel.feedback_list": "Вопросы",
        "panel.news_list": "Новости",
        "panel.reviews_list": "Отзывы",
        "panel.schedule_list": "Расписание",
        "panel.partners_list": "Партнеры",
    }

    # Для суперпользователей добавляем дополнительные элементы
    if current_user.get("is_superuser"):
        nav_items.update(
            {"panel.vacancies_list": "Вакансии", "panel.users_list": "Пользователи"}
        )
    # Для рекрутеров (но не суперпользователей) оставляем ТОЛЬКО вакансии
    elif current_user.get("is_recruiter"):
        nav_items = {"panel.vacancies_list": "Вакансии"}
    # Для обычных администраторов оставляем базовые элементы (без вакансий и пользователей)
    else:
        pass

    return {
        endpoint: {"text": text, "is_active": endpoint == current_endpoint}
        for endpoint, text in nav_items.items()
    }
