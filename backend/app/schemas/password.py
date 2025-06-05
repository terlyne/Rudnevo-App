from pydantic import BaseModel, EmailStr


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
