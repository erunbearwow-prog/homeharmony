# accounts/services/phone_auth_service.py

import random
import re
from typing import Optional, Dict
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..utils.sms_sender import SMSSender
from ..validators.phone_validator import validate_phone_number

User = get_user_model()


class PhoneAuthService:
    """
    Сервис аутентификации по номеру телефона
    """

    OTP_LENGTH = 6
    OTP_TIMEOUT = 300  # 5 минут

    @classmethod
    def generate_otp(cls, phone_number: str) -> str:
        """Генерирует OTP код"""
        otp = ''.join([str(random.randint(0, 9)) for _ in range(cls.OTP_LENGTH)])
        cache_key = f'phone_otp:{phone_number}'
        cache.set(cache_key, otp, timeout=cls.OTP_TIMEOUT)
        return otp

    @classmethod
    def verify_otp(cls, phone_number: str, otp: str) -> bool:
        """Проверяет OTP код"""
        cache_key = f'phone_otp:{phone_number}'
        cached_otp = cache.get(cache_key)
        if cached_otp == otp:
            cache.delete(cache_key)
            return True
        return False

    @classmethod
    def send_otp(cls, phone_number: str) -> Dict:
        """
        Отправляет OTP на телефон
        Возвращает: { success: bool, message: str, otp: str (для dev) }
        """
        # Валидация телефона
        if not validate_phone_number(phone_number):
            return {
                'success': False,
                'message': 'Неверный формат номера телефона'
            }

        # Генерируем OTP
        otp = cls.generate_otp(phone_number)

        # Отправляем SMS
        success = SMSSender.send(phone_number, f'Ваш код подтверждения: {otp}')

        if success:
            return {
                'success': True,
                'message': 'Код подтверждения отправлен',
                'otp': otp  # Для разработки, в продакшене убрать
            }
        else:
            return {
                'success': False,
                'message': 'Ошибка отправки SMS'
            }

    @classmethod
    def register(cls, phone_number: str) -> Dict:
        """
        Регистрация по телефону
        Возвращает: { success: bool, user: User, otp_sent: bool }
        """
        # Проверяем, существует ли пользователь
        if User.objects.filter(phone_number=phone_number).exists():
            return {
                'success': False,
                'message': 'Пользователь с этим номером уже существует'
            }

        # Отправляем OTP
        result = cls.send_otp(phone_number)

        if not result['success']:
            return result

        return {
            'success': True,
            'message': 'Код подтверждения отправлен',
            'phone_number': phone_number,
            'otp_sent': True
        }

    @classmethod
    def login(cls, phone_number: str, otp: str) -> Optional[User]:
        """
        Вход по телефону с OTP
        """
        # Проверяем OTP
        if not cls.verify_otp(phone_number, otp):
            return None

        # Находим пользователя
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return None

        # Обновляем данные
        user.phone_verified = True
        user.last_activity = timezone.now()
        user.save()

        return user

    @classmethod
    def resend_otp(cls, phone_number: str) -> Dict:
        """
        Повторная отправка OTP
        """
        # Проверяем, существует ли пользователь
        if not User.objects.filter(phone_number=phone_number).exists():
            return {
                'success': False,
                'message': 'Пользователь не найден'
            }

        return cls.send_otp(phone_number)