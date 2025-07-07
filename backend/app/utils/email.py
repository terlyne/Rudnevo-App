from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

from core.config import settings


conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.PROJECT_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "email-templates",
)

fastmail = FastMail(conf)


async def send_registration_email(email_to: EmailStr, token: str) -> None:
    """Отправка email с приглашением для регистрации"""
    registration_url = f"{settings.FRONTEND_URL}/register?token={token}"

    message = MessageSchema(
        subject="Приглашение для регистрации",
        recipients=[email_to],
        body=f"""
            Здравствуйте!
            
            Вы получили это письмо, потому что ваш email был указан при создании учетной записи администратора.
            
            Для завершения регистрации, пожалуйста, перейдите по следующей ссылке:
            {registration_url}
            
            Если вы не запрашивали создание учетной записи, просто проигнорируйте это письмо.
            
            С уважением,
            Команда {settings.PROJECT_NAME}
        """,
        subtype="plain",
    )

    await fastmail.send_message(message)


async def send_reset_password_email(email_to: str, token: str, username: str) -> None:
    """Отправить email для сброса пароля"""
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    message = MessageSchema(
        subject="Сброс пароля",
        recipients=[email_to],
        body=f"""
        Здравствуйте, {username}!
        
        Вы запросили сброс пароля. Для установки нового пароля перейдите по ссылке:
        {reset_link}
        
        Если вы не запрашивали сброс пароля, проигнорируйте это письмо.
        
        Ссылка действительна в течение 24 часов.
        """,
        subtype="plain",
    )

    await fastmail.send_message(message)


async def send_feedback_response(email_to: str, name: str, response_text: str) -> None:
    """Отправить ответ на обратную связь"""
    message = MessageSchema(
        subject="Ответ на ваше обращение",
        recipients=[email_to],
        body=f"""
        Здравствуйте, {name}!
        
        Получен ответ на ваше обращение:
        
        {response_text}
        
        С уважением,
        Администрация Руднево
        """,
        subtype="plain",
    )

    await fastmail.send_message(message)
