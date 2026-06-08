from django.db import models


class CleaningTask(models.Model):
    """Задача по уборке"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    room = models.CharField(max_length=100, choices=[
        ('kitchen', 'Кухня'), ('bathroom', 'Ванная'), ('living', 'Гостиная'),
        ('bedroom', 'Спальня'), ('hallway', 'Прихожая'), ('other', 'Другое')
    ])
    frequency = models.CharField(max_length=50, choices=[
        ('daily', 'Ежедневно'), ('weekly', 'Еженедельно'), ('monthly', 'Ежемесячно'),
        ('seasonal', 'Сезонно'), ('yearly', 'Ежегодно')
    ])
    estimated_minutes = models.PositiveIntegerField(default=30)
    order = models.PositiveIntegerField(default=0)
    icon = models.CharField(max_length=50, default='fa-broom')

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Задача по уборке'
        verbose_name_plural = 'Задачи по уборке'


class CleaningTip(models.Model):
    """Совет по уборке"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='cleaning_tips/', null=True, blank=True)
    category = models.CharField(max_length=50, choices=[
        ('stains', 'Выведение пятен'), ('organization', 'Организация'),
        ('tools', 'Средства и инструменты'), ('hacks', 'Лайфхаки')
    ])
    created_at = models.DateTimeField(auto_now_add=True)