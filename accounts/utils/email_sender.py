# accounts/utils/email_sender.py

from django.core.mail import send_mail
from django.conf import settings


class EmailSender:
    """Класс для отправки email"""

    @staticmethod
    def send(to: str, subject: str, body: str, html_body: str = None) -> bool:
        """
        Отправляет email
        Возвращает True если отправка успешна
        """
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to],
                html_message=html_body,
            )
            return True
        except Exception:
            return False