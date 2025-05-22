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
        
        if "auth-username" not in data or "auth-password" not in data:
            return jsonify({"error": "Missing required fields"}), 400

        # Отправляем запрос к бэкенду
        response = requests.post(
            f"{settings.BACKEND_URL}/users/login",
            json={
                "identifier": data["auth-username"],
                "password": data["auth-password"]
            },
            headers={"Content-Type": "application/json"}
        )

        # Обрабатываем ответ бэкенда
        if response.status_code >= 400:
            return jsonify({
                "error": "Login failed",
                "details": response.json()
            }), response.status_code

        # Извлекаем токен из заголовка Authorization
        auth_header = response.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "No token in response"}), 500

        token = auth_header.split(' ')[1]  # Получаем часть после 'Bearer '

        # Возвращаем успешный ответ с токеном
        return jsonify({
            "message": "Successfully logged in",
            "token": token  # Теперь токен берётся из заголовка
        }), 200
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Backend service unavailable", "details": str(e)}), 502
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/register", endpoint="register", methods=["GET", "POST"])
def register_view():
    """Функция для регистрации пользователя в системе"""
    if request.method == "GET":
        return render_template("auth/register.html")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        if "username" not in data or "email" not in data or "password" not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        # Отправляем запрос к бэкенду
        response = requests.post(
            f"{settings.BACKEND_URL}/users/register",
            json={
                "username": data["username"],
                "email": data["email"],
                "password": data["password"],
            },
            headers={"Content-Type": "application/json"}
        )

        # Обрабатываем ответ бэкенда
        if response.status_code >= 400:
            return jsonify({
                "error": "Login failed",
                "details": response.json()
            }), response.status_code
        
        return render_template("auth/login.html")
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Backend service unavailable", "details": str(e)}), 502
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500