from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit


class Recipe(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание', blank=True)
    cooking_time = models.IntegerField(verbose_name='Время приготовления (мин)')
    difficulty = models.CharField(max_length=20, choices=[
        ('easy', 'Лёгкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ], default='medium', verbose_name='Сложность')
    servings = models.IntegerField(default=4, verbose_name='Порций')
    calories = models.IntegerField(default=0, verbose_name='Калории')
    protein = models.IntegerField(default=0, verbose_name='Белки')
    fat = models.IntegerField(default=0, verbose_name='Жиры')
    carbs = models.IntegerField(default=0, verbose_name='Углеводы')

    # Оригинальное изображение
    image = models.ImageField(upload_to='recipes/original/', verbose_name='Изображение')

    # Автоматически генерируемые версии
    image_400w = ImageSpecField(
        source='image',
        processors=[ResizeToFit(400, 250)],
        format='WEBP',
        options={'quality': 85}
    )
    image_800w = ImageSpecField(
        source='image',
        processors=[ResizeToFit(800, 500)],
        format='WEBP',
        options={'quality': 85}
    )
    image_1200w = ImageSpecField(
        source='image',
        processors=[ResizeToFit(1200, 750)],
        format='WEBP',
        options={'quality': 85}
    )

    # Для старых браузеров (fallback)
    image_fallback = ImageSpecField(
        source='image',
        processors=[ResizeToFit(800, 500)],
        format='JPEG',
        options={'quality': 85}
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'