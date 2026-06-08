# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Расширенная модель пользователя"""
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    telegram_id = models.CharField(max_length=100, blank=True)
    theme = models.CharField(max_length=10, choices=[('light', 'Светлая'), ('dark', 'Тёмная')], default='light')
    email_notifications = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'