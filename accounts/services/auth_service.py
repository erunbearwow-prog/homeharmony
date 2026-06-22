# accounts/services/auth_service.py

from typing import Optional, Dict
from django.contrib.auth import get_user_model
from .phone_auth_service import PhoneAuthService
from .email_auth_service import EmailAuthService
from .social_auth_service import SocialAuthService

User = get_user_model()


class AuthService:
    """
    Главный фасад для аутентификации.
    Объединяет все способы входа.
    """

    @staticmethod
    def login_by_phone(phone_number: str, otp: str) -> Optional[User]:
        """Вход по телефону"""
        return PhoneAuthService.login(phone_number, otp)

    @staticmethod
    def login_by_email(email: str, password: str) -> Optional[User]:
        """Вход по email с паролем"""
        return EmailAuthService.login_with_password(email, password)

    @staticmethod
    def login_by_email_otp(email: str, otp: str) -> Optional[User]:
        """Вход по email с OTP"""
        return EmailAuthService.login_with_otp(email, otp)

    @staticmethod
    def login_by_social(social_type: str, social_id: str, user_data: Dict) -> Optional[User]:
        """Вход через социальные сети"""
        return SocialAuthService.login(social_type, social_id, user_data)

    @staticmethod
    def register_phone(phone_number: str) -> Dict:
        """Регистрация по телефону"""
        return PhoneAuthService.register(phone_number)

    @staticmethod
    def register_email(email: str, password: str, **kwargs) -> Dict:
        """Регистрация по email"""
        return EmailAuthService.register(email, password, **kwargs)

    @staticmethod
    def generate_tokens(user) -> Dict:
        """Генерация JWT токенов"""
        from ..utils.jwt_utils import generate_jwt_tokens
        return generate_jwt_tokens(user)