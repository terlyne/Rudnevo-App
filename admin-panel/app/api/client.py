import requests
from urllib.parse import urljoin
from flask import session
from requests.exceptions import RequestException
import logging

from core.config import settings


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
        self._token: str | None = None
        logger.debug(f"APIClient initialized with base_url: {base_url}")

    @property
    def token(self) -> str | None:
        """Получить текущий токен из сессии"""
        if self._token is None:
            self._token = session.get('access_token')
            logger.debug(f"Token retrieved from session: {'present' if self._token else 'missing'}")
        return self._token

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_error_response(self, response: requests.Response) -> None:
        """Обработка ошибок от API"""
        try:
            error_data = response.json()
            error_message = error_data.get('detail', 'Неизвестная ошибка')
        except ValueError:
            error_message = response.text or 'Неизвестная ошибка'

        logger.error(f"API Error: Status {response.status_code}, Message: {error_message}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response content: {response.text}")

        if response.status_code == 401:
            raise AuthenticationError(
                error_message,
                status_code=response.status_code
            )
        elif response.status_code == 403:
            raise PermissionError(
                error_message,
                status_code=response.status_code
            )
        elif response.status_code == 404:
            raise NotFoundError(
                error_message,
                status_code=response.status_code
            )
        elif response.status_code == 400:
            raise ValidationError(
                error_message,
                status_code=response.status_code
            )
        else:
            raise APIError(
                error_message,
                status_code=response.status_code
            )

    def _save_token_to_session(self, token: str) -> None:
        """Сохранить токен в сессию Flask"""
        session['access_token'] = token
        self._token = token
        logger.debug("Token saved to session")

    def _clear_token(self) -> None:
        """Очистить токен из сессии и из клиента"""
        if 'access_token' in session:
            session.pop('access_token')
        self._token = None
        logger.debug("Token cleared from session")

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
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                self._handle_error_response(response)
            
            data = response.json()
            self._save_token_to_session(data["access_token"])
            logger.debug("Login successful")
            return data
            
        except RequestException as e:
            logger.error(f"Network error during login: {str(e)}")
            raise APIError(f"Ошибка сети при попытке входа: {str(e)}")

    def register(self, email: str, username: str, password: str, token: str) -> dict[str, any]:
        """Регистрация пользователя по токену из email"""
        url = f"{settings.API_URL}/api/v1/auth/register"
        data = {
            "email": email,
            "username": username,
            "password": password,
            "token": token
        }
        
        try:
            logger.debug(f"Attempting registration for email: {email}, username: {username}")
            logger.debug(f"Registration URL: {url}")
            logger.debug(f"Registration data: {data}")
            
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout
            )
            
            logger.debug(f"Registration response status: {response.status_code}")
            logger.debug(f"Registration response headers: {response.headers}")
            logger.debug(f"Registration response content: {response.text}")
            
            if response.status_code != 200:
                self._handle_error_response(response)
            
            data = response.json()
            self._save_token_to_session(data["access_token"])
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
            response = requests.post(
                url,
                json=data,
                headers=self.headers,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            return response.json()
        
        except RequestException as e:
            raise APIError(f"Ошибка сети при попытке отправки письма для смены пароля: {str(e)}")
        

    def reset_password(self, token: str, new_password: str) -> None:
        """Сброс пароля по токену"""
        url = f"{settings.API_URL}/api/v1/password/reset-password"
        
        try:
            response = requests.post(
                url,
                json={
                    "token": token,
                    "new_password": new_password,
                },
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                self._handle_error_response(response)
            return response.json()            
        
        except RequestException as e:
            logger.error(f"Network error during password reset: {str(e)}")
            raise APIError("Ошибка сети при сбросе пароля")


    def invite_user(self, email: str) -> dict[str, any]:
        """Пригласить нового пользователя (требуется токен суперпользователя)"""
        if not self.token:
            raise AuthenticationError("Требуется аутентификация суперпользователя")
            
        url = f"{settings.API_URL}/api/v1/auth/invite"
        data = {"email": email}
        
        try:
            logger.debug(f"Attempting to invite user: {email}")
            response = requests.post(
                url,
                json=data,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                self._handle_error_response(response)
            
            logger.debug("Invitation sent successfully")
            return response.json()
            
        except RequestException as e:
            logger.error(f"Network error during invitation: {str(e)}")
            raise APIError(f"Ошибка сети при попытке отправки приглашения: {str(e)}")

    def logout(self) -> None:
        """Выход пользователя"""
        self._clear_token()


api_client = APIClient(settings.API_URL)