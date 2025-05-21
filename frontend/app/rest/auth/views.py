from flask import Blueprint, render_template, request, jsonify
import requests

from core.config import settings


auth_app = Blueprint("auth_app", __name__)

app = auth_app

@app.route("/login", endpoint="login", methods=["GET", "POST"])
def login_view():
    if request.method == "GET":
        return render_template("auth/login.html")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        response = requests.post(
            f"{settings.BACKEND_URL}/users/login",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        return (response.content, response.status_code, response.headers.items())
        
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/register", endpoint="register", methods=["GET", "POST"])
def register_view():
    """Функция для регистрации пользователя в системе"""
    if request.method == "GET":
        return render_template("auth/register.html")
    
    pass # Дописать логику для отправки данных с формы на сервер (с нашего шаблона должен приходить JSON)