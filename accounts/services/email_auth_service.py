# accounts/services/email_auth_service.py

import random
import re
from typing import Optional, Dict
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..utils.email_sender import EmailSender

User = get_user_model()


class EmailAuthService:
    """
    Сервис аутентификации по email
    """

    OTP_LENGTH = 6
    OTP_TIMEOUT = 300  # 5 минут

    @classmethod
    def generate_otp(cls, email: str) -> str:
        """Генерирует OTP код"""
        otp = ''.join([str(random.randint(0, 9)) for _ in range(cls.OTP_LENGTH)])
        cache_key = f'email_otp:{email}'
        cache.set(cache_key, otp, timeout=cls.OTP_TIMEOUT)
        return otp

    @classmethod
    def verify_otp(cls, email: str, otp: str) -> bool:
        """Проверяет OTP код"""
        cache_key = f'email_otp:{email}'
        cached_otp = cache.get(cache_key)
        if cached_otp == otp:
            cache.delete(cache_key)
            return True
        return False

    @classmethod
    def send_otp(cls, email: str) -> Dict:
        """
        Отправляет OTP на email
        """
        # Валидация email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return {
                'success': False,
                'message': 'Неверный формат email'
            }

        # Генерируем OTP
        otp = cls.generate_otp(email)

        # Отправляем email
        success = EmailSender.send(
            to=email,
            subject='Код подтверждения',
            body=f'Ваш код подтверждения: {otp}\n\nКод действителен 5 минут.'
        )

        if success:
            return {
                'success': True,
                'message': 'Код подтверждения отправлен на email',
                'otp': otp  # Для разработки
            }
        else:
            return {
                'success': False,
                'message': 'Ошибка отправки email'
            }

    @classmethod
    def register(cls, email: str, password: str, **kwargs) -> Dict:
        """
        Регистрация по email с паролем
        """
        # Проверяем, существует ли пользователь
        if User.objects.filter(email=email).exists():
            return {
                'success': False,
                'message': 'Пользователь с этим email уже существует'
            }

        # Валидация пароля
        try:
            validate_password(password)
        except ValidationError as e:
            return {
                'success': False,
                'message': 'Неверный пароль',
                'errors': e.messages
            }

        # Создаем пользователя
        user = User.objects.create_user(
            email=email,
            password=password,
            **kwargs
        )
        user.email_verified = False
        user.save()

        return {
            'success': True,
            'message': 'Пользователь создан',
            'user': user
        }

    @classmethod
    def login_with_password(cls, email: str, password: str) -> Optional[User]:
        """
        Вход по email с паролем
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        if not user.check_password(password):
            return None

        user.last_activity = timezone.now()
        user.save()

        return user

    @classmethod
    def login_with_otp(cls, email: str, otp: str) -> Optional[User]:
        """
        Вход по email с OTP
        """
        # Проверяем OTP
        if not cls.verify_otp(email, otp):
            return None

        # Находим пользователя
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        user.email_verified = True
        user.last_activity = timezone.now()
        user.save()

        return user

    @classmethod
    def resend_otp(cls, email: str) -> Dict:
        """
        Повторная отправка OTP
        """
        if not User.objects.filter(email=email).exists():
            return {
                'success': False,
                'message': 'Пользователь не найден'
            }

        return cls.send_otp(email)

    @classmethod
    def request_password_reset(cls, email: str) -> Dict:
        """
        Запрос на сброс пароля
        """
        if not User.objects.filter(email=email).exists():
            return {
                'success': False,
                'message': 'Пользователь не найден'
            }

        otp = cls.generate_otp(email)
        success = EmailSender.send(
            to=email,
            subject='Сброс пароля',
            body=f'Код для сброса пароля: {otp}'
        )

        if success:
            return {
                'success': True,
                'message': 'Код для сброса пароля отправлен'
            }
        else:
            return {
                'success': False,
                'message': 'Ошибка отправки email'
            }

    @classmethod
    def reset_password(cls, email: str, otp: str, new_password: str) -> Dict:
        """
        Сброс пароля
        """
        if not cls.verify_otp(email, otp):
            return {
                'success': False,
                'message': 'Неверный код'
            }

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return {
                'success': False,
                'message': 'Пользователь не найден'
            }

        user.set_password(new_password)
        user.save()

        return {
            'success': True,
            'message': 'Пароль успешно изменен'
        }