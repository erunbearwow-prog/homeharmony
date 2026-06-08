from django.db import models
from django.conf import settings


class ForumTopic(models.Model):
    """Тема на форуме"""
    title = models.CharField(max_length=200)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_topics')
    category = models.CharField(max_length=50, choices=[
        ('cooking', 'Кулинария'), ('cleaning', 'Уборка'), ('budget', 'Бюджет'),
        ('repair', 'Ремонт'), ('health', 'Здоровье'), ('other', 'Общее')
    ])
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'Темы форума'


class ForumPost(models.Model):
    """Сообщение на форуме"""
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts')
    content = models.TextField()
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='liked_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']