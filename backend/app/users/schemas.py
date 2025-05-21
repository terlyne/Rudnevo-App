from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=255, description="Имя пользователя"
    )
    email: EmailStr = Field(
        ..., min_length=3, max_length=255, description="Почта пользователя"
    )
    password: str = Field(..., description="Пароль пользователя")


class UserLogin(BaseModel):
    identifier: str = Field(..., description="Email или имя пользователя")
    password: str = Field(..., description="Пароль пользователя")


class UserChangePassword(BaseModel):
    current_password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., description="Новый пароль")


class UserResponse(BaseModel):
    id: int = Field(..., description="Id пользователя")
    username: str = Field(..., description="Имя пользователя")
    email: EmailStr = Field(..., description="Почта пользователя")

    class Config:
        from_attributes = True
