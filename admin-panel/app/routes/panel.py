from flask import Blueprint, request, render_template, flash, redirect, url_for
from datetime import datetime
import requests
import logging

from api.client import api_client, AuthenticationError, ValidationError, APIError
from utils.panel import get_navigation_elements, login_required

logger = logging.getLogger(__name__)

panel = Blueprint("panel", __name__, template_folder="templates")


@panel.route("/", methods=["GET", "POST"], endpoint="home")
@login_required
def home():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        last_actions = api_client.get_actions()
        return render_template(
            "panel/home.html", nav_elements=nav_elements, last_actions=last_actions
        )


@panel.route("/feedback", methods=["GET", "POST"], endpoint="feedback_list")
@login_required
def feedback_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        feedbacks = api_client.get("/feedback")

        for feedback in feedbacks:
            if "created_at" in feedback:
                try:
                    feedback["created_at"] = datetime.fromisoformat(
                        feedback["created_at"]
                    )
                except (ValueError, TypeError):
                    feedback["created_at"] = (
                        datetime.now()
                    )  # или другое значение по умолчанию

        return render_template(
            "panel/feedback/feedback_list.html",
            nav_elements=nav_elements,
            feedbacks=feedbacks,
        )


@panel.route("/news", methods=["GET", "POST"], endpoint="news_list")
@login_required
def news_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        news = api_client.get("/news")
        return render_template(
            "panel/news/news_list.html", nav_elements=nav_elements, news=news
        )
    ...


@panel.route("/reviews", methods=["GET", "POST"], endpoint="reviews_list")
@login_required
def reviews_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        reviews = api_client.get("/reviews")
        return render_template(
            "panel/reviews/reviews_list.html",
            nav_elements=nav_elements,
            reviews=reviews,
        )
    ...


@panel.route("/schedule", methods=["GET", "POST"], endpoint="schedule_list")
@login_required
def schedule_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        schedule = api_client.get("/schedule")
        return render_template(
            "panel/schedule/schedule_list.html",
            nav_elements=nav_elements,
            schedule=schedule,
        )
    ...


@panel.route("/users", methods=["GET", "POST"], endpoint="users_list")
@login_required
def users_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        users = api_client.get("/users")
        return render_template(
            "panel/users/users_list.html", nav_elements=nav_elements, users=users
        )
    ...


@panel.route("/vacancies", methods=["GET", "POST"], endpoint="vacancies_list")
@login_required
def vacancies_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        show_hidden = request.args.get("show_hidden", "false").lower() == "true"
        vacancies = api_client.get_vacancies(show_hidden=show_hidden)

        # Получаем статистику для каждой вакансии
        for vacancy in vacancies:
            try:
                stats = api_client.get_vacancy_statistics(vacancy["id"])
                vacancy["statistics"] = stats
            except:
                vacancy["statistics"] = {
                    "total_applications": 0,
                    "new_applications": 0,
                    "in_review_applications": 0,
                    "invited_applications": 0,
                    "rejected_applications": 0,
                    "conversion_rate": 0,
                    "is_full": False,
                }

        return render_template(
            "panel/vacancies/vacancies_list.html",
            nav_elements=nav_elements,
            vacancies=vacancies,
            show_hidden=show_hidden,
        )


@panel.route("/vacancies/create", methods=["GET", "POST"], endpoint="vacancy_create")
@login_required
def vacancy_create():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        return render_template(
            "panel/vacancies/vacancy_form.html",
            nav_elements=nav_elements,
            vacancy=None,
            is_edit=False,
        )

    if request.method == "POST":
        try:
            # Валидация дат
            start_date = request.form.get("start")
            end_date = request.form.get("end")

            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                if start_dt >= end_dt:
                    flash(
                        "Дата начала должна быть раньше даты окончания",
                        category="error",
                    )
                    return redirect(url_for("panel.vacancy_create"))

                # Проверяем, что дата начала не в прошлом
                today = datetime.now().date()
                if start_dt.date() < today:
                    flash("Дата начала не может быть в прошлом", category="error")
                    return redirect(url_for("panel.vacancy_create"))

            data = {
                "title": request.form.get("title"),
                "description": request.form.get("description"),
                "direction": request.form.get("direction"),
                "speciality": request.form.get("speciality"),
                "requirements": request.form.get("requirements"),
                "work_format": request.form.get("work_format"),
                "start": start_date,
                "end": end_date,
                "chart": request.form.get("chart"),
                "contact_person": request.form.get("contact_person"),
                "required_amount": int(request.form.get("required_amount", 1)),
                "is_hidden": request.form.get("is_hidden") == "on",
            }

            logger.info(f"Creating vacancy with data: {data}")

            result = api_client.create_vacancy(**data)
            logger.info(f"Vacancy creation result: {result}")

            flash("Вакансия успешно создана", category="success")
            return redirect(url_for("panel.vacancies_list"))

        except (ValidationError, APIError) as e:
            logger.error(f"Error creating vacancy: {str(e)}")
            flash(str(e), category="error")
            return redirect(url_for("panel.vacancy_create"))


@panel.route(
    "/vacancies/<int:vacancy_id>/edit", methods=["GET", "POST"], endpoint="vacancy_edit"
)
@login_required
def vacancy_edit(vacancy_id):
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        vacancy = api_client.get_vacancy(vacancy_id)
        return render_template(
            "panel/vacancies/vacancy_form.html",
            nav_elements=nav_elements,
            vacancy=vacancy,
            is_edit=True,
        )

    if request.method == "POST":
        try:
            # Валидация дат
            start_date = request.form.get("start")
            end_date = request.form.get("end")

            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                if start_dt >= end_dt:
                    flash(
                        "Дата начала должна быть раньше даты окончания",
                        category="error",
                    )
                    return redirect(
                        url_for("panel.vacancy_edit", vacancy_id=vacancy_id)
                    )

                # Проверяем, что дата начала не в прошлом
                today = datetime.now().date()
                if start_dt.date() < today:
                    flash("Дата начала не может быть в прошлом", category="error")
                    return redirect(
                        url_for("panel.vacancy_edit", vacancy_id=vacancy_id)
                    )

            data = {
                "title": request.form.get("title"),
                "description": request.form.get("description"),
                "direction": request.form.get("direction"),
                "speciality": request.form.get("speciality"),
                "requirements": request.form.get("requirements"),
                "work_format": request.form.get("work_format"),
                "start": start_date,
                "end": end_date,
                "chart": request.form.get("chart"),
                "contact_person": request.form.get("contact_person"),
                "required_amount": int(request.form.get("required_amount", 1)),
                "is_hidden": request.form.get("is_hidden") == "on",
            }

            api_client.update_vacancy(vacancy_id, **data)
            flash("Вакансия успешно обновлена", category="success")
            return redirect(url_for("panel.vacancies_list"))

        except (ValidationError, APIError) as e:
            flash(str(e), category="error")
            return redirect(url_for("panel.vacancy_edit", vacancy_id=vacancy_id))


@panel.route(
    "/vacancies/<int:vacancy_id>/delete", methods=["POST"], endpoint="vacancy_delete"
)
@login_required
def vacancy_delete(vacancy_id):
    try:
        api_client.delete_vacancy(vacancy_id)
        flash("Вакансия успешно удалена", category="success")
    except (ValidationError, APIError) as e:
        flash(str(e), category="error")

    return redirect(url_for("panel.vacancies_list"))


@panel.route(
    "/vacancies/<int:vacancy_id>/applications",
    methods=["GET", "POST"],
    endpoint="vacancy_applications",
)
@login_required
def vacancy_applications(vacancy_id):
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        vacancy = api_client.get_vacancy(vacancy_id)
        students = api_client.get_students(vacancy_id=vacancy_id)

        # Группируем студентов по статусам
        students_by_status = {"new": [], "in_review": [], "invited": [], "rejected": []}

        for student in students:
            status = student.get("status", "new")
            students_by_status[status].append(student)

        return render_template(
            "panel/vacancies/vacancy_applications.html",
            nav_elements=nav_elements,
            vacancy=vacancy,
            students_by_status=students_by_status,
        )

    if request.method == "POST":
        try:
            action = request.form.get("action")
            student_ids = request.form.getlist("student_ids")

            if action == "bulk_update_status":
                status = request.form.get("status")
                if student_ids and status:
                    student_ids = [int(sid) for sid in student_ids]
                    api_client.bulk_update_student_status(student_ids, status)
                    flash(
                        f"Статус {len(student_ids)} заявок обновлен", category="success"
                    )

        except (ValidationError, APIError) as e:
            flash(str(e), category="error")

        return redirect(url_for("panel.vacancy_applications", vacancy_id=vacancy_id))


@panel.route("/profile", methods=["GET", "POST"], endpoint="profile")
@login_required
def profile():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = api_client.get_current_user()
        return render_template(
            "panel/profile.html", nav_elements=nav_elements, user=current_user
        )
    ...



@panel.route("/student_resume_file", methods=["GET"], endpoint="student_resume_file")
@login_required
def student_resume_file():
    student_id = request.args.get("student_id")
    if not student_id:
        flash("Не указан студент", "error")
        return redirect(url_for("panel.vacancies_list"))