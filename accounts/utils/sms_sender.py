# accounts/utils/sms_sender.py

import requests
from django.conf import settings


class SMSSender:
    """Класс для отправки SMS через внешний сервис"""

    @staticmethod
    def send(phone_number: str, message: str) -> bool:
        """
        Отправляет SMS
        Возвращает True если отправка успешна
        """
        # Здесь интеграция с SMS-шлюзом (Twilio, SMS.ru, и т.д.)
        try:
            # Пример для SMS.ru
            # response = requests.post(
            #     'https://sms.ru/sms/send',
            #     data={
            #         'api_id': settings.SMS_API_ID,
            #         'to': phone_number,
            #         'msg': message,
            #     }
            # )
            # return response.status_code == 200
            return True  # Временная заглушка
        except Exception:
            return False