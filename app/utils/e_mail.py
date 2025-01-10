import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app import settings


def send_ascii_email(receiver: str, message: str):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(settings.email.smtp_host, settings.email.ssl_port, context=context) as server:
        server.login(settings.email.sender, settings.email.password)
        server.sendmail(settings.email.sender, receiver, message)


def send_email(receiver: str, subject: str, msg: str):
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.email.sender
    message["To"] = receiver
    message.attach(MIMEText(msg, "plain", "utf-8"))
    send_ascii_email(receiver, message.as_string())


def send_confirm_email(receiver: str, confirm_url: str):
    send_email(
        receiver,
        "Подтверждение почты",
        f"Вы получили это сообщение, потому что ваша почто указана при регистрации на сайте ITMO-meetings."
        f"Для подтверждения почты перейдите по ссылке:\n{confirm_url}\n\n\n"
        f"Если это сделали не вы, проигнорируйте это сообщение.",
    )
