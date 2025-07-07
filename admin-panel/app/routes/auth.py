from flask import Blueprint, request, render_template, flash, redirect, url_for, jsonify
import logging

from api.client import api_client, AuthenticationError, ValidationError, APIError


# Настраиваем логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


auth = Blueprint("auth", __name__, template_folder="templates")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")

    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("password")

            api_client.login(username=username, password=password)
            
            # Получаем информацию о пользователе для определения роли
            try:
                user_info = api_client.get_current_user()
                if user_info.get("is_recruiter") and not user_info.get("is_superuser"):
                    # Работодатель - перенаправляем на вакансии
                    flash("Успешный вход", category="success")
                    return redirect(url_for("panel.vacancies_list"))
                else:
                    # Администратор - перенаправляем на главную
                    flash("Успешный вход", category="success")
                    return redirect(url_for("panel.home"))
            except Exception:
                # Если не удалось получить информацию о пользователе, перенаправляем на главную
                flash("Успешный вход", category="success")
                return redirect(url_for("panel.home"))

        except AuthenticationError as e:
            flash("Неверное имя пользователя или пароль", category="error")
            return redirect(url_for("auth.login"))
        except ValidationError as e:
            flash(str(e), category="error")
            return redirect(url_for("auth.login"))
        except APIError as e:
            flash(str(e), category="error")
            return redirect(url_for("auth.login"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        # Получаем токен из URL параметра при GET запросе
        token = request.args.get("token", "")
        logger.debug(f"GET: Received token (length: {len(token)}): {token}")

        if not token or len(token.strip()) == 0:
            logger.warning("GET: Token is missing or empty")
            flash(
                "Для регистрации необходим токен. Проверьте ссылку в письме.",
                category="error",
            )
            return redirect(url_for("auth.login"))

        return render_template("auth/register.html", token=token)

    if request.method == "POST":
        try:
            # При POST запросе получаем токен из формы
            token = request.form.get("token", "")
            logger.debug(
                f"POST: Received token from form (length: {len(token)}): {token}"
            )

            if not token or len(token.strip()) == 0:
                logger.warning("POST: Token is missing or empty in form data")
                flash("Отсутствует токен регистрации.", category="error")
                return redirect(url_for("auth.login"))

            email = request.form.get("email")
            username = request.form.get("username")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm-password")

            logger.debug(
                f"Registration attempt - Email: {email}, Username: {username}, Token length: {len(token)}"
            )

            if not all([email, username, password]):
                flash("Все поля обязательны для заполнения.", category="error")
                return redirect(url_for("auth.register", token=token))

            if password != confirm_password:
                flash("Пароли не совпадают.", category="error")
                return redirect(url_for("auth.register", token=token))

            if len(password) < 8:
                flash("Пароль должен содержать минимум 8 символов.", category="error")
                return redirect(url_for("auth.register", token=token))

            # Логируем данные перед отправкой в API
            logger.debug("Sending registration request to API")
            logger.debug(f"Token being used: {token}")

            api_client.register(
                email=email, username=username, password=password, token=token
            )
            flash("Регистрация успешна", category="success")
            return redirect(url_for("auth.login"))

        except ValidationError as e:
            logger.error(f"Validation error during registration: {str(e)}")
            flash(str(e), category="error")
            return redirect(url_for("auth.register", token=token))
        except APIError as e:
            logger.error(f"API error during registration: {str(e)}")
            flash(str(e), category="error")
            return redirect(url_for("auth.register", token=token))
        except Exception as e:
            logger.exception("Unexpected error during registration")
            flash("Произошла ошибка при регистрации", category="error")
            return redirect(url_for("auth.register", token=token))


@auth.route("/forgot-password", methods=["GET", "POST"], endpoint="forgot_password")
def forgot_password():
    if request.method == "GET":
        return render_template("auth/forgot_password.html")

    if request.method == "POST":
        email = request.form.get("email")
        if not email:
            flash("Email обязателен для заполнения.", category="error")
            return redirect(url_for("auth.forgot_password"))
        try:
            api_client.forgot_password(email=email)
            flash(
                "Если пользователь с таким email существует, на почту была отправлена ссылка для изменения пароля",
                category="success"
            )
            return redirect(url_for("auth.login"))
        except ValidationError as e:
            flash(str(e), category="error")
            return redirect(url_for("auth.forgot_password"))
        except APIError as e:
            flash(str(e), category="error")
            return redirect(url_for("auth.forgot_password"))



@auth.route("/change-password", methods=["GET", "POST"])
def change_password():
    if request.method == "GET":
        return render_template("auth/change_password.html")

    if request.method == "POST":
        try:
            current_password = request.form.get("current-password")
            new_password = request.form.get("new-password")
            confirm_password = request.form.get("confirm-new-password")

            if not all([current_password, new_password, confirm_password]):
                flash("Все поля обязательны для заполнения", category="error")
                return redirect(url_for("auth.change_password"))
            if new_password != confirm_password:
                flash("Пароли не совпадают", category="error")
                return redirect(url_for("auth.change_password"))
            if len(new_password) < 8:
                flash("Пароль должен содержать минимум 8 символов", category="error")
                return redirect(url_for("auth.change_password"))

            api_client.change_password(
                current_password=current_password,
                new_password=new_password,
            )
            api_client.logout()
            flash("Пароль успешно изменён. Пожалуйста, войдите снова", category="success")
            return redirect(url_for("auth.login"))
        except ValidationError as e:
            flash(str(e), category="error")
            return redirect(url_for("auth.change_password"))
        except APIError as e:
            flash(str(e), category="error")
            return redirect(url_for("auth.change_password"))


@auth.route("/logout")
def logout():
    api_client.logout()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'redirect': url_for('auth.login')})
    flash("Вы вышли из системы", category="success")
    return redirect(url_for("auth.login"))


@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token") if request.method == "GET" else request.form.get("token")
    if not token:
        flash("Некорректная или устаревшая ссылка для сброса пароля.", category="error")
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("auth/reset_password.html", token=token)

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm-password")
        if not new_password or not confirm_password:
            flash("Все поля обязательны для заполнения.", category="error")
            return redirect(url_for("auth.reset_password", token=token))
        if new_password != confirm_password:
            flash("Пароли не совпадают.", category="error")
            return redirect(url_for("auth.reset_password", token=token))
        if len(new_password) < 8:
            flash("Пароль должен содержать минимум 8 символов.", category="error")
            return redirect(url_for("auth.reset_password", token=token))
        try:
            api_client.reset_password(token=token, new_password=new_password)
            flash("Пароль успешно изменён. Теперь вы можете войти.", category="success")
            return redirect(url_for("auth.login"))
        except ValidationError as e:
            flash(str(e), category="error")
            return redirect(url_for("auth.reset_password", token=token))
        except APIError as e:
            flash(str(e), category="error")
            return redirect(url_for("auth.reset_password", token=token))
