import requests
from datetime import datetime
from urllib.parse import urljoin
from flask import session
from requests.exceptions import RequestException
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


class APIError(Exception):
    """Базовый класс для ошибок API"""

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(APIError):
    """Ошибка аутентификации"""

    pass


class PermissionError(APIError):
    """Ошибка прав доступа"""

    pass


class ValidationError(APIError):
    """Ошибка валидации данных"""

    pass


class NotFoundError(APIError):
    """Ошибка - ресурс не найден"""

    pass


class APIClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        logger.debug(f"APIClient initialized with base_url: {base_url}")

    @property
    def access_token(self) -> str | None:
        """Получить текущий access токен из сессии"""
        if self._access_token is None:
            self._access_token = session.get("access_token")
            logger.debug(
                f"Access token retrieved from session: {'present' if self._access_token else 'missing'}"
            )
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        """Получить текущий refresh токен из сессии"""
        if self._refresh_token is None:
            self._refresh_token = session.get("refresh_token")
            logger.debug(
                f"Refresh token retrieved from session: {'present' if self._refresh_token else 'missing'}"
            )
        return self._refresh_token

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _handle_error_response(self, response: requests.Response) -> None:
        """Обработка ошибок от API"""
        try:
            error_data = response.json()
            error_message = error_data.get("detail", "Неизвестная ошибка")
        except ValueError:
            error_message = response.text or "Неизвестная ошибка"

        logger.error(
            f"API Error: Status {response.status_code}, Message: {error_message}"
        )
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response content: {response.text}")

        if response.status_code == 401:
            raise AuthenticationError(error_message, status_code=response.status_code)
        elif response.status_code == 403:
            raise PermissionError(error_message, status_code=response.status_code)
        elif response.status_code == 404:
            raise NotFoundError(error_message, status_code=response.status_code)
        elif response.status_code == 400:
            raise ValidationError(error_message, status_code=response.status_code)
        else:
            raise APIError(error_message, status_code=response.status_code)

    def _save_tokens_to_session(self, access_token: str, refresh_token: str) -> None:
        """Сохранить токены в сессию Flask"""
        session["access_token"] = access_token
        session["refresh_token"] = refresh_token
        self._access_token = access_token
        self._refresh_token = refresh_token
        logger.debug("Tokens saved to session")

    def _clear_tokens(self) -> None:
        """Очистить токены из сессии и из клиента"""
        if "access_token" in session:
            session.pop("access_token")
        if "refresh_token" in session:
            session.pop("refresh_token")
        self._access_token = None
        self._refresh_token = None
        logger.debug("Tokens cleared from session")

    def _refresh_access_token(self) -> bool:
        """Обновить access токен с помощью refresh токена"""
        if not self.refresh_token:
            logger.warning("No refresh token available")
            return False

        try:
            url = f"{settings.API_URL}/api/v1/auth/refresh"
            data = {"refresh_token": self.refresh_token}

            logger.debug("Attempting to refresh access token")
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.error(f"Failed to refresh token: {response.status_code}")
                return False

            data = response.json()
            self._save_tokens_to_session(data["access_token"], data["refresh_token"])
            logger.debug("Access token refreshed successfully")
            return True

        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return False

    def _make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Выполнить аутентифицированный запрос с автоматическим обновлением токена"""
        logger.info(f"=== _make_authenticated_request ===")
        logger.info(f"Method: {method}")
        logger.info(f"URL: {url}")
        logger.info(f"Kwargs keys: {list(kwargs.keys())}")
        
        # Подготавливаем заголовки
        headers = kwargs.get('headers', {}).copy()
        if not headers:
            headers = self.headers.copy()
        
        logger.info(f"Headers: {headers}")
        
        # Удаляем Content-Type для multipart запросов
        if 'files' in kwargs:
            headers.pop('Content-Type', None)
            logger.info("Removed Content-Type for multipart request")
        
        kwargs['headers'] = headers
        
        logger.info("Making initial request...")
        response = requests.request(method, url, **kwargs)
        logger.info(f"Initial response status: {response.status_code}")
        
        # Если получили 401 и включено автоматическое обновление токенов
        if response.status_code == 401 and settings.AUTO_REFRESH_TOKENS:
            logger.info("Received 401, attempting to refresh token")
            if self._refresh_access_token():
                logger.info("Token refreshed successfully, retrying request")
                # Обновляем заголовки с новым токеном
                headers = kwargs.get('headers', {}).copy()
                if not headers:
                    headers = self.headers.copy()
                if 'files' in kwargs:
                    headers.pop('Content-Type', None)
                kwargs['headers'] = headers
                # Повторяем запрос с новым токеном
                response = requests.request(method, url, **kwargs)
                logger.info(f"Retry response status: {response.status_code}")
            else:
                logger.error("Failed to refresh token")
                # Не удалось обновить токен, очищаем сессию
                self._clear_tokens()
                raise AuthenticationError("Не удалось обновить токен доступа")
        
        logger.info(f"Final response status: {response.status_code}")
        return response

    def login(self, username: str, password: str) -> dict[str, any]:
        """Аутентификация пользователя"""
        url = f"{settings.API_URL}/api/v1/auth/login"
        data = {
            "username": username,
            "password": password,
        }

        try:
            logger.debug(f"Attempting login for user: {username}")
            response = requests.post(
                url,
                data=data,  # используем data вместо json для совместимости с OAuth2PasswordRequestForm
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.timeout,
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            data = response.json()
            self._save_tokens_to_session(data["access_token"], data["refresh_token"])
            logger.debug("Login successful")
            return data

        except RequestException as e:
            logger.error(f"Network error during login: {str(e)}")
            raise APIError(f"Ошибка сети при попытке входа: {str(e)}")

    def register(
        self, email: str, username: str, password: str, token: str
    ) -> dict[str, any]:
        """Регистрация пользователя по токену из email"""
        url = f"{settings.API_URL}/api/v1/auth/register"
        data = {
            "email": email,
            "username": username,
            "password": password,
            "token": token,
        }

        try:
            logger.debug(
                f"Attempting registration for email: {email}, username: {username}"
            )
            logger.debug(f"Registration URL: {url}")
            logger.debug(f"Registration data: {data}")

            response = requests.post(url, json=data, timeout=self.timeout)

            logger.debug(f"Registration response status: {response.status_code}")
            logger.debug(f"Registration response headers: {response.headers}")
            logger.debug(f"Registration response content: {response.text}")

            if response.status_code != 200:
                self._handle_error_response(response)

            data = response.json()
            self._save_tokens_to_session(data["access_token"], data["refresh_token"])
            logger.debug("Registration successful")
            return data

        except RequestException as e:
            logger.error(f"Network error during registration: {str(e)}")
            raise APIError(f"Ошибка сети при попытке регистрации: {str(e)}")

    def forgot_password(self, email: str) -> dict[str, any]:
        """Отправить пользователю ссылку для смены пароля"""
        url = f"{settings.API_URL}/api/v1/password/forgot-password"
        data = {"email": email}

        try:
            response = self._make_authenticated_request(
                "POST", url, json=data, timeout=self.timeout
            )
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(
                f"Ошибка сети при попытке отправки письма для смены пароля: {str(e)}"
            )

    def reset_password(self, token: str, new_password: str) -> None:
        """Сброс пароля по токену"""
        url = f"{settings.API_URL}/api/v1/password/reset-password"
        data = {"token": token, "new_password": new_password}

        try:
            response = self._make_authenticated_request(
                "POST", url, json=data, timeout=self.timeout
            )
            if response.status_code != 200:
                self._handle_error_response(response)
        except RequestException as e:
            raise APIError(f"Ошибка сети при сбросе пароля: {str(e)}")

    def invite_user(self, email: str, is_recruiter: bool = False) -> dict[str, any]:
        """Пригласить нового пользователя"""
        url = f"{settings.API_URL}/api/v1/auth/invite"
        data = {"email": email, "is_recruiter": is_recruiter}

        try:
            response = self._make_authenticated_request(
                "POST", url, json=data, timeout=self.timeout
            )
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            logger.error(f"Network error during invitation: {str(e)}")
            raise APIError(f"Ошибка сети при попытке приглашения: {str(e)}")

    def resend_invite(self, email: str) -> dict[str, any]:
        """Повторно отправить приглашение пользователю"""
        url = f"{settings.API_URL}/api/v1/auth/resend-invite"
        data = {"email": email}

        try:
            response = self._make_authenticated_request(
                "POST", url, json=data, timeout=self.timeout
            )
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            logger.error(f"Network error during invitation: {str(e)}")
            raise APIError(f"Ошибка сети при попытке повторной отправки приглашения: {str(e)}")

    def get_current_user(self) -> dict[str, any]:
        """Получить информацию о пользователе, зашедшего в админ-панель"""
        if not self.access_token:
            raise AuthenticationError("Требуется аутентификация пользователя")

        url = f"{settings.API_URL}/api/v1/users/me"
        try:
            response = self._make_authenticated_request("GET", url, timeout=self.timeout)
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети при получении информации о пользователе: {str(e)}")

    def logout(self) -> None:
        """Выход пользователя"""
        self._clear_tokens()

    def create_action(self, username: str, action: str) -> dict[str, any]:
        """Создание нового события (выполняется каждый раз при любом действии пользователя: создание новости, редактирование расписания и т.д.)"""
        if not self.access_token:
            raise AuthenticationError("Требуется аутентификация пользователя")

        url = f"{settings.API_URL}/api/v1/actions/"
        data = {"username": username, "action": action}

        try:
            response = self._make_authenticated_request(
                "POST", url, json=data, timeout=self.timeout
            )
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети при создании события: {str(e)}")

    def get_actions(self, limit: int = 10) -> list[dict[str, any]]:
        """Получить список событий с преобразованным временем"""
        if not self.access_token:
            raise AuthenticationError("Требуется аутентификация пользователя")

        url = f"{settings.API_URL}/api/v1/actions/"
        params = {"limit": limit}

        try:
            response = self._make_authenticated_request(
                "GET", url, params=params, timeout=self.timeout
            )
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети при получении списка событий: {str(e)}")

    def get(self, uri: str, params: dict = None):
        if not self.access_token:
            raise AuthenticationError("Требуется аутентификация пользователя")

        url = f"{settings.API_URL}/api/v1{uri}"
        try:
            response = self._make_authenticated_request("GET", url, params=params, timeout=self.timeout)
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети: {str(e)}")

    def get_by_id(self, uri: str, id: int):
        if not self.access_token:
            raise AuthenticationError("Требуется аутентификация пользователя")

        url = f"{settings.API_URL}/api/v1{uri}/{id}"
        try:
            response = self._make_authenticated_request("GET", url, timeout=self.timeout)
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети: {str(e)}")

    def post(self, uri: str, **data):
        if not self.access_token:
            raise AuthenticationError("Требуется аутентификация пользователя")

        url = f"{settings.API_URL}/api/v1{uri}"
        try:
            response = self._make_authenticated_request(
                "POST", url, json=data, timeout=self.timeout
            )
            if response.status_code not in [200, 201]:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети: {str(e)}")

    def put(self, uri: str, **data):
        """PUT запрос к API"""
        if not self.access_token:
            raise AuthenticationError("Требуется аутентификация пользователя")

        url = f"{settings.API_URL}/api/v1{uri}"
        try:
            response = self._make_authenticated_request(
                "PUT", url, json=data, timeout=self.timeout
            )
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети: {str(e)}")

    def delete(self, uri: str):
        """DELETE запрос к API"""
        if not self.access_token:
            raise AuthenticationError("Требуется аутентификация пользователя")

        url = f"{settings.API_URL}/api/v1{uri}"
        try:
            response = self._make_authenticated_request("DELETE", url, timeout=self.timeout)
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети: {str(e)}")

    # Методы для работы с вакансиями
    def get_vacancies(self, show_hidden: bool = False):
        """Получить список вакансий"""
        params = {}
        if show_hidden:
            params["show_hidden"] = "true"
        return self.get("/vacancies", params=params)

    def get_vacancy(self, vacancy_id: int):
        """Получить вакансию по ID"""
        return self.get_by_id("/vacancies", vacancy_id)

    def create_vacancy(self, **data):
        """Создать вакансию"""
        logger.info(f"Creating vacancy with data: {data}")
        result = self.post("/vacancies", **data)
        logger.info(f"Vacancy creation successful: {result}")
        return result

    def update_vacancy(self, vacancy_id: int, **data):
        """Обновить вакансию"""
        return self.put(f"/vacancies/{vacancy_id}", **data)

    def delete_vacancy(self, vacancy_id: int):
        """Удалить вакансию"""
        return self.delete(f"/vacancies/{vacancy_id}")

    def get_vacancy_statistics(self, vacancy_id: int):
        """Получить статистику вакансии"""
        return self.get(f"/vacancies/{vacancy_id}/statistics")

    # Методы для работы со студентами
    def get_students(self, vacancy_id: int = None, status: str = None):
        """Получить список студентов"""
        params = []
        if vacancy_id:
            params.append(f"vacancy_id={vacancy_id}")
        if status:
            params.append(f"status={status}")

        query = "&".join(params) if params else ""
        uri = f"/students{f'?{query}' if query else ''}"
        return self.get(uri)

    def get_student(self, student_id: int):
        """Получить студента по ID"""
        return self.get_by_id("/students", student_id)

    def update_student(self, student_id: int, **data):
        """Обновить студента"""
        return self.put(f"/students/{student_id}", **data)

    def delete_student(self, student_id: int):
        """Удалить студента"""
        return self.delete(f"/students/{student_id}")

    def bulk_update_student_status(self, student_ids: list[int], status: str):
        """Массовое обновление статусов студентов"""
        return self.post(
            "/students/bulk-status-update", student_ids=student_ids, status=status
        )

    def download_file(self, uri: str, dest_path: str = None) -> bytes | None:
        """
        Скачать файл по uri (относительно base_url). Если dest_path указан — сохранить файл туда, иначе вернуть bytes.
        """
        url = f"{settings.API_URL}/api/v1{uri}"
        try:
            response = self._make_authenticated_request("GET", url, timeout=self.timeout, stream=True)
            if response.status_code != 200:
                self._handle_error_response(response)
            if dest_path:
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return None
            else:
                return response.content
        except RequestException as e:
            logger.error(f"Network error during file download: {str(e)}")
            raise APIError(f"Ошибка сети при скачивании файла: {str(e)}")

    def change_password(self, current_password: str, new_password: str) -> dict[str, any]:
        """Смена пароля"""
        url = f"{settings.API_URL}/api/v1/password/change"
        data = {
            "current_password": current_password,
            "new_password": new_password,
        }

        try:
            response = self._make_authenticated_request(
                "POST", url, json=data, timeout=self.timeout
            )
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети при смене пароля: {str(e)}")

    # Методы для работы с новостями
    def get_news(self, show_hidden: bool = False) -> list[dict[str, any]]:
        """Получить список новостей"""
        params = {}
        if show_hidden:
            params["show_hidden"] = "true"
        return self.get("/news", params=params)

    def get_news_by_id(self, news_id: int) -> dict[str, any]:
        """Получить новость по ID"""
        return self.get_by_id("/news", news_id)

    def create_news(self, **data) -> dict[str, any]:
        """Создать новость"""
        url = f"{settings.API_URL}/api/v1/news/"
        
        try:
            logger.debug(f"Attempting to create news with data: {data}")
            
            # Подготавливаем данные для multipart/form-data
            files = {}
            form_data = {}
            
            # Обрабатываем изображение, если оно передано
            if 'image' in data:
                image_data = data.pop('image')
                if image_data is not None:
                    if hasattr(image_data, 'read'):
                        content_type = getattr(image_data, 'content_type', 'image/jpeg')
                        files['image'] = (getattr(image_data, 'filename', 'image.jpg'), image_data, content_type)
                    elif isinstance(image_data, tuple) and len(image_data) == 2:
                        files['image'] = (image_data[0], image_data[1], 'image/jpeg')
                    elif isinstance(image_data, tuple) and len(image_data) == 3:
                        files['image'] = image_data
                    else:
                        files['image'] = ('image.jpg', image_data, 'image/jpeg')
                    
            # Все остальные данные
            for key, value in data.items():
                if value is not None:
                    form_data[key] = str(value)
            
            # Копируем заголовки и удаляем Content-Type
            headers = self.headers.copy()
            headers.pop('Content-Type', None)
            
            # Если нет файлов, отправляем как обычные form-data
            if not files:
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                response = self._make_authenticated_request(
                    "POST", url, data=form_data, headers=headers, timeout=self.timeout
                )
            else:
                response = self._make_authenticated_request(
                    "POST", url, files=files, data=form_data, headers=headers, timeout=self.timeout
                )
            
            if response.status_code != 200:
                self._handle_error_response(response)
                
            return response.json()
            
        except RequestException as e:
            logger.error(f"Network error during news creation: {str(e)}")
            raise APIError(f"Ошибка сети при создании новости: {str(e)}")


    def update_news(self, news_id: int, **data) -> dict[str, any]:
        """Обновить новость с возможностью обновления изображения"""
        url = f"{settings.API_URL}/api/v1/news/{news_id}"
        
        try:
            logger.debug(f"Attempting to update news {news_id} with data: {data}")
            
            files = {}
            remove_image = data.get('remove_image') == 'true'
            if 'image' in data:
                image_data = data.pop('image')
                if image_data is not None:
                    if hasattr(image_data, 'read'):
                        content_type = getattr(image_data, 'content_type', 'image/jpeg')
                        files['image'] = (getattr(image_data, 'filename', 'image.jpg'), image_data, content_type)
                    elif isinstance(image_data, tuple) and len(image_data) == 2:
                        files['image'] = (image_data[0], image_data[1], 'image/jpeg')
                    elif isinstance(image_data, tuple) and len(image_data) == 3:
                        files['image'] = image_data
                    else:
                        files['image'] = ('image.jpg', image_data, 'image/jpeg')
                elif remove_image:
                    data['remove_image'] = 'true'
            elif remove_image:
                data['remove_image'] = 'true'
            
            headers = self.headers.copy()
            headers.pop('Content-Type', None)
            
            response = self._make_authenticated_request(
                "PUT", url, files=files if files else None, data=data, headers=headers, timeout=self.timeout
            )
            
            if response.status_code != 200:
                self._handle_error_response(response)
                
            return response.json()
            
        except RequestException as e:
            logger.error(f"Network error during news update: {str(e)}")
            raise APIError(f"Ошибка сети при попытке обновления новости: {str(e)}")

    def delete_news(self, news_id: int) -> dict[str, any]:
        """Удалить новость"""
        return self.delete(f"/news/{news_id}")

    def toggle_news_visibility(self, news_id: int) -> dict[str, any]:
        """Переключить видимость новости"""
        return self.post(f"/news/{news_id}/toggle-visibility")

    # Методы для работы с вопросами (обратная связь)
    def get_feedbacks(self) -> list[dict[str, any]]:
        """Получить список вопросов"""
        return self.get("/feedback")

    def get_feedback_by_id(self, feedback_id: int) -> dict[str, any]:
        """Получить вопрос по ID"""
        return self.get_by_id("/feedback", feedback_id)

    def create_feedback(self, **data) -> dict[str, any]:
        """Создать вопрос"""
        return self.post("/feedback", **data)

    def respond_to_feedback(self, feedback_id: int, response_text: str) -> dict[str, any]:
        """Ответить на вопрос"""
        url = f"{settings.API_URL}/api/v1/feedback/{feedback_id}/respond"
        data = {"response_text": response_text}
        try:
            response = self._make_authenticated_request(
                "POST", url, json=data, timeout=self.timeout
            )
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети при ответе на вопрос: {str(e)}")

    def delete_feedback(self, feedback_id: int) -> dict[str, any]:
        """Удалить вопрос"""
        return self.delete(f"/feedback/{feedback_id}")

    # Методы для работы с отзывами
    def get_reviews(self, show_hidden: bool = False) -> list[dict[str, any]]:
        """Получить список отзывов"""
        params = {}
        if show_hidden:
            params["show_hidden"] = "true"
        return self.get("/reviews", params=params)

    def get_review_by_id(self, review_id: int) -> dict[str, any]:
        """Получить отзыв по ID"""
        return self.get_by_id("/reviews", review_id)

    def create_review(self, **data) -> dict[str, any]:
        """Создать отзыв"""
        return self.post("/reviews", **data)

    def update_review(self, review_id: int, **data) -> dict[str, any]:
        """Обновить отзыв (только переданные поля)"""
        update_data = {k: v for k, v in data.items() if v is not None}
        return self.put(f"/reviews/{review_id}", **update_data)

    def delete_review(self, review_id: int) -> dict[str, any]:
        """Удалить отзыв"""
        return self.delete(f"/reviews/{review_id}")

    # Методы для работы с пользователями
    def get_users(self) -> list[dict[str, any]]:
        """Получить список пользователей"""
        return self.get("/users")

    def get_user_by_id(self, user_id: int) -> dict[str, any]:
        """Получить пользователя по ID"""
        return self.get_by_id("/users", user_id)

    def delete_user(self, user_id: int) -> dict[str, any]:
        """Удалить пользователя"""
        return self.delete(f"/users/{user_id}")

    def update_user(self, user_id: int, **data) -> dict[str, any]:
        """Обновить пользователя"""
        return self.put(f"/users/{user_id}", **data)

    def activate_user(self, user_id: int) -> dict[str, any]:
        """Активировать пользователя"""
        return self.post(f"/users/{user_id}/activate")

    def deactivate_user(self, user_id: int) -> dict[str, any]:
        """Деактивировать пользователя"""
        return self.post(f"/users/{user_id}/deactivate")

    def activate_vacancy(self, vacancy_id: int) -> dict[str, any]:
        """Активировать вакансию"""
        return self.post(f"/vacancies/{vacancy_id}/activate")

    def deactivate_vacancy(self, vacancy_id: int) -> dict[str, any]:
        """Деактивировать вакансию"""
        return self.post(f"/vacancies/{vacancy_id}/deactivate")

    def delete_application(self, application_id: int) -> dict[str, any]:
        """Удалить заявку на вакансию"""
        return self.delete(f"/students/{application_id}")

    def approve_review(self, review_id: int) -> dict[str, any]:
        """Одобрить отзыв"""
        return self.post(f"/api/v1/reviews/{review_id}/approve")

    def reject_review(self, review_id: int) -> dict[str, any]:
        """Отклонить отзыв"""
        return self.post(f"/api/v1/reviews/{review_id}/reject")

    # Методы для работы с шаблонами расписаний
    def upload_excel_schedule(self, file_path: str) -> dict[str, any]:
        """Загрузить Excel файл и сгенерировать JSON шаблоны расписаний"""
        url = f"{settings.API_URL}/api/v1/schedule/upload-excel"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.split('/')[-1], f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                
                response = self._make_authenticated_request(
                    'POST', url, files=files, timeout=self.timeout
                )
                
                if response.status_code != 200:
                    self._handle_error_response(response)
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Error uploading Excel schedule: {str(e)}")
            raise APIError(f"Ошибка загрузки файла: {str(e)}")

    def upload_schedule_excel(self, files: dict) -> dict[str, any]:
        """Загрузить Excel файл через multipart/form-data"""
        url = f"{settings.API_URL}/api/v1/schedule/upload-excel"
        
        try:
            response = self._make_authenticated_request(
                'POST', url, files=files, timeout=self.timeout
            )
            
            if response.status_code != 200:
                self._handle_error_response(response)
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error uploading Excel schedule: {str(e)}")
            raise APIError(f"Ошибка загрузки файла: {str(e)}")

    def get_schedule_templates(self) -> list[dict[str, any]]:
        """Получить список активных шаблонов расписаний"""
        url = f"{settings.API_URL}/api/v1/schedule/templates"
        
        try:
            response = self._make_authenticated_request('GET', url, timeout=self.timeout)
            
            if response.status_code != 200:
                self._handle_error_response(response)
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting schedule templates: {str(e)}")
            raise APIError(f"Ошибка получения шаблонов: {str(e)}")

    def get_schedule_template_by_college(self, college_name: str) -> dict[str, any]:
        """Получить JSON данные расписания по названию колледжа"""
        url = f"{settings.API_URL}/api/v1/schedule/templates/{college_name}"
        
        try:
            response = self._make_authenticated_request('GET', url, timeout=self.timeout)
            
            if response.status_code != 200:
                self._handle_error_response(response)
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting schedule template: {str(e)}")
            raise APIError(f"Ошибка получения шаблона: {str(e)}")

    def delete_schedule_template(self, template_id: int) -> dict:
        """Удалить шаблон расписания по ID"""
        logger.info(f"=== APIClient.delete_schedule_template ===")
        logger.info(f"Template ID: {template_id}")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Access token available: {self.access_token is not None}")
        
        url = f"{self.base_url}/api/v1/schedule/templates/{template_id}"
        logger.info(f"Full URL: {url}")
        
        try:
            logger.info("Making authenticated DELETE request...")
            response = self._make_authenticated_request("DELETE", url, timeout=self.timeout)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response content: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"Non-200 response: {response.status_code}")
                self._handle_error_response(response)
            
            result = response.json()
            logger.info(f"Parsed response: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Exception in delete_schedule_template: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise APIError(f"Ошибка удаления шаблона: {str(e)}")

    def delete_all_schedule_templates(self) -> dict[str, any]:
        """Удалить все шаблоны расписаний"""
        if not self.access_token:
            raise AuthenticationError("Требуется аутентификация пользователя")

        url = f"{settings.API_URL}/api/v1/schedule/templates"
        try:
            response = self._make_authenticated_request("DELETE", url, timeout=self.timeout)
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()
        except RequestException as e:
            raise APIError(f"Ошибка сети при удалении всех шаблонов: {str(e)}")


api_client = APIClient(settings.API_URL)
