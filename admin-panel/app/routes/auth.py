from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.services.api import api_service
from app.models.user import User

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Пожалуйста, заполните все поля', 'error')
            return render_template('auth/login.html')
        
        result = api_service.login(username, password)
        if result and result.get('access_token'):
            api_service.set_token(result['access_token'])
            user_data = api_service.get_current_user()
            
            if user_data and isinstance(user_data, dict) and user_data.get('is_superuser') is True:
                user = User(
                    id=user_data['id'],
                    email=user_data['username'],
                    is_admin=True
                )
                login_user(user)
                return redirect(url_for('admin.index'))
            else:
                api_service.clear_token()
                flash('Доступ запрещен. Только администраторы могут войти в панель управления.', 'error')
                return render_template('auth/login.html')
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    token = request.args.get('token')
    if not token:
        flash('Отсутствует токен регистрации', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not email or not username or not password or not password_confirm:
            flash('Пожалуйста, заполните все поля', 'error')
            return render_template('auth/register.html', token=token)
        
        if password != password_confirm:
            flash('Пароли не совпадают', 'error')
            return render_template('auth/register.html', token=token)
        
        result = api_service.complete_registration(token, email, username, password)
        if result:
            flash('Регистрация успешно завершена. Теперь вы можете войти.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Ошибка при регистрации. Возможно, токен недействителен или срок его действия истек.', 'error')
            return render_template('auth/register.html', token=token)
    
    return render_template('auth/register.html', token=token)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    api_service.clear_token()
    return redirect(url_for('auth.login')) 