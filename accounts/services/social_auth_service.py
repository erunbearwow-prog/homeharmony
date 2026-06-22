# accounts/services/social_auth_service.py

import requests
from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import User

User = get_user_model()


class SocialAuthService:
    """
    Сервис аутентификации через социальные сети
    """

    # Конфигурация провайдеров
    PROVIDERS = {
        'google': {
            'auth_url': 'https://accounts.google.com/o/oauth2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'userinfo_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
        },
        'vk': {
            'auth_url': 'https://oauth.vk.com/authorize',
            'token_url': 'https://oauth.vk.com/access_token',
            'userinfo_url': 'https://api.vk.com/method/users.get',
        },
        'yandex': {
            'auth_url': 'https://oauth.yandex.ru/authorize',
            'token_url': 'https://oauth.yandex.ru/token',
            'userinfo_url': 'https://login.yandex.ru/info',
        },
    }

    @classmethod
    def get_provider_config(cls, provider: str) -> Dict:
        """Получить конфигурацию провайдера"""
        if provider not in cls.PROVIDERS:
            raise ValueError(f'Неизвестный провайдер: {provider}')
        return cls.PROVIDERS[provider]

    @classmethod
    def exchange_code(cls, provider: str, code: str, redirect_uri: str) -> Optional[Dict]:
        """
        Обменивает код авторизации на токен доступа
        """
        config = cls.get_provider_config(provider)
        # Здесь логика получения токена
        # В реальном проекте используйте библиотеку allauth или python-social-auth
        pass

    @classmethod
    def get_user_info(cls, provider: str, access_token: str) -> Optional[Dict]:
        """
        Получает информацию о пользователе от провайдера
        """
        config = cls.get_provider_config(provider)

        # В реальном проекте здесь логика парсинга ответов разных провайдеров
        # Для каждого провайдера нужно парсить по-своему:
        # - Google: id, email, name, picture
        # - VK: id, first_name, last_name, photo
        # - Yandex: id, login, real_name, default_avatar_id

        pass

    @classmethod
    def login(cls, provider: str, social_id: str, user_data: Dict) -> Optional[User]:
        """
        Вход через социальную сеть
        """
        # Ищем пользователя по social_id
        # Для этого нужно хранить social_id в модели User
        # Добавим поле social_id и social_provider

        # Ищем существующего пользователя
        user = User.objects.filter(
            social_provider=provider,
            social_id=social_id
        ).first()

        if user:
            # Обновляем данные
            user.last_activity = timezone.now()
            user.save()
            return user

        # Если пользователь не найден, создаем нового
        # Проверяем, есть ли пользователь с таким email
        email = user_data.get('email')
        if email:
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                # Привязываем социальный аккаунт к существующему пользователю
                existing_user.social_provider = provider
                existing_user.social_id = social_id
                existing_user.last_activity = timezone.now()
                existing_user.save()
                return existing_user

        # Создаем нового пользователя
        user = User.objects.create_user(
            username=user_data.get('username') or f'social_{social_id}',
            email=email,
            social_provider=provider,
            social_id=social_id,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
        )
        user.social_provider = provider
        user.social_id = social_id
        user.save()

        return user

    @classmethod
    def get_authorization_url(cls, provider: str, redirect_uri: str) -> str:
        """
        Возвращает URL для авторизации через соцсеть
        """
        config = cls.get_provider_config(provider)
        # Формируем URL с параметрами
        # В реальном проекте используйте библиотеку allauth
        pass