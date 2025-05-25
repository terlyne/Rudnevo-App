from fastapi import Depends, HTTPException, status, APIRouter, Response
from pydantic import EmailStr
from datetime import datetime, timedelta
from typing import Optional
from users.crud import (
    change_user_password,
    get_user_by_email_or_username,
    create_user as crud_create_user,
    delete_user,
    is_superadmin_exists,
    register_user as crud_register_user,
    register_superadmin as crud_register_superadmin,
)
from core.database import async_session_maker
from core.config import settings
from users.dependencies import authenticate_user_by_token
from users.auth import create_jwt_token, create_registration_token, verify_registration_token
from users.models import User, UserRole
from users.schemas import UserChangePassword, UserLogin, UserRegister, UserResponse, UserCreate
from users.email_service import send_register_invitation


router = APIRouter(tags=["Users"], prefix="/users")


@router.post("/super-admin/register", response_model=UserResponse)
async def register_superadmin(user_in: UserRegister):
    """Регистрация супер-админа в системе"""
    if await get_user_by_email_or_username(user_in.email):
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email or username already registered.",
    )

    if await is_superadmin_exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Superadmin already exists."
        )
    
    user = await crud_register_superadmin(user_in)
    if user:
        user.role = UserRole.SUPERADMIN
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
        )
    


@router.post("/create", response_model=UserResponse)
async def create_user(user_in: UserCreate, current_user = Depends(authenticate_user_by_token)):
    """Создание пользователя супер-админом."""
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can create users."
        )
    
    user = await crud_create_user(user_in)
    
    if user:
        return UserResponse(
            id=user.id,
            email=user.email,
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email or username already registered.",
    )

@router.post("/invite")
async def invite_user(
    email: EmailStr,
    current_user: User = Depends(authenticate_user_by_token)
):
    """Отправляет приглашение на регистрацию"""
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmin can invite users")

    async with async_session_maker() as session:
        # Проверяем, существует ли пользователь в базе
        user = await get_user_by_email_or_username(email)
        if not user:
            raise HTTPException(
                status_code=400,
                detail="User not found in system. Please add user first via /create endpoint"
            )
        
        if user.is_registered:
            raise HTTPException(
                status_code=400,
                detail="User already registered"
            )

        # Генерируем и сохраняем токен
        token = create_registration_token(email)
        user.registration_token = token
        user.token_expires = datetime.now() + timedelta(days=settings.REGISTRATION_TOKEN_EXPIRE_DAYS)
        
        await session.commit()
        await send_register_invitation(email, token)
        return {"message": "Invitation sent"}



@router.post("/register", response_model=UserResponse)
async def register_user(
    user_in: UserRegister,
    token: Optional[str] = None
):
    """Регистрация пользователя по токену"""
    if not token:
        raise HTTPException(status_code=400, detail="Registration token required")
    
    email = await verify_registration_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    if email != user_in.email:
        raise HTTPException(status_code=400, detail="Token email doesn't match")

    user = await get_user_by_email_or_username(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.is_registered:
        raise HTTPException(status_code=400, detail="User already registered")
    

    user = await crud_register_user(user_in)
    if user:
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Registration failed."
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
