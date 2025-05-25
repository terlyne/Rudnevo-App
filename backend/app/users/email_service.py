from fastapi_mail import ConnectionConfig, MessageSchema, FastMail
from pydantic import EmailStr

from core.config import settings

def get_mail_config():
    return ConnectionConfig(
        MAIL_USERNAME=settings.ADMIN_EMAIL,
        MAIL_PASSWORD=settings.ADMIN_PASSWORD,
        MAIL_FROM=settings.ADMIN_EMAIL,
        MAIL_PORT=465,
        MAIL_SERVER="smtp.mail.ru",
        MAIL_FROM_NAME="admin",
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=True,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


mail_config = get_mail_config()

async def send_register_invitation(email: str, token: str):
    registration_url = f"{settings.FRONTEND_URL}/register?token={token}"
    message = MessageSchema(
        subject="Приглашение на регистрацию",
        recipients=[email],
        body=f"""
        <h1>Приглашение на регистрацию</h1>
        <p>Пожалуйста, перейдите по ссылке для завершения регистрации:</p>
        <a href="{registration_url}">Зарегистрироваться</a>
        <p>Ссылка действительна {settings.REGISTRATION_TOKEN_EXPIRE_DAYS} день.</p>
        """,
        subtype="html"
    )
    fm = FastMail(mail_config)
    await fm.send_message(message)