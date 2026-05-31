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


class CookingMethod(models.Model):
    """Метод приготовления — кулинарная техника"""

    CATEGORY_CHOICES = [
        ('thermal', 'Тепловая обработка'),
        ('preparation', 'Подготовка продуктов'),
        ('shaping', 'Формование'),
        ('other', 'Прочее'),
    ]

    # Основная информация
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='thermal')
    short_description = models.CharField(max_length=200, verbose_name='Краткое описание')

    # Развёрнутое описание
    description = models.TextField(verbose_name='Подробное описание техники')
    scientific_background = models.TextField(blank=True, verbose_name='Научное обоснование')

    # Параметры
    typical_temperature = models.CharField(max_length=50, blank=True, verbose_name='Типичная температура')
    typical_duration = models.CharField(max_length=50, blank=True, verbose_name='Типичная длительность')

    # Советы
    tips = models.TextField(blank=True, verbose_name='Советы и хитрости')
    common_mistakes = models.TextField(blank=True, verbose_name='Типичные ошибки')

    # Визуальный контент
    icon = models.CharField(max_length=50, default='fa-fire', verbose_name='Иконка (FontAwesome)')
    color = models.CharField(max_length=20, default='amber', verbose_name='Цвет темы')

    # Для продвинутых пользователей
    advanced_notes = models.TextField(blank=True, verbose_name='Для опытных кулинаров')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Метод приготовления'
        verbose_name_plural = 'Методы приготовления'


class IngredientPreparation(models.Model):
    """Подготовка продуктов (нарезка, замачивание, маринование)"""
    name = models.CharField(max_length=100)  # "шинковка", "кубики", "соломка"
    description = models.TextField()
    image = models.ImageField(upload_to='preparations/', null=True, blank=True)
    video_url = models.URLField(blank=True)
    time_factor = models.FloatField(default=1.0, help_text="Коэффициент увеличения времени")
    tips = models.TextField(blank=True)

    def __str__(self):
        return self.name


class RecommendedUtensil(models.Model):
    """Рекомендованная утварь для шага"""
    name = models.CharField(max_length=100)  # "нож для удаления косточек", "трубчатый нож"
    description = models.TextField()
    image = models.ImageField(upload_to='utensils/', null=True, blank=True)
    alternative = models.CharField(max_length=200, blank=True, help_text="Чем можно заменить")
    care_instructions = models.TextField(blank=True)

    def __str__(self):
        return self.name


class CookingStep(models.Model):
    """Шаг приготовления (расширенный)"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps')
    order = models.IntegerField()
    title = models.CharField(max_length=200)
    instruction = models.TextField()
    image = models.ImageField(upload_to='steps/', null=True, blank=True)

    # Связи с новыми модулями
    preparation = models.ForeignKey(IngredientPreparation, on_delete=models.SET_NULL, null=True, blank=True)
    cooking_method = models.ForeignKey(CookingMethod, on_delete=models.SET_NULL, null=True, blank=True)
    utensils = models.ManyToManyField(RecommendedUtensil, blank=True)

    # Параметры
    duration = models.IntegerField(default=0, help_text="Длительность шага в минутах")
    temperature = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.order}. {self.title}"