import requests
from typing import Optional, Dict, Any, List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class APIService:
    def __init__(self):
        self.base_url = settings.API_BASE_URL
        self.session = requests.Session()
    
    def _make_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"
    
    def set_token(self, token: str):
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info(f"Token set in headers: {self.session.headers}")
    
    def clear_token(self):
        self.session.headers.pop("Authorization", None)
    
    # Auth endpoints
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        try:
            url = self._make_url("/api/v1/auth/login")
            data = {
                "username": username,
                "password": password,
                "grant_type": "password"
            }
            logger.info(f"Attempting login at {url} with username: {username}")
            
            response = self.session.post(url, data=data)
            logger.info(f"Login response status: {response.status_code}")
            
            if response.ok:
                result = response.json()
                logger.info(f"Login successful, token received: {result.get('access_token', '')[:10]}...")
                return result
            else:
                logger.error(f"Login failed with status {response.status_code}: {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Login error: {str(e)}")
            return None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        try:
            url = self._make_url("/api/v1/users/me")
            logger.info(f"Getting current user from {url}")
            logger.info(f"Headers: {self.session.headers}")
            
            response = self.session.get(url)
            logger.info(f"Get current user response status: {response.status_code}")
            
            if response.ok:
                data = response.json()
                logger.info(f"Current user data: {data}")
                return data
            else:
                logger.error(f"Failed to get user data: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None
    
    # User management endpoints
    def get_users(self) -> List[Dict[str, Any]]:
        try:
            response = self.session.get(self._make_url("/api/v1/users/"))
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return []

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(self._make_url(f"/api/v1/users/{user_id}"))
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def create_user_invitation(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.post(
                self._make_url("/api/v1/auth/invite"),
                json={"email": email}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def complete_registration(self, token: str, email: str, username: str, password: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.post(
                self._make_url("/api/v1/auth/register"),
                json={
                    "token": token,
                    "email": email,
                    "username": username,
                    "password": password
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def delete_user(self, user_id: str) -> bool:
        try:
            response = self.session.delete(self._make_url(f"/api/v1/users/{user_id}"))
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    # News management endpoints
    def get_news(self) -> List[Dict[str, Any]]:
        try:
            response = self.session.get(self._make_url("/api/v1/news"))
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return []

    def get_news_item(self, news_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(self._make_url(f"/api/v1/news/{news_id}"))
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def create_news(self, title: str, content: str, image_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            data = {
                "title": title,
                "content": content,
                "image_url": image_url
            }
            response = self.session.post(self._make_url("/api/v1/news"), json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def update_news(self, news_id: str, title: str, content: str, image_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            data = {
                "title": title,
                "content": content,
                "image_url": image_url
            }
            response = self.session.put(self._make_url(f"/api/v1/news/{news_id}"), json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def delete_news(self, news_id: str) -> bool:
        try:
            response = self.session.delete(self._make_url(f"/api/v1/news/{news_id}"))
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

api_service = APIService() 