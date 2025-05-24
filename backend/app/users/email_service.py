from fastapi_mail import ConnectionConfig, MessageSchema, FastMail
from pydantic import EmailStr

from core.config import settings

def get_mail_config():
    mail_name = settings.ADMIN_EMAIL.split("@")[1].split(".")[0]
    if mail_name == "mail":
        mail_server = "smtp.mail.ru"
    elif mail_name == "yandex":
        mail_server = "smtp.yandex.ru"
    elif mail_name == "gmail":
        mail_server = "smtp.gmail.com"

    return ConnectionConfig(
        MAIL_USERNAME=settings.ADMIN_EMAIL,
        MAIL_PASSWORD=settings.ADMIN_PASSWORD,
        MAIL_FROM=settings.ADMIN_EMAIL,
        MAIL_PORT=587,
        MAIL_SERVER=mail_server,
        MAIL_FROM_NAME="admin",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


mail_config = get_mail_config()

async def send_register_invitation(user_email: EmailStr):
    message = MessageSchema(
        subject="Приглашение на регистрацию",
        recipients=[user_email],
        body=f"Пожалуйста, перейдите по ссылке для регистрации на нашем сервисе: {settings.FRONTEND_URL}/register",
        subtype="html"
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)