from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from users.crud import get_user_by_email_or_username
from users.auth import get_user_from_token


security = HTTPBasic()


async def authenticate_user(creds: HTTPBasicCredentials = Depends(security)):
    identifier = creds.username

    user = await get_user_by_email_or_username(identifier)
    if user is None or not user.check_password(creds.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return user


async def authenticate_user_by_token(request: Request):
    authorization = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token = authorization.split(" ")[1]
        return await get_user_from_token(token)

    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization code",
            headers={"WWW-Authenticate": "Bearer"},
        )
