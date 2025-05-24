from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    # Схема для первичного создания пользователя администратором
    email: EmailStr = Field(
        ..., min_length=3, description="Почта пользователя"
    )

class UserRegister(BaseModel):
    # Схема для регистрации пользователя
    email: EmailStr = Field(
        ..., min_length=3, description="Почта пользователя"
    )
    username: str = Field(
        ..., min_length=3, description="Имя пользователя"
    )
    password: str = Field(
        ..., min_length=3, description="Пароль пользователя"
    )
    is_registered: bool = True


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
