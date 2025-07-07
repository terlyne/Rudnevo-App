from flask import Blueprint, request, render_template, flash, redirect, url_for, send_file, jsonify, Response
from flask_wtf.csrf import generate_csrf
import io
from datetime import datetime
import logging
import requests

from api.client import api_client, ValidationError, APIError, PermissionError, NotFoundError
from utils.panel import get_navigation_elements, login_required, get_current_user, recruiter_restricted, admin_restricted

logger = logging.getLogger(__name__)

panel = Blueprint("panel", __name__, template_folder="templates")


@panel.route("/", methods=["GET", "POST"], endpoint="home")
@login_required
def home():
    # Проверяем, является ли пользователь работодателем (но не суперадминистратором)
    current_user = get_current_user()
    if current_user and current_user.get("is_recruiter") and not current_user.get("is_superuser"):
        return redirect(url_for("panel.vacancies_list"))
    
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        
        try:
            # Получаем последние события
            last_actions = api_client.get_actions(limit=20)
            
            # Фильтруем события - исключаем действия пользователей и личного кабинета
            filtered_actions = []
            for action in last_actions:
                action_text = action.get("action", "").lower()
                if not any(keyword in action_text for keyword in [
                    "пользователь", "пользователя", "пользователей", 
                    "профиль", "пароль", "выход", "logout", "войти", "login"
                ]):
                    # Форматируем время события
                    if "created_at" in action:
                        try:
                            action["created_at"] = datetime.fromisoformat(
                                action["created_at"].replace("Z", "+00:00")
                            ).strftime("%d.%m.%Y %H:%M")
                        except (ValueError, TypeError):
                            action["created_at"] = "Неизвестно"
                    
                    filtered_actions.append(action)
            filtered_actions = filtered_actions[:10]
            
            # Получаем статистику
            stats = {
                "news_count": 0,
                "feedback_count": 0,
                "reviews_count": 0,
                "users_count": 0
            }
            
            try:
                news = api_client.get_news(show_hidden=True)
                stats["news_count"] = len(news)
            except:
                pass
                
            try:
                feedbacks = api_client.get_feedbacks()
                stats["feedback_count"] = len(feedbacks)
            except:
                pass
                
            try:
                reviews = api_client.get_reviews(show_hidden=True)
                stats["reviews_count"] = len(reviews)
            except:
                pass
            
            if current_user and current_user.get("is_superuser"):
                try:
                    users = api_client.get("/users")
                    stats["users_count"] = len(users)
                except:
                    pass
        except PermissionError:
            # Если у пользователя нет прав на просмотр статистики, показываем пустую главную страницу
            filtered_actions = []
            stats = {
                "news_count": 0,
                "feedback_count": 0,
                "reviews_count": 0,
                "users_count": 0
            }
        except Exception as e:
            logger.error(f"Error loading home page: {str(e)}")
            filtered_actions = []
            stats = {
                "news_count": 0,
                "feedback_count": 0,
                "reviews_count": 0,
                "users_count": 0
            }
        
        return render_template(
            "panel/home.html", 
            nav_elements=nav_elements, 
            last_actions=filtered_actions,
            stats=stats,
            current_user=current_user
        )


@panel.route("/feedback", methods=["GET", "POST"], endpoint="feedback_list")
@login_required
@recruiter_restricted
def feedback_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = get_current_user()
        
        try:
            feedbacks = api_client.get_feedbacks()
            
            # Форматируем даты
            for feedback in feedbacks:
                if "created_at" in feedback:
                    try:
                        feedback["created_at"] = datetime.fromisoformat(
                            feedback["created_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        feedback["created_at"] = "Неизвестно"
                
                if "updated_at" in feedback and feedback["updated_at"]:
                    try:
                        feedback["updated_at"] = datetime.fromisoformat(
                            feedback["updated_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        feedback["updated_at"] = "Неизвестно"
            
            return render_template(
                "panel/feedback/feedback_list.html",
                nav_elements=nav_elements,
                feedbacks=feedbacks,
                current_user=current_user
            )
        except Exception as e:
            logger.error(f"Error loading feedback: {str(e)}")
            flash("Ошибка при загрузке вопросов", category="error")
            return render_template(
                "panel/feedback/feedback_list.html",
                nav_elements=nav_elements,
                feedbacks=[],
                current_user=current_user
            )


@panel.route("/feedback/<int:feedback_id>/respond", methods=["POST"], endpoint="feedback_respond")
@login_required
def feedback_respond(feedback_id):
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.feedback_list"))
        
        # Получаем данные из JSON
        response_text = request.form.get("response_text")
        
        if not response_text:
            flash("Введите текст ответа", category="error")
            return redirect(url_for("panel.feedback_list"))
        
        # Отправляем ответ
        result = api_client.respond_to_feedback(feedback_id, response_text)
        
        # Создаем событие
        try:
            short_text = response_text[:50] + '...' if response_text and len(response_text) > 50 else response_text
            safe_create_action(current_user.get("username", "Администратор"), f'ответил на вопрос: "{short_text}"')
        except:
            pass
        
        flash("Ответ успешно отправлен", category="success")
        api_client.delete_feedback(feedback_id)
        return redirect(url_for("panel.feedback_list"))
        
    except Exception as e:
        logger.error(f"Error responding to feedback {feedback_id}: {str(e)}")
        flash("Ошибка при отправке ответа", category="error")
        return redirect(url_for("panel.feedback_list"))


@panel.route("/feedback/<int:feedback_id>/delete", methods=["POST"], endpoint="feedback_delete")
@login_required
def feedback_delete(feedback_id):
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.feedback_list"))
        
        # Удаляем вопрос
        try:
            feedback = api_client.get_feedback_by_id(feedback_id)
            question = feedback.get('message', '')
        except Exception:
            question = ''
        api_client.delete_feedback(feedback_id)
        # Создаем событие
        try:
            short_question = question[:50] + '...' if question and len(question) > 50 else question
            action_text = f'удалил вопрос: "{short_question}"'
            if len(action_text) > 50:
                action_text = action_text[:47] + '...'
            safe_create_action(current_user.get("username", "Администратор"), action_text)
        except:
            pass
        
        flash("Вопрос успешно удален", category="success")
        return redirect(url_for("panel.feedback_list"))
        
    except Exception as e:
        logger.error(f"Error deleting feedback {feedback_id}: {str(e)}")
        flash("Ошибка при удалении вопроса", category="error")
        return redirect(url_for("panel.feedback_list"))


@panel.route("/news", methods=["GET", "POST"], endpoint="news_list")
@login_required
@recruiter_restricted
def news_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = get_current_user()
        
        try:
            # Получаем все новости, включая скрытые
            news = api_client.get_news(show_hidden=True)
            
            # Форматируем даты
            for news_item in news:
                if "created_at" in news_item:
                    try:
                        news_item["created_at"] = datetime.fromisoformat(
                            news_item["created_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        news_item["created_at"] = "Неизвестно"
            
            return render_template(
                "panel/news/news_list.html", 
                nav_elements=nav_elements, 
                news=news,
                current_user=current_user
            )
        except Exception as e:
            logger.error(f"Error loading news: {str(e)}")
            flash("Ошибка при загрузке новостей", category="error")
            return render_template(
                "panel/news/news_list.html", 
                nav_elements=nav_elements, 
                news=[],
                current_user=current_user
            )


@panel.route("/news/create", methods=["POST"], endpoint="news_create")
@login_required
def news_create():
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на создание новостей", category="error")
            return redirect(url_for("panel.news_list"))
        
        # Получаем данные формы
        title = request.form.get("title")
        content = request.form.get("content")
        is_hidden = request.form.get("is_hidden") == "on"
        
        logger.info(f"Creating news with data: title={title}, is_hidden={is_hidden}")
        
        if not title or not content:
            flash("Заполните все обязательные поля", category="error")
            return redirect(url_for("panel.news_list"))
        
        # Создаем новость
        news_data = {
            "title": title,
            "content": content,
            "is_hidden": is_hidden
        }
        
        # Обрабатываем изображение, если оно загружено
        if "image" in request.files:
            image_file = request.files["image"]
            if image_file and image_file.filename:
                news_data["image"] = image_file
        
        logger.info(f"Sending data to API: {news_data}")
        result = api_client.create_news(**news_data)
        logger.info(f"API response: {result}")
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"добавил новость \"{title}\"")
        except:
            pass
        
        flash("Новость успешно создана", category="success")
        
        # Всегда возвращаемся к списку новостей без параметра show_hidden
        return redirect(url_for("panel.news_list"))
        
    except Exception as e:
        logger.error(f"Error creating news: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        flash("Ошибка при создании новости", category="error")
        return redirect(url_for("panel.news_list"))


@panel.route("/news/<int:news_id>", methods=["GET"], endpoint="news_detail")
@login_required
def news_detail(news_id):
    try:
        news_item = api_client.get_news_by_id(news_id)
        return jsonify(news_item)
    except Exception as e:
        logger.error(f"Error getting news {news_id}: {str(e)}")
        return jsonify({"error": "Новость не найдена"}), 404


@panel.route("/news/<int:news_id>/edit", methods=["POST"], endpoint="news_edit")
@login_required
def news_edit(news_id):
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на редактирование новостей", category="error")
            return redirect(url_for("panel.news_list"))
        
        # Получаем данные формы
        title = request.form.get("title")
        content = request.form.get("content")
        is_hidden = request.form.get("is_hidden") == "on"
        
        if not title or not content:
            flash("Заполните все обязательные поля", category="error")
            return redirect(url_for("panel.news_list"))
        
        # Обновляем новость
        news_data = {
            "title": title,
            "content": content,
            "is_hidden": is_hidden
        }
        
        # Обрабатываем изображение, если оно загружено
        if "image" in request.files:
            image_file = request.files["image"]
            if image_file and image_file.filename:
                news_data["image"] = image_file
        # Обрабатываем удаление изображения
        if request.form.get("remove_image") == "true":
            news_data["remove_image"] = "true"
        
        result = api_client.update_news(news_id, **news_data)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"отредактировал новость \"{title}\"")
        except:
            pass
        
        flash("Новость успешно обновлена", category="success")
        return redirect(url_for("panel.news_list"))
        
    except Exception as e:
        logger.error(f"Error updating news {news_id}: {str(e)}")
        flash("Ошибка при обновлении новости", category="error")
        return redirect(url_for("panel.news_list"))


@panel.route("/news/<int:news_id>/delete", methods=["POST"], endpoint="news_delete")
@login_required
def news_delete(news_id):
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на удаление новостей", category="error")
            return redirect(url_for("panel.news_list"))
        
        # Получаем информацию о новости для события
        try:
            news_item = api_client.get_news_by_id(news_id)
            news_title = news_item.get("title", "неизвестная новость")
        except:
            news_title = "неизвестная новость"
        
        # Удаляем новость
        api_client.delete_news(news_id)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"удалил новость \"{news_title}\"")
        except:
            pass
        
        flash("Новость успешно удалена", category="success")
        return redirect(url_for("panel.news_list"))
        
    except Exception as e:
        logger.error(f"Error deleting news {news_id}: {str(e)}")
        flash("Ошибка при удалении новости", category="error")
        return redirect(url_for("panel.news_list"))


@panel.route("/news/<int:news_id>/toggle-visibility", methods=["POST"], endpoint="news_toggle_visibility")
@login_required
def news_toggle_visibility(news_id):
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на изменение видимости новостей", category="error")
            return redirect(url_for("panel.news_list"))
        
        # Получаем информацию о новости для события
        try:
            news_item = api_client.get_news_by_id(news_id)
            news_title = news_item.get("title", "неизвестная новость")
        except:
            news_title = "неизвестная новость"
        
        # Переключаем видимость новости
        result = api_client.toggle_news_visibility(news_id)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"изменил видимость новости \"{news_title}\"")
        except:
            pass
        
        flash("Видимость новости изменена", category="success")
        
        # Сохраняем состояние фильтра
        show_hidden = request.form.get("show_hidden", "false")
        if show_hidden == "true":
            return redirect(url_for("panel.news_list", show_hidden="true"))
        else:
            return redirect(url_for("panel.news_list"))
        
    except Exception as e:
        logger.error(f"Error toggling news visibility {news_id}: {str(e)}")
        flash("Ошибка при изменении видимости новости", category="error")
        return redirect(url_for("panel.news_list"))


@panel.route("/news/<int:news_id>/image", methods=["GET"], endpoint="news_image")
@login_required
def news_image(news_id):
    try:
        # Получаем изображение новости
        image_data = api_client.download_file(f"/news/{news_id}/image")
        if image_data:
            return send_file(
                io.BytesIO(image_data),
                mimetype='image/jpeg',
                as_attachment=False
            )
        else:
            return "Изображение не найдено", 404
    except Exception as e:
        logger.error(f"Error getting news image {news_id}: {str(e)}")
        return "Ошибка при получении изображения", 404


@panel.route("/reviews", methods=["GET", "POST"], endpoint="reviews_list")
@login_required
@recruiter_restricted
def reviews_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = get_current_user()
        
        try:
            # Получаем все отзывы, включая скрытые
            reviews = api_client.get_reviews(show_hidden=True)
            
            logger.info(f"Loaded {len(reviews)} reviews")
            
            # Форматируем даты
            for review in reviews:
                if "created_at" in review:
                    try:
                        review["created_at"] = datetime.fromisoformat(
                            review["created_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        review["created_at"] = "Неизвестно"
                
                if "updated_at" in review and review["updated_at"]:
                    try:
                        review["updated_at"] = datetime.fromisoformat(
                            review["updated_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        review["updated_at"] = "Неизвестно"
            
            return render_template(
                "panel/reviews/reviews_list.html",
                nav_elements=nav_elements,
                reviews=reviews,
                current_user=current_user
            )
        except Exception as e:
            logger.error(f"Error loading reviews: {str(e)}")
            flash("Ошибка при загрузке отзывов", category="error")
            return render_template(
                "panel/reviews/reviews_list.html",
                nav_elements=nav_elements,
                reviews=[],
                current_user=current_user
            )


@panel.route("/reviews/create", methods=["GET", "POST"], endpoint="review_create")
@login_required
def review_create():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = get_current_user()
        return render_template(
            "panel/reviews/review_form.html",
            nav_elements=nav_elements,
            current_user=current_user
        )
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на создание отзыва", category="error")
            return redirect(url_for("panel.reviews_list"))
        # Получаем данные из формы
        name = request.form.get("name")
        email = request.form.get("email")
        review = request.form.get("review")
        is_approved = request.form.get("is_approved") == "on"
        
        logger.info(f"Creating review with data: name={name}, email={email}, is_approved={is_approved}")
        
        if not all([name, email, review]):
            flash("Заполните все обязательные поля", category="error")
            return redirect(url_for("panel.reviews_list"))
        data = {
            "name": name,
            "email": email,
            "review": review,
            "is_approved": is_approved
        }
        logger.info(f"Sending data to API: {data}")
        result = api_client.create_review(**data)
        logger.info(f"API response: {result}")
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"добавил отзыв от {name}")
        except:
            pass
        flash("Отзыв успешно создан", category="success")
        return redirect(url_for("panel.reviews_list"))
    except Exception as e:
        logger.error(f"Error creating review: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        flash("Ошибка при создании отзыва", category="error")
        return redirect(url_for("panel.reviews_list"))


@panel.route("/reviews/<int:review_id>", methods=["GET"], endpoint="review_detail")
@login_required
def review_detail(review_id):
    try:
        review = api_client.get_review_by_id(review_id)
        return jsonify(review)
    except Exception as e:
        logger.error(f"Error getting review {review_id}: {str(e)}")
        return jsonify({"error": "Отзыв не найден"}), 404


@panel.route("/reviews/<int:review_id>/edit", methods=["POST"], endpoint="review_edit")
@login_required
def review_edit(review_id):
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на редактирование отзыва", category="error")
            return redirect(url_for("panel.reviews_list"))
        # Получаем данные из формы
        name = request.form.get("name")
        email = request.form.get("email")
        review = request.form.get("review")
        is_approved = request.form.get("is_approved") == "on"
        if not all([name, email, review]):
            flash("Заполните все обязательные поля", category="error")
            return redirect(url_for("panel.reviews_list"))
        # Обновляем отзыв
        data = {
            "name": name,
            "email": email,
            "review": review,
            "is_approved": is_approved
        }
        result = api_client.update_review(review_id, **data)
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"отредактировал отзыв от {name}")
        except:
            pass
        flash("Отзыв успешно обновлен", category="success")
        return redirect(url_for("panel.reviews_list"))
    except Exception as e:
        logger.error(f"Error updating review {review_id}: {str(e)}")
        flash("Ошибка при обновлении отзыва", category="error")
        return redirect(url_for("panel.reviews_list"))


@panel.route("/reviews/<int:review_id>/approve", methods=["POST"], endpoint="review_approve")
@login_required
def review_approve(review_id):
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на одобрение отзыва", category="error")
            return redirect(url_for("panel.reviews_list"))
        # Получаем информацию об отзыве для события
        try:
            review = api_client.get_review_by_id(review_id)
            name = review.get("name", "неизвестный автор")
        except:
            name = "неизвестный автор"
        # Одобряем отзыв
        result = api_client.update_review(review_id, is_approved=True)
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"одобрил отзыв от {name}")
        except:
            pass
        flash("Отзыв одобрен", category="success")
        return redirect(url_for("panel.reviews_list", _external=True))
    except Exception as e:
        logger.error(f"Error approving review {review_id}: {str(e)}")
        flash("Ошибка при одобрении отзыва", category="error")
        return redirect(url_for("panel.reviews_list"))


@panel.route("/reviews/<int:review_id>/reject", methods=["POST"])
@login_required
def reject_review(review_id):
    """Отклонить отзыв"""
    try:
        api_client.reject_review(review_id)
        flash("Отзыв отклонен", "success")
    except Exception as e:
        flash(f"Ошибка при отклонении отзыва: {str(e)}", "error")
    
    return redirect(url_for("panel.reviews_list"))


@panel.route("/reviews/<int:review_id>/toggle-visibility", methods=["POST"], endpoint="review_toggle_visibility")
@login_required
def review_toggle_visibility(review_id):
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на изменение видимости отзыва", category="error")
            return redirect(url_for("panel.reviews_list"))
        
        # Получаем текущий отзыв
        review = api_client.get_review_by_id(review_id)
        name = review.get("name", "неизвестный автор")
        
        # Переключаем состояние одобрения
        new_approved_state = not review.get("is_approved", False)
        result = api_client.update_review(review_id, is_approved=new_approved_state)
        
        # Создаем событие
        action_text = "одобрил" if new_approved_state else "скрыл"
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"{action_text} отзыв от {name}")
        except:
            pass
        
        flash(f"Отзыв {'одобрен' if new_approved_state else 'скрыт'}", category="success")
        return redirect(url_for("panel.reviews_list"))
        
    except Exception as e:
        logger.error(f"Error toggling review visibility {review_id}: {str(e)}")
        flash("Ошибка при изменении видимости отзыва", category="error")
        return redirect(url_for("panel.reviews_list"))


@panel.route("/reviews/<int:review_id>/delete", methods=["POST"], endpoint="review_delete")
@login_required
def review_delete(review_id):
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на удаление отзыва", category="error")
            return redirect(url_for("panel.reviews_list"))
        
        # Получаем информацию об отзыве для события
        try:
            review = api_client.get_review_by_id(review_id)
            name = review.get("name", "неизвестный автор")
        except:
            name = "неизвестный автор"
        
        # Удаляем отзыв
        api_client.delete_review(review_id)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"удалил отзыв от {name}")
        except:
            pass
        
        flash("Отзыв успешно удален", category="success")
        return redirect(url_for("panel.reviews_list"))
        
    except Exception as e:
        logger.error(f"Error deleting review {review_id}: {str(e)}")
        flash("Ошибка при удалении отзыва", category="error")
        return redirect(url_for("panel.reviews_list"))


@panel.route("/schedule", methods=["GET", "POST"], endpoint="schedule_list")
@login_required
@recruiter_restricted
def schedule_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = get_current_user()
        
        try:
            # Получаем список колледжей
            colleges = api_client.get_colleges()
            
            # Получаем шаблоны расписаний
            templates = api_client.get_schedule_templates()
            
            # Создаем словарь для быстрого поиска шаблонов по названию колледжа
            templates_dict = {template.get("college_name", ""): template for template in templates}
            
            # Отладочная информация
            logger.info(f"Found {len(templates)} schedule templates")
            for template in templates:
                logger.info(f"Template: {template}")
            
            # Объединяем колледжи с их расписаниями
            colleges_with_schedules = []
            for college in colleges:
                college_name = college.get("name", "")
                template = templates_dict.get(college_name)
                
                college_data = {
                    "id": college.get("id"),
                    "name": college_name,
                    "image_url": college.get("image_url"),
                    "has_schedule": template is not None,
                    "template_id": template.get("id") if template else None,
                    "schedule_template_id": template.get("id") if template else None,  # Дублируем для совместимости
                    "html_content": template.get("html_content") if template else None
                }
                logger.info(f"College {college_name}: has_schedule={college_data['has_schedule']}, template_id={college_data['template_id']}")
                colleges_with_schedules.append(college_data)
            
            # Получаем HTML для первого колледжа с расписанием (если есть)
            schedule_html = ""
            has_schedules = any(college["has_schedule"] for college in colleges_with_schedules)
            
            if has_schedules:
                first_college_with_schedule = next((college for college in colleges_with_schedules if college["has_schedule"]), None)
                if first_college_with_schedule and first_college_with_schedule["html_content"]:
                    schedule_html = first_college_with_schedule["html_content"]
            
            return render_template(
                "panel/schedule/schedule_list.html",
                nav_elements=nav_elements,
                colleges=colleges_with_schedules,
                schedule_html=schedule_html,
                has_schedules=has_schedules,
                current_user=current_user,
                csrf_token=generate_csrf()
            )
        except Exception as e:
            logger.error(f"Error loading schedule: {str(e)}")
            flash("Ошибка при загрузке расписания", category="error")
            return render_template(
                "panel/schedule/schedule_list.html",
                nav_elements=nav_elements,
                colleges=[],
                schedule_html="",
                has_schedules=False,
                current_user=current_user,
                csrf_token=generate_csrf()
            )
    
    elif request.method == "POST":
        # Обработка создания колледжа
        try:
            current_user = get_current_user()
            if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
                flash("У вас нет прав на создание колледжей", category="error")
                return redirect(url_for("panel.schedule_list"))
            
            # Получаем данные формы
            name = request.form.get("name")
            
            if not name:
                flash("Заполните название колледжа", category="error")
                return redirect(url_for("panel.schedule_list"))
            
            # Создаем колледж
            college_data = {
                "name": name
            }
            
            # Обрабатываем изображение, если оно загружено
            if "image" in request.files:
                image_file = request.files["image"]
                if image_file and image_file.filename:
                    college_data["image"] = image_file
            
            result = api_client.create_college(**college_data)
            
            # Создаем событие
            try:
                safe_create_action(current_user.get("username", "Администратор"), f"добавил колледж \"{name}\"")
            except:
                pass
            
            flash("Колледж успешно создан", category="success")
            return redirect(url_for("panel.schedule_list"))
            
        except Exception as e:
            logger.error(f"Error creating college: {str(e)}")
            flash("Ошибка при создании колледжа", category="error")
            return redirect(url_for("panel.schedule_list"))


@panel.route("/users", methods=["GET", "POST"], endpoint="users_list")
@login_required
@recruiter_restricted
def users_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = get_current_user()
        
        # Проверяем права доступа
        if not current_user or not current_user.get("is_superuser"):
            flash("У вас нет прав для просмотра списка пользователей", category="error")
            return redirect(url_for("panel.home"))
        
        try:
            users = api_client.get_users()
            
            # Форматируем даты
            for user in users:
                if "created_at" in user:
                    try:
                        user["created_at"] = datetime.fromisoformat(
                            user["created_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        user["created_at"] = "Неизвестно"
                
                if "updated_at" in user and user["updated_at"]:
                    try:
                        user["updated_at"] = datetime.fromisoformat(
                            user["updated_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        user["updated_at"] = "Неизвестно"
            
            return render_template(
                "panel/users/users_list.html",
                nav_elements=nav_elements,
                users=users,
                current_user=current_user
            )
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}")
            flash("Ошибка при загрузке пользователей", category="error")
            return render_template(
                "panel/users/users_list.html",
                nav_elements=nav_elements,
                users=[],
                current_user=current_user
            )


@panel.route("/users/invite", methods=["POST"], endpoint="user_invite")
@login_required
@admin_restricted
def user_invite():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.get("is_superuser"):
            flash("У вас нет прав для приглашения пользователей", category="error")
            return redirect(url_for("panel.users_list"))
        
        # Получаем данные из JSON
        data = request.get_json()
        email = data.get("email")
        is_recruiter = data.get("is_recruiter", False)
        
        if not email:
            flash("Введите email пользователя", category="error")
            return redirect(url_for("panel.users_list"))
        
        # Приглашаем пользователя
        result = api_client.invite_user(email, is_recruiter=is_recruiter)
        
        # Создаем событие
        try:
            role_text = "работодателя" if is_recruiter else "администратора"
            safe_create_action(current_user.get("username", "Администратор"), f"пригласил {role_text} {email}")
        except:
            pass
        
        flash("Приглашение успешно отправлено", category="success")
        return redirect(url_for("panel.users_list"))
        
    except ValidationError as e:
        logger.error(f"Validation error inviting user: {str(e)}")
        flash(f"Ошибка валидации: {str(e)}", category="error")
        return redirect(url_for("panel.users_list"))
    except APIError as e:
        logger.error(f"API error inviting user: {str(e)}")
        # Используем сообщение от API напрямую
        flash(str(e), category="error")
        return redirect(url_for("panel.users_list"))
    except Exception as e:
        logger.error(f"Error inviting user: {str(e)}")
        flash(f"Ошибка при отправке приглашения: {str(e)}", category="error")
        return redirect(url_for("panel.users_list"))


@panel.route("/auth/resend-invite", methods=["POST"])
@login_required
@admin_restricted
def auth_resend_invite():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.get("is_superuser"):
            flash("У вас нет прав для повторной отправки приглашений", category="error")
            return redirect(url_for("panel.users_list"))
        
        # Получаем данные из JSON
        data = request.get_json()
        email = data.get("email")
        
        if not email:
            flash("Email не указан", category="error")
            return redirect(url_for("panel.users_list"))
        
        # Повторно отправляем приглашение
        result = api_client.resend_invite(email)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"повторно отправил приглашение {email}")
        except:
            pass
        
        flash("Приглашение повторно отправлено", category="success")
        return redirect(url_for("panel.users_list"))
        
    except ValidationError as e:
        logger.error(f"Validation error resending invite: {str(e)}")
        flash(f"Ошибка валидации: {str(e)}", category="error")
        return redirect(url_for("panel.users_list"))
    except APIError as e:
        logger.error(f"API error resending invite: {str(e)}")
        flash(f"Ошибка API: {str(e)}", category="error")
        return redirect(url_for("panel.users_list"))
    except Exception as e:
        logger.error(f"Error resending invite: {str(e)}")
        flash("Ошибка при повторной отправке приглашения", category="error")
        return redirect(url_for("panel.users_list"))


@panel.route("/users/<int:user_id>/delete", methods=["POST"], endpoint="user_delete")
@login_required
@admin_restricted
def user_delete(user_id):
    try:
        current_user = get_current_user()
        if not current_user or not current_user.get("is_superuser"):
            flash("У вас нет прав для удаления пользователей", category="error")
            return redirect(url_for("panel.users_list"))
        
        # Проверяем, что пользователь не удаляет сам себя
        if user_id == current_user.get("id"):
            flash("Вы не можете удалить свой аккаунт", category="error")
            return redirect(url_for("panel.users_list"))
        
        # Получаем информацию о пользователе для события
        try:
            user = api_client.get_user_by_id(user_id)
            user_email = user.get("email", "неизвестный пользователь")
        except:
            user_email = "неизвестный пользователь"
        
        # Удаляем пользователя
        api_client.delete_user(user_id)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"удалил пользователя {user_email}")
        except:
            pass
        
        flash("Пользователь успешно удален", category="success")
        return redirect(url_for("panel.users_list"))
        
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        flash("Ошибка при удалении пользователя", category="error")
        return redirect(url_for("panel.users_list"))


@panel.route("/users/<int:user_id>/edit", methods=["POST"], endpoint="user_edit")
@login_required
@admin_restricted
def user_edit(user_id):
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на редактирование пользователя", category="error")
            return redirect(url_for("panel.users_list"))
        
        # Получаем данные из формы
        data = request.form
        username = data.get("username")
        email = data.get("email")
        role = data.get("role")
        
        if not username or not email:
            flash("Заполните все обязательные поля", category="error")
            return redirect(url_for("panel.users_list"))
        
        # Обновляем пользователя
        user_data = {
            "username": username,
            "email": email,
            "role": role
        }
        
        result = api_client.update_user(user_id, user_data)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"отредактировал пользователя {username}")
        except:
            pass
        
        flash("Пользователь успешно обновлен", category="success")
        return redirect(url_for("panel.users_list"))
        
    except Exception as e:
        logger.error(f"Error editing user {user_id}: {str(e)}")
        flash("Ошибка при обновлении пользователя", category="error")
        return redirect(url_for("panel.users_list"))


@panel.route("/vacancies", methods=["GET", "POST"], endpoint="vacancies_list")
@login_required
def vacancies_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = get_current_user()
        
        try:
            # Получаем вакансии в зависимости от роли пользователя
            if current_user and current_user.get("is_superuser"):
                # Супер-администратор видит все вакансии
                vacancies = api_client.get_vacancies(show_hidden=True)
            elif current_user and current_user.get("is_recruiter"):
                # Работодатель видит только свои вакансии (включая скрытые)
                vacancies = api_client.get_vacancies(show_hidden=True)
            else:
                # Обычные администраторы не видят вакансии
                return redirect(url_for("panel.home"))

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
                    current_user=current_user,
                )
        except Exception as e:
            logger.error(f"Error loading vacancies: {str(e)}")
            flash("Ошибка при загрузке вакансий", category="error")
            return render_template(
                "panel/vacancies/vacancies_list.html",
                nav_elements=nav_elements,
                vacancies=[],
                current_user=current_user,
        )


@panel.route("/vacancies/create", methods=["GET", "POST"], endpoint="vacancy_create")
@login_required
def vacancy_create():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = get_current_user()
        
        # Проверяем права доступа
        if not current_user or (not current_user.get("is_superuser") and not current_user.get("is_recruiter")):
            flash("У вас нет прав на создание вакансий", category="error")
            return redirect(url_for("panel.home"))
        
        return render_template(
            "panel/vacancies/vacancy_form.html",
            nav_elements=nav_elements,
            vacancy=None,
            is_edit=False,
        )

    if request.method == "POST":
        try:
            current_user = get_current_user()
            # Проверяем права доступа
            if not current_user or (not current_user.get("is_superuser") and not current_user.get("is_recruiter")):
                flash("У вас нет прав на создание вакансий", category="error")
                return redirect(url_for("panel.home"))
            
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

            # Функция для безопасного преобразования строки в int
            def safe_int(value):
                if not value or value.strip() == "":
                    return None
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return None

            data = {
                "title": request.form.get("title"),
                "description": request.form.get("description"),
                "direction": request.form.get("direction"),
                "speciality": request.form.get("speciality"),
                "requirements": request.form.get("requirements"),
                "work_format": request.form.get("work_format"),
                "start": start_date if start_date else None,
                "end": end_date if end_date else None,
                "chart": request.form.get("chart"),
                "company_name": request.form.get("company_name"),
                "contact_person": request.form.get("contact_person"),
                "required_amount": int(request.form.get("required_amount", 1)),
                "is_hidden": request.form.get("is_hidden") == "on",
                "is_internship": request.form.get("is_internship") == "true",
                "salary_from": safe_int(request.form.get("salary_from")),
                "salary_to": safe_int(request.form.get("salary_to")),
                "city": request.form.get("city"),
                "metro_station": request.form.get("metro_station"),
                "address": request.form.get("address"),
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
        current_user = get_current_user()
        
        # Проверяем права доступа
        if not current_user or (not current_user.get("is_superuser") and not current_user.get("is_recruiter")):
            flash("У вас нет прав на редактирование вакансий", category="error")
            return redirect(url_for("panel.home"))
        
        vacancy = api_client.get_vacancy(vacancy_id)
        return render_template(
            "panel/vacancies/vacancy_form.html",
            nav_elements=nav_elements,
            vacancy=vacancy,
            is_edit=True,
        )

    if request.method == "POST":
        try:
            current_user = get_current_user()
            # Проверяем права доступа
            if not current_user or (not current_user.get("is_superuser") and not current_user.get("is_recruiter")):
                flash("У вас нет прав на редактирование вакансий", category="error")
                return redirect(url_for("panel.home"))
            
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

            # Функция для безопасного преобразования строки в int
            def safe_int(value):
                if not value or value.strip() == "":
                    return None
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return None

            data = {
                "title": request.form.get("title"),
                "description": request.form.get("description"),
                "direction": request.form.get("direction"),
                "speciality": request.form.get("speciality"),
                "requirements": request.form.get("requirements"),
                "work_format": request.form.get("work_format"),
                "start": start_date if start_date else None,
                "end": end_date if end_date else None,
                "chart": request.form.get("chart"),
                "company_name": request.form.get("company_name"),
                "contact_person": request.form.get("contact_person"),
                "required_amount": int(request.form.get("required_amount", 1)),
                "is_hidden": request.form.get("is_hidden") == "on",
                "is_internship": request.form.get("is_internship") == "true",
                "salary_from": safe_int(request.form.get("salary_from")),
                "salary_to": safe_int(request.form.get("salary_to")),
                "city": request.form.get("city"),
                "metro_station": request.form.get("metro_station"),
                "address": request.form.get("address"),
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
        current_user = get_current_user()
        # Проверяем права доступа
        if not current_user or (not current_user.get("is_superuser") and not current_user.get("is_recruiter")):
            flash("У вас нет прав на удаление вакансий", category="error")
            return redirect(url_for("panel.home"))
        
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
        current_user = get_current_user()
        
        # Проверяем права доступа
        if not current_user or (not current_user.get("is_superuser") and not current_user.get("is_recruiter")):
            flash("У вас нет прав на просмотр заявок", category="error")
            return redirect(url_for("panel.home"))
        
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
            current_user = get_current_user()
            # Проверяем права доступа
            if not current_user or (not current_user.get("is_superuser") and not current_user.get("is_recruiter")):
                flash("У вас нет прав на управление заявками", category="error")
                return redirect(url_for("panel.home"))
            
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
    current_user = get_current_user()
    # Проверяем права доступа
    if not current_user or (not current_user.get("is_superuser") and not current_user.get("is_recruiter")):
        flash("У вас нет прав на скачивание резюме", category="error")
        return redirect(url_for("panel.home"))
    
    student_id = request.args.get("student_id")
    student_full_name = "_".join(request.args.get("student_full_name").split())
    file_extension = request.args.get("extension", ".pdf")  # Получаем расширение из параметра
    
    if not student_id:
        flash("Не указан студент", "error")
        return redirect(url_for("panel.vacancies_list"))

    file_data = api_client.download_file(f"/students/{student_id}/resume-file")
    if not file_data:
        flash("Файл резюме не найден", "error")
        return redirect(url_for("panel.vacancies_list"))

    if isinstance(file_data, bytes):
        file_data = io.BytesIO(file_data)

    filename = f"resume_{student_full_name}{file_extension}"

    return send_file(
        file_data,
        as_attachment=True,
        download_name=filename,
    )


@panel.route("/vacancies/<int:vacancy_id>/activate", methods=["POST"], endpoint="vacancy_activate")
@login_required
def vacancy_activate(vacancy_id):
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.vacancies_list"))
        
        # Проверяем права доступа
        if not current_user.get("is_superuser") and not current_user.get("is_recruiter"):
            flash("У вас нет прав на активацию вакансий", category="error")
            return redirect(url_for("panel.home"))
        
        # Активируем вакансию
        api_client.activate_vacancy(vacancy_id)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), "активировал вакансию")
        except:
            pass
        
        flash("Вакансия успешно активирована", category="success")
        return redirect(url_for("panel.vacancies_list"))
        
    except Exception as e:
        logger.error(f"Error activating vacancy {vacancy_id}: {str(e)}")
        flash("Ошибка при активации вакансии", category="error")
        return redirect(url_for("panel.vacancies_list"))


@panel.route("/vacancies/<int:vacancy_id>/deactivate", methods=["POST"], endpoint="vacancy_deactivate")
@login_required
def vacancy_deactivate(vacancy_id):
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.vacancies_list"))
        
        # Проверяем права доступа
        if not current_user.get("is_superuser") and not current_user.get("is_recruiter"):
            flash("У вас нет прав на деактивацию вакансий", category="error")
            return redirect(url_for("panel.home"))
        
        # Деактивируем вакансию
        api_client.deactivate_vacancy(vacancy_id)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), "деактивировал вакансию")
        except:
            pass
        
        flash("Вакансия успешно деактивирована", category="success")
        return redirect(url_for("panel.vacancies_list"))
        
    except Exception as e:
        logger.error(f"Error deactivating vacancy {vacancy_id}: {str(e)}")
        flash("Ошибка при деактивации вакансии", category="error")
        return redirect(url_for("panel.vacancies_list"))


@panel.route("/applications/<int:application_id>/delete", methods=["POST"], endpoint="application_delete")
@login_required
def application_delete(application_id):
    try:
        current_user = get_current_user()
        # Проверяем права доступа - только супер-администраторы могут удалять заявки
        if not current_user or not current_user.get("is_superuser"):
            flash("У вас нет прав на удаление заявок", category="error")
            return redirect(url_for("panel.home"))
        
        api_client.delete_student(application_id)
        flash("Заявка успешно удалена", category="success")
    except (ValidationError, APIError) as e:
        flash(str(e), category="error")

    return redirect(url_for("panel.vacancies_list"))





@panel.route("/schedule/template/<college_name>")
@login_required
def get_schedule_template_by_college(college_name):
    try:
        template_data = api_client.get_schedule_template_by_college(college_name)
        return jsonify(template_data)
    except Exception as e:
        logger.error(f"Error getting schedule template for {college_name}: {str(e)}")
        return jsonify({"error": "Шаблон не найден"}), 404


@panel.route("/schedule/templates/<int:template_id>/delete", methods=["POST"])
@login_required
def delete_schedule_template(template_id):
    try:
        logger.info(f"=== DELETE SCHEDULE TEMPLATE REQUEST ===")
        logger.info(f"Template ID: {template_id}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request form data: {dict(request.form)}")
        logger.info(f"Request args: {dict(request.args)}")
        
        # Проверяем CSRF токен
        csrf_token = request.form.get('csrf_token')
        logger.info(f"CSRF token received: {csrf_token is not None}")
        if not csrf_token:
            logger.error("CSRF token missing")
            flash("Ошибка безопасности", "error")
            return redirect(url_for("panel.schedule_list"))
        
        logger.info(f"CSRF token validated, calling API to delete template {template_id}")
        
        # Удаляем шаблон через API
        result = api_client.delete_schedule_template(template_id)
        logger.info(f"API call successful, result: {result}")
        
        flash("Расписание успешно удалено", "success")
    except NotFoundError as e:
        logger.error(f"Schedule template {template_id} not found: {str(e)}")
        flash("Расписание не найдено", "error")
    except Exception as e:
        logger.error(f"Error deleting schedule template {template_id}: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f"Ошибка при удалении расписания: {str(e)}", "error")
    
    return redirect(url_for("panel.schedule_list"))


@panel.route("/schedule/delete-all-templates", methods=["POST"])
@login_required
def delete_all_schedule_templates():
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            flash("У вас нет прав на удаление шаблонов расписаний", category="error")
            return redirect(url_for("panel.schedule_list"))
        
        # Удаляем все шаблоны
        result = api_client.delete_all_schedule_templates()
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), "удалил все шаблоны расписаний")
        except:
            pass
        
        flash("Все шаблоны расписаний удалены", category="success")
        return redirect(url_for("panel.schedule_list"))
        
    except Exception as e:
        logger.error(f"Error deleting all schedule templates: {str(e)}")
        flash("Ошибка при удалении шаблонов расписаний", category="error")
        return redirect(url_for("panel.schedule_list"))


@panel.route("/partners", methods=["GET", "POST"], endpoint="partners_list")
@login_required
@recruiter_restricted
def partners_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = get_current_user()
        
        try:
            partners = api_client.get_partners(show_hidden=True)
            
            # Форматируем даты
            for partner in partners:
                if "created_at" in partner:
                    try:
                        partner["created_at"] = datetime.fromisoformat(
                            partner["created_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        partner["created_at"] = "Неизвестно"
                
                if "updated_at" in partner and partner["updated_at"]:
                    try:
                        partner["updated_at"] = datetime.fromisoformat(
                            partner["updated_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        partner["updated_at"] = "Неизвестно"
            
            return render_template(
                "panel/partners/partners_list.html",
                nav_elements=nav_elements,
                partners=partners,
                current_user=current_user
            )
        except Exception as e:
            logger.error(f"Error loading partners: {str(e)}")
            flash("Ошибка при загрузке партнеров", category="error")
            return render_template(
                "panel/partners/partners_list.html",
                nav_elements=nav_elements,
                partners=[],
                current_user=current_user
            )


@panel.route("/partners/create", methods=["POST"], endpoint="partner_create")
@login_required
def partner_create():
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.partners_list"))
        
        name = request.form.get("name")
        description = request.form.get("description")
        is_active = request.form.get("is_active") == "on"
        
        if not name:
            flash("Название партнера обязательно", category="error")
            return redirect(url_for("panel.partners_list"))
        
        # Обрабатываем изображение
        image = request.files.get("image")
        data = {
            "name": name,
            "description": description,
            "is_active": is_active
        }
        
        if image and image.filename:
            # Читаем файл один раз
            image_data = image.read()
            files = {"image": (image.filename, image_data, image.content_type)}
            data.update(files)
        
        result = api_client.create_partner(**data)
        
        if result:
            flash("Партнер успешно создан", category="success")
            
            # Создаем событие
            try:
                safe_create_action(current_user.get("username", "Администратор"), f'создал партнера: "{name}"')
            except:
                pass
        else:
            flash("Ошибка при создании партнера", category="error")
        
        return redirect(url_for("panel.partners_list"))
        
    except Exception as e:
        logger.error(f"Error creating partner: {str(e)}")
        flash("Ошибка при создании партнера", category="error")
        return redirect(url_for("panel.partners_list"))


@panel.route("/partners/<int:partner_id>/edit", methods=["POST"], endpoint="partner_edit")
@login_required
def partner_edit(partner_id):
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.partners_list"))
        
        name = request.form.get("name")
        description = request.form.get("description")
        is_active = request.form.get("is_active") == "on"
        remove_image = request.form.get("remove_image") == "on"
        
        if not name:
            flash("Название партнера обязательно", category="error")
            return redirect(url_for("panel.partners_list"))
        
        # Обрабатываем изображение
        image = request.files.get("image")
        data = {
            "name": name,
            "description": description,
            "is_active": is_active
        }
        
        if remove_image:
            data["remove_image"] = "true"
        elif image and image.filename:
            # Читаем файл один раз
            image_data = image.read()
            files = {"image": (image.filename, image_data, image.content_type)}
            data.update(files)
        
        result = api_client.update_partner(partner_id, **data)
        
        if result:
            flash("Партнер успешно обновлен", category="success")
            
            # Создаем событие
            try:
                safe_create_action(current_user.get("username", "Администратор"), f'обновил партнера: "{name}"')
            except:
                pass
        else:
            flash("Ошибка при обновлении партнера", category="error")
        
        return redirect(url_for("panel.partners_list"))
        
    except Exception as e:
        logger.error(f"Error updating partner: {str(e)}")
        flash("Ошибка при обновлении партнера", category="error")
        return redirect(url_for("panel.partners_list"))


@panel.route("/partners/<int:partner_id>/delete", methods=["POST"], endpoint="partner_delete")
@login_required
def partner_delete(partner_id):
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.partners_list"))
        
        # Получаем информацию о партнере перед удалением
        partner = api_client.get_partner(partner_id)
        partner_name = partner.get("name", "Неизвестный партнер") if partner else "Неизвестный партнер"
        
        result = api_client.delete_partner(partner_id)
        
        if result:
            flash("Партнер успешно удален", category="success")
            
            # Создаем событие
            try:
                safe_create_action(current_user.get("username", "Администратор"), f'удалил партнера: "{partner_name}"')
            except:
                pass
        else:
            flash("Ошибка при удалении партнера", category="error")
        
        return redirect(url_for("panel.partners_list"))
        
    except Exception as e:
        logger.error(f"Error deleting partner: {str(e)}")
        flash("Ошибка при удалении партнера", category="error")
        return redirect(url_for("panel.partners_list"))


@panel.route("/partners/<int:partner_id>", methods=["GET"], endpoint="partner_detail")
@login_required
def partner_detail(partner_id):
    try:
        partner = api_client.get_partner(partner_id)
        if partner:
            return jsonify(partner)
        else:
            return jsonify({"error": "Партнер не найден"}), 404
    except Exception as e:
        logger.error(f"Error getting partner {partner_id}: {str(e)}")
        return jsonify({"error": "Ошибка при получении данных партнера"}), 500


@panel.route("/partners/<int:partner_id>/image", methods=["GET"], endpoint="partner_image")
@login_required
def partner_image(partner_id):
    try:
        partner = api_client.get_partner(partner_id)
        if partner and partner.get("image_url"):
            # Перенаправляем на изображение с бэкенда
            backend_url = f"{api_client.base_url}/api/v1/partners/{partner_id}/image"
            response = requests.get(backend_url, stream=True)
            if response.status_code == 200:
                return Response(response.iter_content(chunk_size=1024), 
                              content_type=response.headers.get('content-type', 'image/jpeg'))
            else:
                return "Изображение не найдено", 404
        else:
            return "Изображение не найдено", 404
    except Exception as e:
        logger.error(f"Error getting partner image {partner_id}: {str(e)}")
        return "Ошибка при получении изображения", 500


@panel.route("/partners/<int:partner_id>/toggle-visibility", methods=["POST"], endpoint="partner_toggle_visibility")
@login_required
def partner_toggle_visibility(partner_id):
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.partners_list"))
        
        result = api_client.toggle_partner_visibility(partner_id)
        
        if result:
            status = "активировал" if result.get("is_active") else "деактивировал"
            flash(f"Партнер {status}", category="success")
            
            # Создаем событие
            try:
                safe_create_action(current_user.get("username", "Администратор"), f'{status} партнера: "{result.get("name", "")}"')
            except:
                pass
        else:
            flash("Ошибка при изменении статуса партнера", category="error")
        
        return redirect(url_for("panel.partners_list"))
        
    except Exception as e:
        logger.error(f"Error toggling partner visibility: {str(e)}")
        flash("Ошибка при изменении статуса партнера", category="error")
        return redirect(url_for("panel.partners_list"))


# Роуты для управления колледжами
@panel.route("/colleges", methods=["GET", "POST"], endpoint="colleges_list")
@login_required
@recruiter_restricted
def colleges_list():
    if request.method == "GET":
        nav_elements = get_navigation_elements()
        current_user = get_current_user()
        
        try:
            colleges = api_client.get_colleges()
            
            # Форматируем даты
            for college in colleges:
                if "created_at" in college:
                    try:
                        college["created_at"] = datetime.fromisoformat(
                            college["created_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        college["created_at"] = "Неизвестно"
                
                if "updated_at" in college and college["updated_at"]:
                    try:
                        college["updated_at"] = datetime.fromisoformat(
                            college["updated_at"].replace("Z", "+00:00")
                        ).strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        college["updated_at"] = "Неизвестно"
            
            return render_template(
                "panel/colleges/colleges_list.html",
                nav_elements=nav_elements,
                colleges=colleges,
                current_user=current_user
            )
        except Exception as e:
            logger.error(f"Error loading colleges: {str(e)}")
            flash("Ошибка при загрузке колледжей", category="error")
            return render_template(
                "panel/colleges/colleges_list.html",
                nav_elements=nav_elements,
                colleges=[],
                current_user=current_user
            )


@panel.route("/colleges/create", methods=["POST"], endpoint="college_create")
@login_required
def college_create():
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.colleges_list"))
        
        name = request.form.get("name")
        image = request.files.get("image")
        
        # HTML5 валидация будет показывать "Заполните это поле."
        # если поля не заполнены, поэтому здесь просто создаем колледж
        
        try:
            # Создаем колледж с изображением
            data = {"name": name, "image": image}
            
            result = api_client.create_college(**data)
            
            flash("Колледж успешно создан", category="success")
            
            # Создаем событие
            try:
                safe_create_action(current_user.get("username", "Администратор"), f'создал колледж: "{name}"')
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error creating college: {str(e)}")
            flash("Ошибка при создании колледжа", category="error")
        
        return redirect(url_for("panel.colleges_list"))
        
    except Exception as e:
        logger.error(f"Error creating college: {str(e)}")
        flash("Ошибка при создании колледжа", category="error")
        return redirect(url_for("panel.colleges_list"))


@panel.route("/colleges/<int:college_id>/edit", methods=["POST"], endpoint="college_edit")
@login_required
def college_edit(college_id):
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.colleges_list"))
        
        name = request.form.get("name")
        remove_image = request.form.get("remove_image") == "on"
        
        # HTML5 валидация будет показывать "Заполните это поле."
        # если поля не заполнены, поэтому здесь просто обновляем колледж
        
        # Обрабатываем изображение
        image = request.files.get("image")
        data = {
            "name": name
        }
        
        if remove_image:
            data["remove_image"] = "true"
        elif image and image.filename:
            data["image"] = image
        
        result = api_client.update_college(college_id, **data)
        
        if result:
            flash("Колледж успешно обновлен", category="success")
            
            # Создаем событие
            try:
                safe_create_action(current_user.get("username", "Администратор"), f'обновил колледж: "{name}"')
            except:
                pass
        else:
            flash("Ошибка при обновлении колледжа", category="error")
        
        return redirect(url_for("panel.colleges_list"))
        
    except Exception as e:
        logger.error(f"Error updating college: {str(e)}")
        flash("Ошибка при обновлении колледжа", category="error")
        return redirect(url_for("panel.colleges_list"))


@panel.route("/colleges/<int:college_id>/delete", methods=["POST"], endpoint="college_delete")
@login_required
def college_delete(college_id):
    try:
        current_user = get_current_user()
        if not current_user:
            flash("Ошибка аутентификации", category="error")
            return redirect(url_for("panel.schedule_list"))
        
        # Проверяем CSRF токен
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            logger.error("CSRF token missing in college delete")
            flash("Ошибка безопасности", "error")
            return redirect(url_for("panel.schedule_list"))
        
        # Получаем информацию о колледже перед удалением
        college = api_client.get_college(college_id)
        college_name = college.get("name", "Неизвестный колледж") if college else "Неизвестный колледж"
        
        result = api_client.delete_college(college_id)
        
        if result:
            flash("Колледж успешно удален", category="success")
            
            # Создаем событие
            try:
                safe_create_action(current_user.get("username", "Администратор"), f'удалил колледж: "{college_name}"')
            except:
                pass
        else:
            flash("Ошибка при удалении колледжа", category="error")
        
        return redirect(url_for("panel.schedule_list"))
        
    except Exception as e:
        logger.error(f"Error deleting college: {str(e)}")
        flash("Ошибка при удалении колледжа", category="error")
        return redirect(url_for("panel.schedule_list"))


@panel.route("/colleges/<int:college_id>", methods=["GET"], endpoint="college_detail")
@login_required
def college_detail(college_id):
    try:
        college = api_client.get_college(college_id)
        if college:
            return jsonify(college)
        else:
            return jsonify({"error": "Колледж не найден"}), 404
    except Exception as e:
        logger.error(f"Error getting college {college_id}: {str(e)}")
        return jsonify({"error": "Ошибка при получении данных колледжа"}), 500


@panel.route("/colleges/<int:college_id>/image", methods=["GET"], endpoint="college_image")
@login_required
def college_image(college_id):
    try:
        college = api_client.get_college(college_id)
        if college and college.get("image_url"):
            # Перенаправляем на изображение с бэкенда
            backend_url = f"{api_client.base_url}/api/v1/colleges/{college_id}/image"
            response = requests.get(backend_url, stream=True)
            if response.status_code == 200:
                return Response(response.iter_content(chunk_size=1024), 
                              content_type=response.headers.get('content-type', 'image/jpeg'))
            else:
                return "Изображение не найдено", 404
        else:
            return "Изображение не найдено", 404
    except Exception as e:
        logger.error(f"Error getting college image {college_id}: {str(e)}")
        return "Ошибка при получении изображения", 500





@panel.route("/api/schedule/templates/<college_name>")
@login_required
def api_get_schedule_template(college_name):
    try:
        backend_url = f"{api_client.base_url}/api/v1/schedule/templates/{college_name}"
        resp = requests.get(backend_url)
        if resp.status_code == 200:
            return resp.text
        else:
            return f"<div class='error'>Ошибка загрузки расписания для {college_name}</div>"
    except Exception as e:
        logger.error(f"Error getting schedule template for {college_name}: {str(e)}")
        return f"<div class='error'>Ошибка получения шаблона: {str(e)}</div>"


# API маршруты для управления колледжами
@panel.route("/api/colleges", methods=["POST"])
@login_required
def api_create_college():
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            return jsonify({"error": "У вас нет прав на создание колледжей"}), 403
        
        # Получаем данные формы
        name = request.form.get("name")
        
        if not name:
            return jsonify({"error": "Заполните название колледжа"}), 400
        
        # Создаем колледж
        college_data = {
            "name": name
        }
        
        # Обрабатываем изображение, если оно загружено
        if "image" in request.files:
            image_file = request.files["image"]
            if image_file and image_file.filename:
                # Читаем файл один раз
                image_data = image_file.read()
                college_data["image"] = (image_file.filename, image_data, image_file.content_type)
        
        result = api_client.create_college(**college_data)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"добавил колледж \"{name}\"")
        except:
            pass
        
        return jsonify({"success": True, "message": "Колледж успешно создан"})
        
    except Exception as e:
        logger.error(f"Error creating college: {str(e)}")
        return jsonify({"error": "Ошибка при создании колледжа"}), 500


@panel.route("/api/colleges/<int:college_id>", methods=["PUT"])
@login_required
def api_update_college(college_id):
    try:
        current_user = get_current_user()
        if not current_user or (not current_user.get("is_superuser") and current_user.get("is_recruiter")):
            return jsonify({"error": "У вас нет прав на редактирование колледжей"}), 403
        
        # Получаем данные формы
        name = request.form.get("name")
        
        if not name:
            return jsonify({"error": "Заполните название колледжа"}), 400
        
        # Обновляем колледж
        college_data = {
            "name": name
        }
        
        # Обрабатываем изображение, если оно загружено
        if "image" in request.files:
            image_file = request.files["image"]
            if image_file and image_file.filename:
                # Читаем файл один раз
                image_data = image_file.read()
                college_data["image"] = (image_file.filename, image_data, image_file.content_type)
        
        # Обрабатываем удаление изображения
        if request.form.get("remove_image") == "on":
            college_data["remove_image"] = True
        
        result = api_client.update_college(college_id, **college_data)
        
        # Создаем событие
        try:
            safe_create_action(current_user.get("username", "Администратор"), f"отредактировал колледж \"{name}\"")
        except:
            pass
        
        return jsonify({"success": True, "message": "Колледж успешно обновлен"})
        
    except Exception as e:
        logger.error(f"Error updating college {college_id}: {str(e)}")
        return jsonify({"error": "Ошибка при обновлении колледжа"}), 500


# Удаляем этот маршрут, так как теперь используется Flask-форма
# @panel.route("/api/colleges/<int:college_id>", methods=["DELETE"])
# @login_required
# def api_delete_college(college_id):
#     # Этот маршрут больше не используется
#     pass





# --- универсальная обрезка action для всех событий ---
def safe_create_action(username, action):
    if action and len(action) > 110:
        action = action[:107] + '...'
    return api_client.create_action(username=username, action=action)


@panel.route("/api/schedule/upload-excel", methods=["POST"])
@login_required
def api_upload_schedule_excel():
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Ошибка аутентификации"}), 401
        
        # Проверяем, что файл был загружен
        if "file" not in request.files:
            return jsonify({"error": "Файл не выбран"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Файл не выбран"}), 400
        
        # Проверяем расширение файла
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({"error": "Поддерживаются только файлы Excel (.xlsx, .xls)"}), 400
        
        # Отправляем файл на backend
        files = {"file": (file.filename, file.read(), file.content_type)}
        result = api_client.upload_schedule_excel(files)
        
        # Создаем событие
        try:
            action_text = f'загрузил Excel файл с расписаниями: {file.filename}'
            if len(action_text) > 50:
                action_text = action_text[:47] + '...'
            safe_create_action(current_user.get("username", "Администратор"), action_text)
        except:
            pass
        
        return jsonify({"status": "success", "message": "Расписание успешно загружено"})
        
    except Exception as e:
        logger.error(f"Error uploading schedule: {str(e)}")
        return jsonify({"error": f"Ошибка при загрузке расписания: {str(e)}"}), 500