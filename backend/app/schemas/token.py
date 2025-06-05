from pydantic import BaseModel


class Token(BaseModel):
    """Схема токена доступа"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Схема данных в токене"""
    username: str | None = None
    email: str | None = None
