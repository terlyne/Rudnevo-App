from pydantic import BaseModel, EmailStr


class PasswordReset(BaseModel):
    """Схема для запроса сброса пароля"""

    email: EmailStr


class PasswordChange(BaseModel):
    """Схема для изменения пароля"""

    current_password: str
    new_password: str


class PasswordResetConfirm(BaseModel):
    """Схема для подтверждения сброса пароля"""

    token: str
    new_password: str
