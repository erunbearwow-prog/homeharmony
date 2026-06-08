from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    """Расширенная модель пользователя"""
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    telegram_id = models.CharField(max_length=100, blank=True)
    theme = models.CharField(max_length=10, choices=[('light', 'Светлая'), ('dark', 'Тёмная')], default='light')
    email_notifications = models.BooleanField(default=True)

    # Избранное
    favorite_recipes = models.ManyToManyField('kitchen.Recipe', blank=True, related_name='favorited_by')
    favorite_articles = models.ManyToManyField('pages.Article', blank=True, related_name='favorited_by')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class UserTask(models.Model):
    """Личные задачи пользователя"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    category = models.CharField(max_length=50, choices=[
        ('cleaning', 'Уборка'), ('shopping', 'Покупки'), ('repair', 'Ремонт'), ('other', 'Другое')
    ], default='other')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']