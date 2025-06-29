from pydantic import BaseModel


class Token(BaseModel):
    """Схема токена доступа"""

    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    """Схема данных в токене"""

    username: str | None = None
    email: str | None = None


class RefreshToken(BaseModel):
    """Схема для обновления токена"""

    refresh_token: str
