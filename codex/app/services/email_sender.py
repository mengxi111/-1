import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings


class EmailDeliveryError(RuntimeError):
    pass


def is_email_delivery_enabled() -> bool:
    return settings.email_enabled


def send_email(*, recipient: str, subject: str, text_content: str, html_content: str | None = None) -> None:
    if not settings.email_enabled:
        raise EmailDeliveryError("邮件发送未启用")
    if not settings.smtp_host or not settings.smtp_from_email:
        raise EmailDeliveryError("SMTP 配置不完整")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        if settings.smtp_from_name
        else settings.smtp_from_email
    )
    message["To"] = recipient
    message.set_content(text_content)
    if html_content:
        message.add_alternative(html_content, subtype="html")

    try:
        if settings.smtp_use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
                context=context,
            ) as server:
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password or "")
                server.send_message(message)
            return

        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=settings.smtp_timeout_seconds,
        ) as server:
            if settings.smtp_use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password or "")
            server.send_message(message)
    except Exception as exc:
        raise EmailDeliveryError(str(exc)) from exc
