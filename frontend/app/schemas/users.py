from pydantic import BaseModel, Field



class UserLogin(BaseModel):
    identifier: str = Field(..., description="Email или имя пользователя")
    password: str = Field(..., description="Пароль пользователя")
