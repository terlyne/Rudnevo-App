from sqlalchemy.future import select
from typing import Optional
from core.database import async_session_maker
from users.models import User, UserRole
from users.schemas import UserRegister, UserCreate


async def get_user_by_email_or_username(identifier: str) -> Optional[User]:
    """Получение пользователя по email или username."""
    async with async_session_maker() as session:
        query = select(User).where(
            (User.email == identifier) | (User.username == identifier)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()


async def create_user(user_data: UserCreate) -> Optional[User]:
    """Создание нового пользователя администратором."""
    async with async_session_maker() as session:
        user = await get_user_by_email_or_username(user_data.email)

        if user is None:
            new_user = User(email=user_data.email)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user

        return None
    
async def is_superadmin_exists() -> bool:
    """Проверка существования супер-админа."""
    async with async_session_maker() as session:
        query = select(User).where(User.role == UserRole.SUPERADMIN)
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None
    

async def register_superadmin(user_data: UserRegister) -> Optional[User]:
    """Регистрация супер-админа."""
    async with async_session_maker() as session:
        user = await get_user_by_email_or_username(user_data.email)

        if user is None:
            user = User(email=user_data.email, username=user_data.username, role=UserRole.SUPERADMIN)
            user.set_password(user_data.password)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

        return None


async def register_user(user_data: UserRegister) -> Optional[User]:
    """Регистрация пользователя."""
    async with async_session_maker() as session:
        user = await get_user_by_email_or_username(user_data.email)

        if user is not None and not user.is_registered:
            user.username = user_data.username
            user.set_password(user_data.password)
            user.is_registered = True
            await session.commit()
            await session.refresh(user)
            return user
        
        return None


async def change_user_password(user: User, new_password: str) -> None:
    """Изменение пароля пользователя."""
    async with async_session_maker() as session:
        user.set_password(new_password)
        session.add(user)
        await session.commit()


async def delete_user(user: User) -> None:
    """Удаление пользователя."""
    async with async_session_maker() as session:
        await session.delete(user)
        await session.commit()
