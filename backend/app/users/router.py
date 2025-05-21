from fastapi import Depends, HTTPException, status, APIRouter, Response, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from users.crud import (
    change_user_password,
    get_user_by_email_or_username,
    create_user,
    delete_user,
)
from users.dependencies import authenticate_user, authenticate_user_by_token
from users.auth import create_jwt_token, get_user_from_token, oauth2_scheme
from users.models import User
from users.schemas import UserChangePassword, UserLogin, UserRegister, UserResponse

router = APIRouter(tags=["Users"], prefix="/users")


@router.post("/register", response_model=UserResponse)
async def register_user(user_in: UserRegister):
    user = await create_user(user_in)
    if user:
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email or username already registered.",
    )


@router.post("/login")
async def login_user(user_in: UserLogin, response: Response):
    user = await get_user_by_email_or_username(user_in.identifier)
    if user is None or not user.check_password(user_in.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_jwt_token(user)
    response.headers["Authorization"] = f"Bearer {token}"
    return {"message": "Successfully logged in"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(authenticate_user_by_token)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
    )


@router.patch("/password")
async def update_password(
    password_data: UserChangePassword,
    current_user: User = Depends(authenticate_user_by_token),
):
    if not current_user.check_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password",
        )

    await change_user_password(current_user, password_data.new_password)
    return {"message": "Password updated successfully"}


@router.delete("/me")
async def delete_current_user(current_user: User = Depends(authenticate_user_by_token)):
    await delete_user(current_user)
    return {"message": "User deleted successfully"}
