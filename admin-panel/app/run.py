from flask import Flask
from flask_wtf.csrf import CSRFProtect, generate_csrf

from routes.auth import auth
from routes.panel import panel
from core.config import settings


app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY

# Включаем CSRF защиту
csrf = CSRFProtect()
csrf.init_app(app)

# Добавляем CSRF токен в контекст шаблонов
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

app.register_blueprint(auth)
app.register_blueprint(panel)

@app.template_filter("datetime_format")
def datetime_format(value, format="%d.%m.%Y %H:%M"):
    if value is None:
        return ""
    return value.strftime(format)


if __name__ == "__main__":
    app.run(debug=True)