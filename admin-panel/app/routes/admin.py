from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.services.api import api_service

bp = Blueprint('admin', __name__)

@bp.route('/')
@login_required
def index():
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    return render_template('admin/index.html')

@bp.route('/users')
@login_required
def users():
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    users_list = api_service.get_users()
    return render_template('admin/users.html', users=users_list)

@bp.route('/users/invite', methods=['POST'])
@login_required
def invite_user():
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    email = request.form.get('email')
    if not email:
        flash('Email обязателен', 'error')
        return redirect(url_for('admin.users'))
    
    result = api_service.create_user_invitation(email)
    if result:
        flash(f'Приглашение отправлено на {email}', 'success')
    else:
        flash('Ошибка при отправке приглашения', 'error')
    return redirect(url_for('admin.users'))

@bp.route('/users/<user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    if api_service.delete_user(user_id):
        flash('Пользователь удален', 'success')
    else:
        flash('Ошибка при удалении пользователя', 'error')
    return redirect(url_for('admin.users'))

@bp.route('/news')
@login_required
def news():
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    news_list = api_service.get_news()
    return render_template('admin/news.html', news=news_list)

@bp.route('/news/new', methods=['GET'])
@login_required
def new_news():
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    return render_template('admin/news_form.html')

@bp.route('/news', methods=['POST'])
@login_required
def create_news():
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    
    title = request.form.get('title')
    content = request.form.get('content')
    image_url = request.form.get('image_url')
    
    if not title or not content:
        flash('Заголовок и содержание обязательны', 'error')
        return render_template('admin/news_form.html')
    
    result = api_service.create_news(title, content, image_url)
    if result:
        flash('Новость создана', 'success')
        return redirect(url_for('admin.news'))
    else:
        flash('Ошибка при создании новости', 'error')
        return render_template('admin/news_form.html')

@bp.route('/news/<news_id>/edit', methods=['GET'])
@login_required
def edit_news_form(news_id):
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    
    news_item = api_service.get_news_item(news_id)
    if not news_item:
        flash('Новость не найдена', 'error')
        return redirect(url_for('admin.news'))
    
    return render_template('admin/news_form.html', news=news_item)

@bp.route('/news/<news_id>', methods=['POST'])
@login_required
def update_news(news_id):
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    
    title = request.form.get('title')
    content = request.form.get('content')
    image_url = request.form.get('image_url')
    
    if not title or not content:
        flash('Заголовок и содержание обязательны', 'error')
        return redirect(url_for('admin.edit_news_form', news_id=news_id))
    
    result = api_service.update_news(news_id, title, content, image_url)
    if result:
        flash('Новость обновлена', 'success')
        return redirect(url_for('admin.news'))
    else:
        flash('Ошибка при обновлении новости', 'error')
        return redirect(url_for('admin.edit_news_form', news_id=news_id))

@bp.route('/news/<news_id>/delete', methods=['POST'])
@login_required
def delete_news(news_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    if api_service.delete_news(news_id):
        flash('Новость удалена', 'success')
    else:
        flash('Ошибка при удалении новости', 'error')
    return redirect(url_for('admin.news')) 