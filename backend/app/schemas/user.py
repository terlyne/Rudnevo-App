from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Базовая схема пользователя"""

    email: EmailStr
    username: str | None = None
    is_superuser: bool = False
    is_registered: bool = False
    is_recruiter: bool = False


class UserCreate(UserBase):
    """Схема создания пользователя"""

    password: str | None = None


class UserUpdate(BaseModel):
    """Схема обновления пользователя"""

    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None


class UserInvite(BaseModel):
    """Схема для приглашения пользователя"""

    email: EmailStr
    is_recruiter: bool = False


class UserRegistration(BaseModel):
    """Схема для регистрации пользователя"""

    token: str
    email: EmailStr
    username: str
    password: str


class UserInDB(UserBase):
    """Схема пользователя из БД"""

    id: int

    model_config = ConfigDict(from_attributes=True)


class UserWithToken(UserInDB):
    """Схема пользователя с токеном"""

    access_token: str
    token_type: str = "bearer"
