# accounts/managers/user_manager.py

from django.contrib.auth.models import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """Менеджер для модели User"""

    def _create_user(self, username, email, phone_number, password, **extra_fields):
        """Создает пользователя"""
        if not username and not email and not phone_number:
            raise ValueError('Укажите хотя бы один способ идентификации')

        if email:
            email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username=None, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, phone_number, password, **extra_fields)

    def create_superuser(self, username=None, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self._create_user(username, email, phone_number, password, **extra_fields)

    def get_by_phone(self, phone_number):
        """Получить пользователя по телефону"""
        try:
            return self.get(phone_number=phone_number)
        except self.model.DoesNotExist:
            return None

    def get_by_email(self, email):
        """Получить пользователя по email"""
        try:
            return self.get(email=email)
        except self.model.DoesNotExist:
            return None

    def get_active_users(self):
        """Получить активных пользователей"""
        return self.filter(is_active=True)