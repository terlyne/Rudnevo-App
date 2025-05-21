from flask import Flask

from rest.auth.views import auth_app

def create_app():
    app = Flask(__name__)
    app.config.update(
        TEMPLATES_AUTO_RELOAD=True, # При деплое убрать эту настройку
    )
    app.register_blueprint(auth_app) # Регистрация всех путей аутентификации (регистрации и входа) пользователя
    return app

def main():
    app = create_app()
    app.run(debug=True)

if __name__ == "__main__":
    main()