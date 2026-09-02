# kitchen/models.py

from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator
from slugify import slugify
from django.urls import reverse
from django.db.models.functions import Lower
import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings

# ======================= ГЛОБАЛЬНЫЕ КОНСТАНТЫ =======================
UNIT_CHOICES = [
    ('г', 'грамм'),
    ('кг', 'килограмм'),
    ('мл', 'миллилитр'),
    ('л', 'литр'),
    ('шт', 'штука'),
    ('ст.л.', 'столовая ложка'),
    ('ч.л.', 'чайная ложка'),
    ('щеп.', 'щепотка'),
]


# ======================= ФУНКЦИИ ДЛЯ ГЕНЕРАЦИИ ПУТЕЙ =======================
def recipe_main_image_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    slug = slugify(instance.title)[:50]
    return os.path.join('recipes', f"{instance.id}_{slug}", f"main.{ext}")


def recipe_step_image_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    recipe_slug = slugify(instance.recipe.title)[:50]
    step_slug = slugify(instance.title)[:40] if instance.title else f"step_{instance.order}"
    return os.path.join('recipe_steps', f"{instance.recipe.id}_{recipe_slug}", 'steps',
                        f"{instance.order:03d}_{step_slug}.{ext}")


def ingredient_image_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    slug = slugify(instance.name)[:50]
    return os.path.join('ingredients', f"{instance.id}_{slug}.{ext}")


def product_image_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    slug = slugify(instance.name)[:50]
    return os.path.join('products', f"{instance.id}_{slug}.{ext}")


# ======================= 1. КУХНИ МИРА =======================
class Cuisine(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(unique=True, blank=True, max_length=100, verbose_name='URL')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    region = models.CharField(max_length=100, blank=True, verbose_name='Регион')
    description = models.TextField(blank=True, verbose_name='Описание')
    traditions = models.TextField(blank=True, verbose_name='Традиции')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Кухня'
        verbose_name_plural = 'Кухни'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return self.name

    def _generate_unique_slug(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        while Cuisine.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('cuisine_detail', kwargs={'slug': self.slug})

    def get_ancestors(self):
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors[::-1]


# ======================= 2. КАТЕГОРИИ ИНГРЕДИЕНТОВ =======================
class IngredientCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    icon = models.CharField(max_length=50, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Категория ингредиентов"
        verbose_name_plural = "Категории ингредиентов"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def level(self):
        if self.parent is None:
            return 0
        elif self.parent.parent is None:
            return 1
        else:
            return 2

    @property
    def root_parent(self):
        if self.level == 0:
            return None
        elif self.level == 1:
            return self
        else:
            current = self
            while current.parent and current.parent.parent:
                current = current.parent
            return current.parent if current.parent else current

    @property
    def second_level_parent(self):
        if self.level == 2:
            return self.parent
        return None

    @property
    def full_hierarchy(self):
        if self.parent is None:
            return self.name
        elif self.parent.parent is None:
            return f"{self.parent.name} → {self.name}"
        else:
            ancestors = []
            current = self
            while current:
                ancestors.append(current.name)
                current = current.parent
            return " → ".join(reversed(ancestors))


# ======================== АБСТРАКТНЫЙ ИНГРЕДИЕНТ ========================
# kitchen/models.py

class AbstractIngredient(models.Model):
    """Абстрактный ингредиент — базовый сферический конь с КБЖУ"""

    # ===== ОСНОВНЫЕ ПОЛЯ =====
    name = models.CharField(max_length=300, db_index=True, verbose_name="Название")
    name_normalized = models.CharField(max_length=300, blank=True, db_index=True,
                                       verbose_name="Нормализованное название")

    synonyms = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Синонимы",
        help_text="Альтернативные названия через запятую (например: томат, помидор; курага, урюк)"
    )

    # Краткое описание для карточек и списков
    short_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Краткое описание",
        help_text="Краткая характеристика для карточек и списков (до 500 символов)"
    )

    # Полное описание
    description = models.TextField(
        blank=True,
        verbose_name="Полное описание (HTML)",
        help_text="Поддерживает HTML-разметку: <b>жирный</b>, <i>курсив</i>, <a href='...'>ссылки</a>, <ul><li>списки</li></ul>"
    )

    # ===== КАТЕГОРИЯ =====
    category = models.ForeignKey(
        'IngredientCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория"
    )

    # ===== КАТЕГОРИЯ =====
    # ===== Скурихин И. М., Тутельян В. А.
    # ===== Таблицы химического состава и калорийности российских продуктов питания : справочник.
    # ===== М. : ДеЛи принт, 2008. — 275 с. — ISBN 5-943431-22-5.
    skurikhin_category = models.JSONField(
        verbose_name="Категории справочника Скурихина",
        help_text="Иерархия категорий из справочника в формате JSON",
        null=True,
        blank=True
    )

    # ===== СЕМАНТИЧЕСКИЕ ТЕГИ =====
    semantic_tags = models.ManyToManyField(
        'SemanticTag',
        blank=True,
        related_name='abstract_ingredients',
        verbose_name="Семантические теги"
    )

    # ===== СЕМАНТИЧЕСКИЕ ДАННЫЕ (СТРУКТУРИРОВАННЫЕ) =====
    semantic_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Семантические данные",
        help_text="Структурированная информация: свойства, методы, сочетаемость, замены"
    )

    # ===== КБЖУ =====
    calories = models.FloatField(null=True, blank=True, verbose_name="Калории, ккал")
    protein = models.FloatField(null=True, blank=True, verbose_name="Белки, г")
    fat = models.FloatField(null=True, blank=True, verbose_name="Жиры, г")
    carbohydrates = models.FloatField(null=True, blank=True, verbose_name="Углеводы, г")

    # ===== МАКРОНУТРИЕНТЫ =====
    fiber = models.FloatField(null=True, blank=True, verbose_name="Пищевые волокна, г")
    sugar = models.FloatField(null=True, blank=True, verbose_name="Сахара, г")
    water = models.FloatField(null=True, blank=True, verbose_name="Вода, г")
    ash = models.FloatField(null=True, blank=True, verbose_name="Зола, г")
    starch = models.FloatField(null=True, blank=True, verbose_name="Крахмал, г")

    # ===== ВИТАМИНЫ =====
    vitamin_a = models.FloatField(null=True, blank=True, verbose_name="Витамин А, мкг")
    beta_carotene = models.FloatField(null=True, blank=True, verbose_name="Бета-каротин, мг")
    vitamin_b1 = models.FloatField(null=True, blank=True, verbose_name="Витамин B1, мг")
    vitamin_b2 = models.FloatField(null=True, blank=True, verbose_name="Витамин B2, мг")
    vitamin_b3 = models.FloatField(null=True, blank=True, verbose_name="Витамин B3, мг")
    vitamin_b4 = models.FloatField(null=True, blank=True, verbose_name="Витамин B4, мг")
    vitamin_b5 = models.FloatField(null=True, blank=True, verbose_name="Витамин B5, мг")
    vitamin_b6 = models.FloatField(null=True, blank=True, verbose_name="Витамин B6, мг")
    vitamin_b7 = models.FloatField(null=True, blank=True, verbose_name="Витамин B7 (биотин), мкг")
    vitamin_b9_folate = models.FloatField(null=True, blank=True, verbose_name="Витамин B9 (фолаты), мкг")
    vitamin_b12 = models.FloatField(null=True, blank=True, verbose_name="Витамин B12, мкг")
    vitamin_c = models.FloatField(null=True, blank=True, verbose_name="Витамин C, мг")
    vitamin_d = models.FloatField(null=True, blank=True, verbose_name="Витамин D, мкг")
    vitamin_e = models.FloatField(null=True, blank=True, verbose_name="Витамин E, мг")
    vitamin_k = models.FloatField(null=True, blank=True, verbose_name="Витамин K, мкг")

    # ===== МАКРОЭЛЕМЕНТЫ =====
    potassium = models.FloatField(null=True, blank=True, verbose_name="Калий, мг")
    calcium = models.FloatField(null=True, blank=True, verbose_name="Кальций, мг")
    magnesium = models.FloatField(null=True, blank=True, verbose_name="Магний, мг")
    sodium = models.FloatField(null=True, blank=True, verbose_name="Натрий, мг")
    phosphorus = models.FloatField(null=True, blank=True, verbose_name="Фосфор, мг")
    sulfur = models.FloatField(null=True, blank=True, verbose_name="Сера, мг")
    silicon = models.FloatField(null=True, blank=True, verbose_name="Кремний, мг")
    chlorine = models.FloatField(null=True, blank=True, verbose_name="Хлор, мг")

    # ===== МИКРОЭЛЕМЕНТЫ =====
    iron = models.FloatField(null=True, blank=True, verbose_name="Железо, мг")
    manganese = models.FloatField(null=True, blank=True, verbose_name="Марганец, мг")
    copper = models.FloatField(null=True, blank=True, verbose_name="Медь, мкг")
    selenium = models.FloatField(null=True, blank=True, verbose_name="Селен, мкг")
    zinc = models.FloatField(null=True, blank=True, verbose_name="Цинк, мг")
    aluminum = models.FloatField(null=True, blank=True, verbose_name="Алюминий, мкг")
    boron = models.FloatField(null=True, blank=True, verbose_name="Бор, мкг")
    vanadium = models.FloatField(null=True, blank=True, verbose_name="Ванадий, мкг")
    iodine = models.FloatField(null=True, blank=True, verbose_name="Йод, мкг")
    cobalt = models.FloatField(null=True, blank=True, verbose_name="Кобальт, мкг")
    lithium = models.FloatField(null=True, blank=True, verbose_name="Литий, мкг")
    molybdenum = models.FloatField(null=True, blank=True, verbose_name="Молибден, мкг")
    nickel = models.FloatField(null=True, blank=True, verbose_name="Никель, мкг")
    rubidium = models.FloatField(null=True, blank=True, verbose_name="Рубидий, мкг")
    fluorine = models.FloatField(null=True, blank=True, verbose_name="Фтор, мкг")
    chromium = models.FloatField(null=True, blank=True, verbose_name="Хром, мкг")

    # ===== ЖИРНЫЕ КИСЛОТЫ =====
    saturated_fat = models.FloatField(null=True, blank=True, verbose_name="Насыщенные жирные кислоты, г")
    trans_fat = models.FloatField(null=True, blank=True, verbose_name="Трансжиры, г")
    cholesterol = models.FloatField(null=True, blank=True, verbose_name="Холестерин, мг")
    omega_3 = models.FloatField(null=True, blank=True, verbose_name="Омега-3, г")
    omega_6 = models.FloatField(null=True, blank=True, verbose_name="Омега-6, г")

    # ===== ОРГАНИЧЕСКИЕ КИСЛОТЫ =====
    organic_acids = models.FloatField(null=True, blank=True, verbose_name="Органические кислоты, г")

    # ===== ИСТОЧНИК =====
    data_source = models.CharField(max_length=500, default='pbprog.ru', blank=True, verbose_name="Источник данных")
    fdc_id = models.IntegerField(unique=True, null=True, blank=True, db_index=True, verbose_name="FDC ID")

    # ===== ИЗОБРАЖЕНИЕ =====
    image = models.ImageField(
        upload_to='abstract_ingredients/',
        null=True,
        blank=True,
        verbose_name="Изображение"
    )

    # ===== СЛУЖЕБНЫЕ =====
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Абстрактный ингредиент"
        verbose_name_plural = "Абстрактные ингредиенты"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['fdc_id']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name_normalized:
            self.name_normalized = self.name.replace(' ', '').lower()
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.name

    @property
    def has_complete_nutrients(self):
        return all([
            self.calories is not None,
            self.protein is not None,
            self.fat is not None,
            self.carbohydrates is not None,
        ])


# ========================= БРЕНДИРОВАННЫЙ ИНГРЕДИЕНТ =========================
class BrandedIngredient(models.Model):
    abstract = models.ForeignKey(
        AbstractIngredient,
        on_delete=models.CASCADE,
        related_name='branded_versions',
        verbose_name="Абстрактный ингредиент"
    )

    brand = models.CharField(max_length=200, db_index=True, verbose_name="Бренд")
    product_name = models.CharField(max_length=300, verbose_name="Название продукта")
    barcode = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Штрих-код"
    )

    calories = models.FloatField(null=True, blank=True, verbose_name="Калории, ккал")
    protein = models.FloatField(null=True, blank=True, verbose_name="Белки, г")
    fat = models.FloatField(null=True, blank=True, verbose_name="Жиры, г")
    carbohydrates = models.FloatField(null=True, blank=True, verbose_name="Углеводы, г")

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена за упаковку"
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Вес упаковки, г"
    )

    store = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="Магазин"
    )
    store_url = models.URLField(blank=True, verbose_name="Ссылка на товар")

    is_available = models.BooleanField(default=True, verbose_name="В наличии")
    last_checked = models.DateTimeField(null=True, blank=True, verbose_name="Последняя проверка")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Создал пользователь"
    )

    class Meta:
        verbose_name = "Брендированный продукт"
        verbose_name_plural = "Брендированные продукты"
        unique_together = ['brand', 'product_name']
        indexes = [
            models.Index(fields=['brand']),
            models.Index(fields=['barcode']),
            models.Index(fields=['store']),
        ]

    def __str__(self):
        return f"{self.brand} {self.product_name}"

    @property
    def full_name(self):
        return f"{self.brand} {self.product_name}"

    @property
    def price_per_100g(self):
        if self.price and self.weight and self.weight > 0:
            return round((float(self.price) / float(self.weight)) * 100, 2)
        return None

    @property
    def price_per_kg(self):
        if self.price_per_100g:
            return round(self.price_per_100g * 10, 2)
        return None

    def get_nutrients(self):
        return {
            'calories': self.calories or self.abstract.calories,
            'protein': self.protein or self.abstract.protein,
            'fat': self.fat or self.abstract.fat,
            'carbohydrates': self.carbohydrates or self.abstract.carbohydrates,
        }

    def compare_with_abstract(self):
        abs_nutrients = {
            'calories': self.abstract.calories,
            'protein': self.abstract.protein,
            'fat': self.abstract.fat,
            'carbohydrates': self.abstract.carbohydrates,
        }
        branded_nutrients = self.get_nutrients()

        return {
            nutrient: {
                'abstract': abs_nutrients.get(nutrient),
                'branded': branded_nutrients.get(nutrient),
                'diff': round(branded_nutrients.get(nutrient, 0) - (abs_nutrients.get(nutrient) or 0), 2)
            }
            for nutrient in ['calories', 'protein', 'fat', 'carbohydrates']
        }

# ======================= 4. ДИЕТЫ =======================
class Diet(models.Model):
    name = models.CharField(max_length=100)
    authority = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    # ✅ ИСПРАВЛЕНО: Ingredient → AbstractIngredient
    allowed_ingredients = models.ManyToManyField(
        'AbstractIngredient',
        blank=True,
        related_name='allowed_for_diets'
    )
    # ✅ ИСПРАВЛЕНО: Ingredient → AbstractIngredient
    prohibited_ingredients = models.ManyToManyField(
        'AbstractIngredient',
        blank=True,
        related_name='prohibited_for_diets'
    )
    allowed_methods = models.TextField(blank=True)
    nutritional_guidelines = models.TextField(blank=True)
    medical_indications = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Диета'
        verbose_name_plural = 'Диеты'

    def __str__(self):
        return self.name


# ======================= 5. МЕТОДЫ ПРИГОТОВЛЕНИЯ =======================
class CookingMethod(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    code = models.CharField(max_length=50, unique=True, verbose_name='Код')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_heat_treatment = models.BooleanField(default=True, verbose_name='Тепловая обработка')
    sort_order = models.IntegerField(default=0, verbose_name='Порядок')

    tips = models.TextField(blank=True, verbose_name='Советы')
    common_mistakes = models.TextField(blank=True, verbose_name='Типичные ошибки')
    scientific_background = models.TextField(blank=True, verbose_name='Научная база')
    advanced_notes = models.TextField(blank=True, verbose_name='Для продвинутых')

    oil_absorption_rates = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Коэффициенты впитываемости масла',
        help_text='Формат: {"продукт": 0.08, "продукт2": 0.12}'
    )

    recommended_temperature_min = models.IntegerField(null=True, blank=True, verbose_name='Мин. температура, °C')
    recommended_temperature_max = models.IntegerField(null=True, blank=True, verbose_name='Макс. температура, °C')

    cut_shape_factors = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Коэффициенты для форм нарезки',
        help_text='Формат: {"брусочками": 1.0, "соломкой": 1.5, "кубиками": 1.2, "кружочками": 0.8}'
    )

    BREADING_CHOICES = [
        ('none', 'Без панировки'),
        ('flour', 'Только мука'),
        ('batter', 'Кляр'),
        ('classic', 'Классическая (мука+яйцо+сухари)'),
        ('panko', 'Панко (японские сухари)'),
        ('double', 'Двойная панировка'),
    ]

    breading_type = models.CharField(max_length=20, choices=BREADING_CHOICES, default='none', verbose_name='Тип панировки')

    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', '🟢 Простая — справится каждый'),
            ('medium', '🟡 Средняя — нужна практика'),
            ('hard', '🔴 Сложная — для опытных'),
        ],
        default='medium',
        verbose_name='Сложность'
    )

    step_by_step_guide = models.TextField(
        blank=True,
        verbose_name='Пошаговое руководство',
        help_text='Подробное описание каждого шага'
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Иконка (Emoji)',
        help_text='Например: 🍳, 🔥, 💧'
    )

    image = models.ImageField(
        upload_to='cooking_methods/',
        null=True,
        blank=True,
        verbose_name='Изображение'
    )

    video_url = models.URLField(
        blank=True,
        verbose_name='Ссылка на видео-урок',
        help_text='YouTube или другой видео-хостинг'
    )

    beginner_tips = models.TextField(
        blank=True,
        verbose_name='Советы для начинающих',
        help_text='Что важно знать, если делаешь это впервые'
    )

    can_cook_with_children = models.BooleanField(
        default=False,
        verbose_name='Можно готовить с детьми'
    )

    child_friendly_notes = models.TextField(
        blank=True,
        verbose_name='Заметки для готовки с детьми'
    )

    best_ingredients = models.ManyToManyField(
        'AbstractIngredient',
        blank=True,
        related_name='best_methods',
        verbose_name='Лучшие ингредиенты для этого метода'
    )

    class Meta:
        verbose_name = 'Способ обработки'
        verbose_name_plural = 'Способы обработки'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


# ======================= 5.1 Нормы потерь =======================
class ProductLossNorm(models.Model):
    CATEGORY_CHOICES = [
        ('vegetable', 'Овощи'),
        ('fruit', 'Фрукты/Ягоды'),
        ('meat', 'Мясо'),
        ('poultry', 'Птица'),
        ('fish', 'Рыба/Морепродукты'),
        ('grain', 'Крупы/Макароны'),
        ('mushroom', 'Грибы'),
        ('dairy', 'Молочные продукты'),
        ('egg', 'Яйца'),
    ]

    product_name = models.CharField(max_length=200, verbose_name='Продукт')
    product_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name='Категория')
    processing_method = models.ForeignKey(CookingMethod, on_delete=models.CASCADE, verbose_name='Способ обработки')

    cold_loss_percent = models.DecimalField(max_digits=5, decimal_places=1, default=0, verbose_name='Потери при холодной обработке, %')
    heat_loss_percent = models.DecimalField(max_digits=5, decimal_places=1, default=0, verbose_name='Потери при тепловой обработке, %')
    season_note = models.CharField(max_length=100, blank=True, verbose_name='Сезон/Примечание')
    source = models.CharField(max_length=100, default='Сборник рецептур', verbose_name='Источник')

    PROCESSING_BEHAVIOR = [
        ('loss', 'Потери (уменьшение веса)'),
        ('gain', 'Увеличение веса (впитывание воды)'),
    ]

    processing_behavior = models.CharField(max_length=10, choices=PROCESSING_BEHAVIOR, default='loss', verbose_name='Поведение при обработке')
    gain_factor = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Коэффициент увеличения веса')

    class Meta:
        verbose_name = 'Норма потерь'
        verbose_name_plural = 'Нормы потерь'
        unique_together = ['product_name', 'processing_method', 'season_note']

    def __str__(self):
        return f'{self.product_name} → {self.processing_method.name}'

    @property
    def total_loss_percent(self):
        return (self.cold_loss_percent or 0) + (self.heat_loss_percent or 0)

    @property
    def yield_coefficient(self):
        return 1 - self.total_loss_percent / 100


# ======================= 6. ПОДГОТОВКА ПРОДУКТОВ =======================
class IngredientPreparation(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='preparations/', null=True, blank=True)
    video_url = models.URLField(blank=True)
    time_factor = models.FloatField(default=1.0)
    waste_percentage = models.FloatField(default=0)
    tips = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Подготовка продукта'
        verbose_name_plural = 'Подготовка продуктов'

    def __str__(self):
        return self.name


# ======================= 7. РЕКОМЕНДОВАННАЯ УТВАРЬ =======================
class RecommendedUtensil(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='utensils/', null=True, blank=True)
    alternative = models.CharField(max_length=200, blank=True)
    care_instructions = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Утварь'
        verbose_name_plural = 'Утварь'

    def __str__(self):
        return self.name


# ======================= 8. РЕЦЕПТЫ =======================
class Recipe(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Легкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]
    title = models.CharField(max_length=200)
    cuisine = models.ForeignKey(Cuisine, on_delete=models.SET_NULL, null=True, blank=True)
    author = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    serving_the_dish = models.TextField(blank=True)
    storage_conditions = models.TextField(blank=True)
    total_time = models.IntegerField(default=0)
    servings = models.IntegerField(default=4)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    is_professional = models.BooleanField(default=False)
    components = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='parent_recipes')
    image = models.ImageField(upload_to=recipe_main_image_path, null=True, blank=True)
    video = models.URLField(blank=True)
    calories = models.IntegerField(default=0)
    protein = models.IntegerField(default=0)
    fat = models.IntegerField(default=0)
    carbs = models.IntegerField(default=0)
    diet_tags = models.ManyToManyField(Diet, blank=True)
    related_recipes = models.ManyToManyField('self', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Добавляем поле для типа рецепта
    RECIPE_TYPE_CHOICES = [
        ('home', 'Домашний рецепт'),
        ('ttk', 'ТТК (Технико-технологическая карта)'),
        ('semi_finished', 'Полуфабрикат'),
    ]
    recipe_type = models.CharField(
        max_length=20,
        choices=RECIPE_TYPE_CHOICES,
        default='home',
        verbose_name='Тип рецепта'
    )

    # Поле для идентификации ТТК
    ttk_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Код ТТК',
        help_text='Например: ТТК-001-2024'
    )

    # Поле для хранения технологического процесса (для ТТК)
    technological_process = models.TextField(
        blank=True,
        verbose_name='Технологический процесс',
        help_text='Подробное описание технологического процесса для ТТК'
    )

    # Поле для хранения требований к качеству (для ТТК)
    quality_requirements = models.TextField(
        blank=True,
        verbose_name='Требования к качеству',
        help_text='Органолептические показатели, сроки хранения и т.д.'
    )

    # Поле для хранения норм расхода (для ТТК)
    consumption_rates = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Нормы расхода сырья',
        help_text='Формат: {"ингредиент": {"брутто": 100, "нетто": 80, "потери": 20}}'
    )

    # Поле для выхода готового блюда (для ТТК)
    yield_weight = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Выход готового блюда, г'
    )

    # Поле для порционирования (для ТТК)
    portion_size = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Размер порции, г'
    )

    # Поле для хранения технологических карт (для ТТК)
    tech_card_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Данные техкарты',
        help_text='Полные данные ТТК в структурированном виде'
    )

    # Поле для оформления и подачи (текст)
    plating = models.TextField(
        blank=True,
        verbose_name='Оформление и подача',
        help_text='Рекомендации по оформлению и подаче блюда'
    )

    # Изображение для оформления
    plating_image = models.ImageField(
        upload_to='recipe_plating/',
        null=True,
        blank=True,
        verbose_name='Изображение оформления',
        help_text='Фото готового блюда или варианта подачи'
    )

    # ===== ПОЛЯ ДЛЯ СОХРАНЕННЫХ РЕЦЕПТОВ =====
    is_saved_variant = models.BooleanField(
        default=False,
        verbose_name='Это сохраненный вариант',
        help_text='Отмечается, если рецепт является пользовательским вариантом'
    )

    original_recipe = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='saved_variants',
        verbose_name='Оригинальный рецепт'
    )

    # Сохраненные замены (JSON)
    saved_replacements = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Сохраненные замены',
        help_text='Формат: {"ингредиент_id": {"ingredient_id": 45, "product_id": null, "quantity": 450, "unit": "г"}}'
    )

    # Для будущей привязки к пользователю
    saved_by_session = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name='Ключ сессии сохранившего'
    )

    saved_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='saved_recipes',
        verbose_name='Сохранил пользователь'
    )

    saved_at = models.DateTimeField(
        null=True,
        blank=True,
        auto_now_add=True,
        verbose_name='Дата сохранения'
    )

    # ===== УСЛОВИЯ И СРОКИ ХРАНЕНИЯ =====
    storage_conditions = models.TextField(
        blank=True,
        verbose_name="Условия и сроки хранения",
        help_text="Температура, влажность, срок годности готового блюда"
    )

    is_favorite = models.BooleanField(default=False, verbose_name='В избранном')
    saved_notes = models.TextField(blank=True, verbose_name='Заметки')

    # Сохраненное КБЖУ (на момент сохранения)
    saved_calories = models.IntegerField(default=0)
    saved_protein = models.IntegerField(default=0)
    saved_fat = models.IntegerField(default=0)
    saved_carbs = models.IntegerField(default=0)

    def __str__(self):
        if self.is_saved_variant:
            return f"{self.title} (сохраненный вариант)"
        return self.title

    @property
    def is_ttk(self):
        """Является ли рецепт ТТК или полуфабрикатом"""
        return self.recipe_type in ['ttk', 'semi_finished']

    @property
    def is_home(self):
        """Является ли рецепт домашним"""
        return self.recipe_type == 'home'

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def calculate_total_time(self):
        return self.steps.aggregate(total=models.Sum('duration'))['total'] or 0

    def save(self, *args, **kwargs):
        # Если выбран ТТК или полуфабрикат, автоматически включаем профессиональный режим
        if self.recipe_type in ['ttk', 'semi_finished']:
            self.is_professional = True

        # Если выбран домашний рецепт, можно выключить профессиональный режим
        if self.recipe_type == 'home':
            # Не принудительно выключаем, чтобы сохранить совместимость
            # Но можно раскомментировать, если нужно:
            # self.is_professional = False
            pass

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# ======================= 9. ПРОДУКТЫ =======================
class Product(models.Model):
    code = models.CharField(max_length=100, unique=True, blank=True)
    name = models.CharField(max_length=300)
    brand = models.CharField(max_length=200, blank=True)
    quantity = models.CharField(max_length=100, blank=True)
    categories = models.TextField(blank=True)
    ingredients_text = models.TextField(blank=True)
    countries_tags = models.JSONField(default=list, blank=True)
    nutriscore_grade = models.CharField(max_length=1, blank=True)
    nova_group = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to=product_image_path, null=True, blank=True)
    data_source = models.CharField(max_length=50, default='Open Food Facts')
    last_update = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Готовый продукт"
        verbose_name_plural = "Готовые продукты"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.brand})" if self.brand else self.name


# ======================= 10. ДОМАШНИЙ ИНГРЕДИЕНТ =======================
class HomeIngredient(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name='home_ingredients')
    # ✅ ИСПРАВЛЕНО: Ingredient → AbstractIngredient
    ingredient = models.ForeignKey(
        'AbstractIngredient',
        on_delete=models.CASCADE,
        related_name='home_uses'
    )
    quantity = models.FloatField(validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='г')
    notes = models.CharField(max_length=500, blank=True)
    is_scalable = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Ингредиент домашнего рецепта'
        verbose_name_plural = 'Ингредиенты домашних рецептов'
        unique_together = ['recipe', 'ingredient']

    def __str__(self):
        return f"{self.ingredient.name}: {self.quantity} {self.unit}"


# ======================= 11. ПРОФЕССИОНАЛЬНЫЙ ИНГРЕДИЕНТ =======================
class ProfessionalIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='pro_ingredients')
    # ✅ ИСПРАВЛЕНО: Ingredient → AbstractIngredient
    ingredient = models.ForeignKey('AbstractIngredient', on_delete=models.PROTECT)
    gross_weight = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    net_weight = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='г')
    loss_factor = models.DecimalField(max_digits=5, decimal_places=3, blank=True, null=True)
    is_base_allowed = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.gross_weight and self.net_weight and self.gross_weight > 0:
            self.loss_factor = self.gross_weight / self.net_weight
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.ingredient.name}: {self.net_weight}/{self.gross_weight}{self.unit}'


# ======================= 12. СВЯЗЬ РЕЦЕПТА С ИНГРЕДИЕНТОМ/ПРОДУКТОМ =======================
class RecipeFoodItem(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='food_items')
    # ✅ ИСПРАВЛЕНО: Ingredient → AbstractIngredient
    ingredient = models.ForeignKey(
        'AbstractIngredient',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.FloatField(validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='г')
    notes = models.CharField(max_length=500, blank=True)
    is_scalable = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ингредиент/продукт в рецепте"
        verbose_name_plural = "Ингредиенты/продукты в рецептах"

    def clean(self):
        if not self.ingredient and not self.product:
            raise ValidationError("Укажите либо ингредиент, либо готовый продукт")
        if self.ingredient and self.product:
            raise ValidationError("Нельзя указать и ингредиент, и продукт одновременно")

    @property
    def food_item(self):
        return self.ingredient or self.product

    @property
    def food_name(self):
        item = self.food_item
        return item.name

    @property
    def food_type(self):
        return 'ingredient' if self.ingredient else 'product'

    def __str__(self):
        return f"{self.food_name}: {self.quantity} {self.unit}"


# ======================= 13. СЕМАНТИЧЕСКИЙ ТЕГ =======================
class SemanticTag(models.Model):
    """
    Семантический тег для ингредиентов с иерархией и группировкой.
    """

    # ===== ТИПЫ ТЕГОВ =====
    TAG_TYPES = [
        ('property', 'Свойство'),
        ('condition', 'Состояние'),
        ('form', 'Форма выпуска'),
        ('size', 'Размер/калибр'),
        ('color', 'Цвет'),
        ('processing', 'Способ обработки'),
        ('storage', 'Способ хранения'),
        ('cut', 'Нарезка'),
        ('origin', 'Происхождение/сорт'),
        ('purpose', 'Назначение'),
        ('style', 'Стиль/вид'),
        ('composition', 'Состав'),
        ('consistency', 'Консистенция'),
        ('type', 'Тип продукта'),
        ('technology', 'Технология'),
        ('fat_content', 'Жирность'),
        ('difficulty', 'Сложность'),
        ('specific', 'Конкретные названия'),
        ('season', 'Сезонность'),
        ('taste', 'Вкус'),
        ('nutrient', 'Нутриент'),
        ('diet', 'Диета'),
        ('allergen', 'Аллерген'),
        ('vitamin', 'Витамин'),
        ('mineral', 'Минерал'),
        ('method', 'Метод приготовления'),
        ('other', 'Другое'),
    ]

    # ===== ОСНОВНЫЕ ПОЛЯ =====
    name = models.CharField(max_length=100, unique=True, db_index=True, verbose_name="Название тега")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Слаг")
    tag_type = models.CharField(max_length=20, choices=TAG_TYPES, default='property', db_index=True, verbose_name="Тип тега")

    # ===== ИЕРАРХИЯ =====
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительский тег"
    )

    # ===== ГРУППИРОВКА =====
    group = models.CharField(max_length=100, blank=True, db_index=True, verbose_name="Группа тегов")

    # ===== ВИЗУАЛЬНЫЕ ПОЛЯ =====
    icon = models.CharField(max_length=50, blank=True, verbose_name="Иконка")
    color = models.CharField(max_length=20, blank=True, verbose_name="Цвет")
    background_color = models.CharField(max_length=20, blank=True, verbose_name="Цвет фона")

    # ===== ОПИСАНИЕ =====
    description = models.TextField(blank=True, verbose_name="Описание")
    short_description = models.CharField(max_length=200, blank=True, verbose_name="Краткое описание")

    # ===== СЛУЖЕБНЫЕ ПОЛЯ =====
    sort_order = models.IntegerField(default=0, db_index=True, verbose_name="Порядок сортировки")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Активен")
    is_public = models.BooleanField(default=True, verbose_name="Публичный")

    # ===== ВРЕМЕННЫЕ =====
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tags',
        verbose_name="Создал"
    )

    class Meta:
        verbose_name = "Семантический тег"
        verbose_name_plural = "Семантические теги"
        ordering = ['tag_type', 'group', 'sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['tag_type']),
            models.Index(fields=['group']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
            models.Index(fields=['name']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['name', 'parent'], name='unique_tag_name_per_parent'),
        ]

    def __str__(self):
        if self.group:
            return f"{self.group}: {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        # Генерируем slug если его нет
        if not self.slug:
            from slugify import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    # ===== СВОЙСТВА =====

    @property
    def ingredient_count(self):
        """Количество ингредиентов с этим тегом"""
        return self.abstract_ingredients.count()

    @property
    def full_hierarchy(self):
        """Полная иерархия тега в виде строки"""
        if self.parent:
            return f"{self.parent.full_hierarchy} → {self.name}"
        return self.name

    @property
    def level(self):
        """Уровень вложенности тега (0 - корневой)"""
        level = 0
        current = self
        while current.parent:
            level += 1
            current = current.parent
        return level

    @property
    def display_name_with_icon(self):
        """Имя с иконкой для отображения"""
        if self.icon:
            return f"{self.icon} {self.name}"
        return self.name

    @property
    def color_style(self):
        """CSS стиль для отображения тега"""
        style = ""
        if self.color:
            style += f"color: {self.color};"
        if self.background_color:
            style += f"background-color: {self.background_color};"
        return style

    @property
    def tag_type_display(self):
        """Человекочитаемое название типа тега"""
        return dict(self.TAG_TYPES).get(self.tag_type, self.tag_type)

    @property
    def ancestors(self):
        """Список всех предков (от корня до родителя)"""
        ancestors_list = []
        current = self.parent
        while current:
            ancestors_list.append(current)
            current = current.parent
        return list(reversed(ancestors_list))

    @property
    def children_count(self):
        """Количество дочерних тегов"""
        return self.children.filter(is_active=True).count()

    @property
    def is_root(self):
        """Является ли тег корневым"""
        return self.parent is None

    @property
    def is_leaf(self):
        """Является ли тег листовым (нет дочерних)"""
        return self.children.filter(is_active=True).count() == 0

    # ===== МЕТОДЫ =====

    def get_children(self):
        """Получить все дочерние активные теги"""
        return self.children.filter(is_active=True)

    def get_all_children(self):
        """Получить все дочерние теги (включая неактивные)"""
        return self.children.all()

    def get_descendants(self, include_self=False):
        """Получить всех потомков (рекурсивно)"""
        descendants = []
        if include_self:
            descendants.append(self)
        for child in self.get_children():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_all_descendants(self, include_self=False):
        """Получить всех потомков (включая неактивные)"""
        descendants = []
        if include_self:
            descendants.append(self)
        for child in self.get_all_children():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def is_descendant_of(self, tag):
        """Проверить, является ли текущий тег потомком указанного"""
        current = self.parent
        while current:
            if current == tag:
                return True
            current = current.parent
        return False

    def is_ancestor_of(self, tag):
        """Проверить, является ли текущий тег предком указанного"""
        return tag.is_descendant_of(self)

    def get_siblings(self, include_self=False):
        """Получить все теги на том же уровне"""
        if self.parent:
            siblings = self.parent.children.filter(is_active=True)
        else:
            siblings = SemanticTag.objects.filter(parent__isnull=True, is_active=True)

        if not include_self:
            siblings = siblings.exclude(pk=self.pk)
        return siblings

    def get_all_ingredients(self):
        """Получить все ингредиенты, включая из дочерних тегов"""
        ingredient_ids = set(self.abstract_ingredients.values_list('id', flat=True))
        for child in self.get_children():
            ingredient_ids.update(child.get_all_ingredients())
        return AbstractIngredient.objects.filter(id__in=ingredient_ids)

    def get_tree_display(self, prefix=""):
        """Получить строковое представление дерева тегов"""
        lines = []
        if prefix:
            lines.append(f"{prefix}{self.name}")
        else:
            lines.append(self.name)

        children = self.get_children()
        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)
            child_prefix = prefix + ("    " if is_last else "│   ")
            child_lines = child.get_tree_display(child_prefix + ("└── " if is_last else "├── "))
            lines.extend(child_lines)

        return lines

    def __repr__(self):
        return f"<SemanticTag: {self.name}>"


# ======================= 14. СЕМАНТИЧЕСКАЯ СВЯЗЬ =======================
class RelationType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="Слаг")
    reverse_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Обратное название",
        help_text="Например: 'сделано из' → 'используется в'"
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    is_symmetric = models.BooleanField(
        default=False,
        verbose_name="Симметричная связь",
        help_text="Например: 'похоже на' — симметричная связь"
    )
    icon = models.CharField(max_length=50, blank=True, verbose_name="Иконка")
    color = models.CharField(max_length=20, blank=True, verbose_name="Цвет")
    order = models.IntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Тип связи"
        verbose_name_plural = "Типы связей"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


# ======================= 15. ШАГИ ПРИГОТОВЛЕНИЯ =======================
class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps')
    order = models.IntegerField()
    title = models.CharField(max_length=200)
    instruction = models.TextField()
    duration = models.IntegerField(default=0)
    temperature = models.IntegerField(null=True, blank=True)
    recipe_step_image = models.ImageField(upload_to=recipe_step_image_path, null=True, blank=True)
    subrecipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_in_steps')
    subrecipe_base_ingredient = models.ForeignKey(HomeIngredient, on_delete=models.SET_NULL, null=True, blank=True, related_name='base_for_steps')
    subrecipe_base_quantity = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    cooking_method = models.ForeignKey(CookingMethod, on_delete=models.SET_NULL, null=True, blank=True, related_name='steps')
    ingredient_preparation = models.ForeignKey(IngredientPreparation, on_delete=models.SET_NULL, null=True, blank=True, related_name='steps')
    recommended_utensils = models.ManyToManyField(RecommendedUtensil, blank=True, related_name='steps')

    class Meta:
        ordering = ['order']
        constraints = [models.UniqueConstraint(fields=['recipe', 'order'], name='unique_recipe_step_order')]

    def __str__(self):
        return f"{self.order}. {self.title}"

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = RecipeStep.objects.get(pk=self.pk)
                if old_instance.recipe_step_image and old_instance.recipe_step_image != self.recipe_step_image:
                    if os.path.isfile(old_instance.recipe_step_image.path):
                        os.remove(old_instance.recipe_step_image.path)
            except RecipeStep.DoesNotExist:
                pass
        super().save(*args, **kwargs)


@receiver(post_delete, sender=RecipeStep)
def delete_recipe_step_image(sender, instance, **kwargs):
    if instance.recipe_step_image:
        if os.path.isfile(instance.recipe_step_image.path):
            os.remove(instance.recipe_step_image.path)


# ======================= 16. ЗАМЕНЫ =======================
class IngredientSubstitution(models.Model):
    recipe_ingredient = models.ForeignKey(HomeIngredient, on_delete=models.CASCADE, related_name='substitutions')
    # ✅ ИСПРАВЛЕНО: Ingredient → AbstractIngredient
    substitute_ingredient = models.ForeignKey(
        'AbstractIngredient',
        on_delete=models.CASCADE,
        related_name='substitutions'
    )
    substitute_unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    ratio = models.FloatField(default=1.0)
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = ['recipe_ingredient', 'substitute_ingredient']

    def __str__(self):
        return f"{self.recipe_ingredient.ingredient.name} → {self.substitute_ingredient.name}"


class CookingMethodSubstitution(models.Model):
    original_method = models.ForeignKey(CookingMethod, on_delete=models.CASCADE, related_name='substitutions')
    substitute_method = models.ForeignKey(CookingMethod, on_delete=models.CASCADE, related_name='original_for')
    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['original_method', 'substitute_method']

    def __str__(self):
        return f"{self.original_method.name} → {self.substitute_method.name}"


class UtensilSubstitution(models.Model):
    original_utensil = models.ForeignKey(RecommendedUtensil, on_delete=models.CASCADE, related_name='substitutions')
    substitute_utensil = models.ForeignKey(RecommendedUtensil, on_delete=models.CASCADE, related_name='original_for')
    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['original_utensil', 'substitute_utensil']

    def __str__(self):
        return f"{self.original_utensil.name} → {self.substitute_utensil.name}"


# ======================= 17. СЕМАНТИЧЕСКИЕ СВЯЗИ =======================
class SemanticRelation(models.Model):
    # ===== ОТ КОГО =====
    from_category = models.ForeignKey(
        'IngredientCategory',
        on_delete=models.CASCADE,
        related_name='outgoing_relations',
        verbose_name="От категории",
        null=True,
        blank=True
    )
    from_tag = models.ForeignKey(
        'SemanticTag',
        on_delete=models.CASCADE,
        related_name='outgoing_relations',
        verbose_name="От тега",
        null=True,
        blank=True
    )
    from_method = models.ForeignKey(
        'CookingMethod',
        on_delete=models.CASCADE,
        related_name='outgoing_relations',
        verbose_name="От метода",
        null=True,
        blank=True
    )
    from_utensil = models.ForeignKey(
        'RecommendedUtensil',
        on_delete=models.CASCADE,
        related_name='outgoing_relations',
        verbose_name="От утвари",
        null=True,
        blank=True
    )
    from_cuisine = models.ForeignKey(
        'Cuisine',
        on_delete=models.CASCADE,
        related_name='outgoing_relations',
        verbose_name="От кухни",
        null=True,
        blank=True
    )
    # ✅ НОВОЕ: от ингредиента
    from_ingredient = models.ForeignKey(
        'AbstractIngredient',
        on_delete=models.CASCADE,
        related_name='outgoing_relations',
        verbose_name="От ингредиента",
        null=True,
        blank=True
    )
    to_category = models.ForeignKey(
        'IngredientCategory',
        on_delete=models.CASCADE,
        related_name='incoming_relations',
        verbose_name="К категории",
        null=True,
        blank=True
    )
    to_tag = models.ForeignKey(
        'SemanticTag',
        on_delete=models.CASCADE,
        related_name='incoming_relations',
        verbose_name="К тегу",
        null=True,
        blank=True
    )
    to_method = models.ForeignKey(
        'CookingMethod',
        on_delete=models.CASCADE,
        related_name='incoming_relations',
        verbose_name="К методу",
        null=True,
        blank=True
    )
    to_utensil = models.ForeignKey(
        'RecommendedUtensil',
        on_delete=models.CASCADE,
        related_name='incoming_relations',
        verbose_name="К утвари",
        null=True,
        blank=True
    )
    to_cuisine = models.ForeignKey(
        'Cuisine',
        on_delete=models.CASCADE,
        related_name='incoming_relations',
        verbose_name="К кухне",
        null=True,
        blank=True
    )
    to_ingredient = models.ForeignKey(
        'AbstractIngredient',
        on_delete=models.CASCADE,
        related_name='incoming_relations',
        verbose_name="К ингредиенту",
        null=True,
        blank=True
    )

    # ===== ТИП СВЯЗИ =====
    relation_type = models.ForeignKey(
        'RelationType',
        on_delete=models.CASCADE,
        verbose_name="Тип связи"
    )
    notes = models.TextField(blank=True, verbose_name="Примечания")


@receiver(pre_save, sender=Recipe)
def update_recipe_nutrition(sender, instance, **kwargs):
    if instance.pk:
        pass

#=============== 18. ЗАМЕНА ИНГРЕДИЕНТА =================================
class IngredientSubstitutionRule(models.Model):
    """Универсальное правило замены ингредиента"""

    # ===== ИСХОДНЫЙ ИНГРЕДИЕНТ (что заменяем) =====
    original_ingredient = models.ForeignKey(
        'AbstractIngredient',
        on_delete=models.CASCADE,
        related_name='substitution_rules',
        verbose_name='Исходный ингредиент'
    )

    # ===== ВАРИАНТЫ ЗАМЕНЫ (ручной выбор) =====
    # Можно выбрать ЛИБО абстрактный ингредиент, ЛИБО брендированный продукт
    substitute_ingredient = models.ForeignKey(
        'AbstractIngredient',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Заменяющий ингредиент (абстрактный)'
    )

    substitute_branded = models.ForeignKey(
        'BrandedIngredient',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Заменяющий продукт (брендированный)'
    )

    # ===== АВТОМАТИЧЕСКИЙ ПОДБОР ПО ТЕГАМ =====
    # Если не выбран конкретный ингредиент, ищем по тегам
    required_tags = models.ManyToManyField(
        'SemanticTag',
        blank=True,
        related_name='substitution_requirements',
        verbose_name='Обязательные теги'
    )

    optional_tags = models.ManyToManyField(
        'SemanticTag',
        blank=True,
        related_name='substitution_optional',
        verbose_name='Желательные теги'
    )

    forbidden_tags = models.ManyToManyField(
        'SemanticTag',
        blank=True,
        related_name='substitution_forbidden',
        verbose_name='Запрещённые теги'
    )

    # ===== ПАРАМЕТРЫ ЗАМЕНЫ =====
    ratio = models.FloatField(
        default=1.0,
        verbose_name='Коэффициент',
        help_text='1 ст.л. пасты = 2 ст.л. томатов → ratio=2'
    )

    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default='г',
        verbose_name='Единица измерения замены'
    )

    # ===== ТИП ЗАМЕНЫ =====
    SUBSTITUTION_TYPES = [
        ('exact', 'Точная замена (конкретный ингредиент)'),
        ('branded', 'Брендированный продукт'),
        ('tag_based', 'По тегам (автоматический подбор)'),
        ('hybrid', 'Гибридный (ручной + теги)'),
    ]

    substitution_type = models.CharField(
        max_length=20,
        choices=SUBSTITUTION_TYPES,
        default='exact',
        verbose_name='Тип замены'
    )

    # ===== ПРИОРИТЕТ =====
    priority = models.IntegerField(
        default=0,
        verbose_name='Приоритет',
        help_text='Чем выше число, тем предпочтительнее замена'
    )

    # ===== ДОПОЛНИТЕЛЬНО =====
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
        help_text='Почему эта замена подходит, особенности использования'
    )

    is_active = models.BooleanField(default=True, verbose_name='Активна')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал'
    )

    class Meta:
        verbose_name = 'Правило замены'
        verbose_name_plural = 'Правила замен'
        ordering = ['-priority', 'original_ingredient__name']

    def __str__(self):
        target = self.substitute_ingredient or self.substitute_branded
        if target:
            return f"{self.original_ingredient.name} → {target}"
        else:
            tags = self.required_tags.all()
            if tags:
                tag_names = ', '.join([t.name for t in tags[:3]])
                return f"{self.original_ingredient.name} → (по тегам: {tag_names}...)"
            return f"{self.original_ingredient.name} → (автоподбор)"

    def get_target_display(self):
        """Возвращает отображаемое имя замены"""
        if self.substitute_ingredient:
            return self.substitute_ingredient.name
        elif self.substitute_branded:
            return f"{self.substitute_branded.brand} {self.substitute_branded.product_name}"
        else:
            return "Автоподбор по тегам"