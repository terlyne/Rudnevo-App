from flask import Flask
from flask_login import LoginManager
from app.core.config import settings
from app.models.user import User
from app.services.api import api_service

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    user_data = api_service.get_user(user_id)
    if user_data:
        return User(
            id=user_data['id'],
            email=user_data['email'],
            is_admin=user_data.get('is_superuser', False)
        )
    return None

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    
    # Register blueprints
    from app.routes import auth, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    
    return app 