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
        # python-slugify автоматически транслитерирует кириллицу
        base_slug = slugify(self.name)  # "тестовая кухня" → "testovaya-kukhnya"
        print(f'base_slug = {base_slug}')
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
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
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
        """Возвращает уровень вложенности (0, 1, 2)"""
        if self.parent is None:
            return 0
        elif self.parent.parent is None:
            return 1
        else:
            return 2

    @property
    def root_parent(self):
        """
        Возвращает корневую категорию (1-й уровень)
        Для level 0: возвращает None
        Для level 1: возвращает саму себя (т.к. это уже категория 1-го уровня)
        Для level 2: возвращает родителя родителя (категорию 1-го уровня)
        """
        if self.level == 0:
            return None
        elif self.level == 1:
            return self
        else:  # level == 2
            # Идём вверх до корня
            current = self
            while current.parent and current.parent.parent:
                current = current.parent
            return current.parent if current.parent else current

    @property
    def second_level_parent(self):
        """
        Возвращает родительскую категорию 2-го уровня (для категорий 3-го уровня)
        Для level 0: возвращает None
        Для level 1: возвращает None (т.к. это не 2-й уровень)
        Для level 2: возвращает родителя (категорию 2-го уровня)
        """
        if self.level == 2:
            return self.parent
        return None

    @property
    def full_hierarchy(self):
        """Возвращает полную иерархию в виде строки"""
        if self.level == 0:
            return self.name
        elif self.level == 1:
            return f"{self.parent.name} → {self.name}"
        elif self.level == 2:
            return f"{self.root_parent.name} → {self.second_level_parent.name} → {self.name}"
        return self.name

# ======================== ?? АБСТРАКТНЫЙ ИНГРЕДИЕНТ ========================
class AbstractIngredient(models.Model):
    """
    Абстрактный ингредиент — данные из pbprog.ru
    Базовый "сферический конь в вакууме"
    """
    # ===== ОСНОВНЫЕ ПОЛЯ =====
    name = models.CharField(max_length=300, db_index=True, verbose_name="Название")
    name_normalized = models.CharField(max_length=300, blank=True, db_index=True,
                                       verbose_name="Нормализованное название")
    description = models.TextField(blank=True, verbose_name="Описание")
    description_ru = models.TextField(blank=True, verbose_name="Описание RU")

    #===== КАТЕГОРИЯ =====
    category = models.ForeignKey(
        'IngredientCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория"
    )

    # ===== КБЖУ ИЗ PBPROG.RU =====
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

    # ===== ДРУГИЕ ПОЛЯ =====
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
            models.Index(fields=['category']),  # <-- ИСПРАВЛЕНО: было 'abstract__category'
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
        """Имя для отображения в интерфейсе"""
        return self.name

    @property
    def has_complete_nutrients(self):
        """Проверяет наличие полного КБЖУ"""
        return all([
            self.calories is not None,
            self.protein is not None,
            self.fat is not None,
            self.carbohydrates is not None,
        ])

# ========================= ?? БРЕНДИРОВАННЫЙ ИНГРЕДИЕНТ =========================
class BrandedIngredient(models.Model):
    """
    Конкретный продукт из магазина с ценой и КБЖУ
    """
    # ===== СВЯЗЬ С АБСТРАКТНЫМ =====
    abstract = models.ForeignKey(
        AbstractIngredient,
        on_delete=models.CASCADE,
        related_name='branded_versions',
        verbose_name="Абстрактный ингредиент"
    )

    # ===== ДАННЫЕ С УПАКОВКИ =====
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

    # ===== КБЖУ (МОЖЕТ ОТЛИЧАТЬСЯ ОТ АБСТРАКТНОГО) =====
    calories = models.FloatField(null=True, blank=True, verbose_name="Калории, ккал")
    protein = models.FloatField(null=True, blank=True, verbose_name="Белки, г")
    fat = models.FloatField(null=True, blank=True, verbose_name="Жиры, г")
    carbohydrates = models.FloatField(null=True, blank=True, verbose_name="Углеводы, г")

    # ===== ЦЕНА =====
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

    # ===== МЕСТО ПОКУПКИ =====
    store = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="Магазин"
    )
    store_url = models.URLField(blank=True, verbose_name="Ссылка на товар")

    # ===== ДОПОЛНИТЕЛЬНО =====
    is_available = models.BooleanField(default=True, verbose_name="В наличии")
    last_checked = models.DateTimeField(null=True, blank=True, verbose_name="Последняя проверка")

    # ===== СЛУЖЕБНЫЕ =====
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
        unique_together = ['brand', 'product_name']  # Не даем создать дубликаты
        indexes = [
            models.Index(fields=['brand']),
            models.Index(fields=['barcode']),
            models.Index(fields=['store']),
        ]

    def __str__(self):
        return f"{self.brand} {self.product_name}"

    @property
    def full_name(self):
        """Полное имя для отображения"""
        return f"{self.brand} {self.product_name}"

    @property
    def price_per_100g(self):
        """Цена за 100 грамм"""
        if self.price and self.weight and self.weight > 0:
            return round((float(self.price) / float(self.weight)) * 100, 2)
        return None

    @property
    def price_per_kg(self):
        """Цена за 1 кг"""
        if self.price_per_100g:
            return round(self.price_per_100g * 10, 2)
        return None

    def get_nutrients(self):
        """
        Возвращает КБЖУ с приоритетом:
        1. Собственные данные (если есть)
        2. Данные абстрактного ингредиента
        """
        return {
            'calories': self.calories or self.abstract.calories,
            'protein': self.protein or self.abstract.protein,
            'fat': self.fat or self.abstract.fat,
            'carbohydrates': self.carbohydrates or self.abstract.carbohydrates,
        }

    def compare_with_abstract(self):
        """Сравнение с абстрактным ингредиентом"""
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


# ======================= 3. ИНГРЕДИЕНТЫ =======================
class Ingredient(models.Model):
    fdc_id = models.IntegerField(unique=True, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=300, db_index=True)
    name_normalized = models.CharField(max_length=300, blank=True, null=True, db_index=True)
    description = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    data_source = models.CharField(max_length=500, default='USDA Foundation', blank=True)

    # Пищевая ценность
    calories = models.FloatField(null=True, blank=True)
    protein = models.FloatField(null=True, blank=True)
    fat = models.FloatField(null=True, blank=True)
    carbohydrates = models.FloatField(null=True, blank=True)
    fiber = models.FloatField(null=True, blank=True)
    sugar = models.FloatField(null=True, blank=True)
    saturated_fat = models.FloatField(null=True, blank=True)
    trans_fat = models.FloatField(null=True, blank=True)
    cholesterol = models.FloatField(null=True, blank=True)
    omega_3 = models.FloatField(null=True, blank=True, verbose_name='Омега-3 жирные кислоты')
    omega_6 = models.FloatField(null=True, blank=True, verbose_name='Омега-6 жирные кислоты')

    # Витамины
    vitamin_a = models.FloatField(null=True, blank=True)
    vitamin_b1 = models.FloatField(null=True, blank=True)
    vitamin_b2 = models.FloatField(null=True, blank=True)
    vitamin_b6 = models.FloatField(null=True, blank=True)
    vitamin_b9 = models.FloatField(null=True, blank=True)
    vitamin_b12 = models.FloatField(null=True, blank=True)
    vitamin_c = models.FloatField(null=True, blank=True)
    vitamin_d = models.FloatField(null=True, blank=True)
    vitamin_e = models.FloatField(null=True, blank=True)
    vitamin_k = models.FloatField(null=True, blank=True)
    vitamin_b4 = models.FloatField(null=True, blank=True, verbose_name='Витамин B4 (холин)')
    vitamin_b5 = models.FloatField(null=True, blank=True, verbose_name='Витамин B5 (пантотеновая кислота)')
    vitamin_b7 = models.FloatField(null=True, blank=True, verbose_name='Витамин B7 (биотин)')
    vitamin_b3 = models.FloatField(null=True, blank=True, verbose_name='Витамин B3 (ниацин)')
    vitamin_b9_folate = models.FloatField(null=True, blank=True, verbose_name='Фолаты (витамин B9)')
    beta_carotene = models.FloatField(null=True, blank=True, verbose_name='Бета-каротин')

    # Минералы
    calcium = models.FloatField(null=True, blank=True)
    iron = models.FloatField(null=True, blank=True)
    magnesium = models.FloatField(null=True, blank=True)
    phosphorus = models.FloatField(null=True, blank=True)
    potassium = models.FloatField(null=True, blank=True)
    sodium = models.FloatField(null=True, blank=True)
    zinc = models.FloatField(null=True, blank=True)
    copper = models.FloatField(null=True, blank=True)
    manganese = models.FloatField(null=True, blank=True)
    selenium = models.FloatField(null=True, blank=True)
    silicon = models.FloatField(null=True, blank=True, verbose_name='Кремний (Si)')
    sulfur = models.FloatField(null=True, blank=True, verbose_name='Сера (S)')
    chlorine = models.FloatField(null=True, blank=True, verbose_name='Хлор (Cl)')
    aluminum = models.FloatField(null=True, blank=True, verbose_name='Алюминий (Al)')
    boron = models.FloatField(null=True, blank=True, verbose_name='Бор (B)')
    vanadium = models.FloatField(null=True, blank=True, verbose_name='Ванадий (V)')
    iodine = models.FloatField(null=True, blank=True, verbose_name='Йод (I)')
    cobalt = models.FloatField(null=True, blank=True, verbose_name='Кобальт (Co)')
    lithium = models.FloatField(null=True, blank=True, verbose_name='Литий (Li)')
    molybdenum = models.FloatField(null=True, blank=True, verbose_name='Молибден (Mo)')
    nickel = models.FloatField(null=True, blank=True, verbose_name='Никель (Ni)')
    rubidium = models.FloatField(null=True, blank=True, verbose_name='Рубидий (Rb)')
    chromium = models.FloatField(null=True, blank=True, verbose_name='Хром (Cr)')
    fluorine = models.FloatField(null=True, blank=True, verbose_name='Фтор (F)')

    # Дополнительно
    water = models.FloatField(null=True, blank=True)
    ash = models.FloatField(null=True, blank=True)
    starch = models.FloatField(null=True, blank=True, verbose_name='Крахмал и декстрины')
    organic_acids = models.FloatField(null=True, blank=True, verbose_name='Органические кислоты')

    # Локальные поля
    image = models.ImageField(upload_to=ingredient_image_path, null=True, blank=True)
    is_common = models.BooleanField(default=False)

    # Служебные
    last_update = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ===== НОВЫЕ СВЯЗИ (ДОБАВЛЯЕМ) =====
    abstract = models.ForeignKey(
        AbstractIngredient,
        on_delete=models.PROTECT,
        related_name='instances',
        verbose_name="Абстрактный ингредиент",
        null=True,  # временно разрешаем null для переноса данных
        blank=True
    )
    branded = models.ForeignKey(
        BrandedIngredient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instances',
        verbose_name="Брендированный продукт"
    )

    # ===== ПОЛЬЗОВАТЕЛЬСКИЕ КОРРЕКТИРОВКИ =====
    custom_calories = models.FloatField(null=True, blank=True, verbose_name="Свои калории")
    custom_protein = models.FloatField(null=True, blank=True, verbose_name="Свои белки")
    custom_fat = models.FloatField(null=True, blank=True, verbose_name="Свои жиры")
    custom_carbohydrates = models.FloatField(null=True, blank=True, verbose_name="Свои углеводы")

    # ===== ДЛЯ ПОЛУФАБРИКАТОВ =====
    is_semi_finished = models.BooleanField(default=False, verbose_name="Полуфабрикат")
    semi_finished_recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produced_ingredients',
        verbose_name="Рецепт полуфабриката"
    )

    # ===== НОВЫЕ СВОЙСТВА =====

    @property
    def category(self):
        """Категория наследуется от abstract"""
        if self.abstract:
            return self.abstract.category
        return None

    @category.setter
    def category(self, value):
        """Устанавливает категорию в abstract"""
        if self.abstract:
            self.abstract.category = value
        elif value:
            # Если нет abstract, создаем его
            from .models import AbstractIngredient
            self.abstract = AbstractIngredient.objects.create(
                name=self.name,
                category=value,
                data_source=self.data_source or 'manual'
            )

    @property
    def calories(self):
        """КБЖУ с приоритетом: custom > branded > abstract"""
        if self.custom_calories is not None:
            return self.custom_calories
        if self.branded and self.branded.calories is not None:
            return self.branded.calories
        if self.abstract and self.abstract.calories is not None:
            return self.abstract.calories
        return None

    @property
    def protein(self):
        if self.custom_protein is not None:
            return self.custom_protein
        if self.branded and self.branded.protein is not None:
            return self.branded.protein
        if self.abstract and self.abstract.protein is not None:
            return self.abstract.protein
        return None

    @property
    def fat(self):
        if self.custom_fat is not None:
            return self.custom_fat
        if self.branded and self.branded.fat is not None:
            return self.branded.fat
        if self.abstract and self.abstract.fat is not None:
            return self.abstract.fat
        return None

    @property
    def carbohydrates(self):
        if self.custom_carbohydrates is not None:
            return self.custom_carbohydrates
        if self.branded and self.branded.carbohydrates is not None:
            return self.branded.carbohydrates
        if self.abstract and self.abstract.carbohydrates is not None:
            return self.abstract.carbohydrates
        return None

    @property
    def display_name(self):
        """Имя для отображения"""
        if self.branded:
            return self.branded.full_name
        if self.abstract:
            return self.abstract.name
        return self.name

    def get_nutrients_dict(self):
        """Возвращает словарь с КБЖУ"""
        return {
            'calories': self.calories,
            'protein': self.protein,
            'fat': self.fat,
            'carbohydrates': self.carbohydrates,
        }

    # ===== МЕТА =====
    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.name_normalized:
            self.name_normalized = self.name.replace(' ', '').lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        self.name_normalized = self.name.replace(' ', '').lower()
        super().save(*args, **kwargs)

    class Meta:
        ordering = [Lower('name_normalized')]

    def __str__(self):
        return self.name


# ======================= 4. ДИЕТЫ (ссылаются на Ingredient) =======================
class Diet(models.Model):
    name = models.CharField(max_length=100)
    authority = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    allowed_ingredients = models.ManyToManyField(Ingredient, blank=True, related_name='allowed_for_diets')
    prohibited_ingredients = models.ManyToManyField(Ingredient, blank=True, related_name='prohibited_for_diets')
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
    """Способы кулинарной обработки с научным обоснованием и практическими рекомендациями"""

    # Основные поля
    name = models.CharField(max_length=100, verbose_name='Название')
    code = models.CharField(max_length=50, unique=True, verbose_name='Код')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_heat_treatment = models.BooleanField(default=True, verbose_name='Тепловая обработка')
    sort_order = models.IntegerField(default=0, verbose_name='Порядок')

    # Советы и предупреждения
    tips = models.TextField(blank=True, verbose_name='Советы')
    common_mistakes = models.TextField(blank=True, verbose_name='Типичные ошибки')

    # Научная база
    scientific_background = models.TextField(blank=True, verbose_name='Научная база')
    advanced_notes = models.TextField(blank=True, verbose_name='Для продвинутых')

    # Коэффициенты впитываемости масла для разных продуктов
    oil_absorption_rates = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Коэффициенты впитываемости масла',
        help_text='Формат: {"продукт": 0.08, "продукт2": 0.12}'
    )

    # Рекомендуемая температура
    recommended_temperature_min = models.IntegerField(null=True, blank=True, verbose_name='Мин. температура, °C')
    recommended_temperature_max = models.IntegerField(null=True, blank=True, verbose_name='Макс. температура, °C')

    # Влияние формы нарезки на впитываемость
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

    breading_type = models.CharField(max_length=20, choices=BREADING_CHOICES, default='none',
                                     verbose_name='Тип панировки')

    class Meta:
        verbose_name = 'Способ обработки'
        verbose_name_plural = 'Способы обработки'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

# ------------------------ 5.1 Нормы потерь при кулинарной обработке -----------------------------------------
class ProductLossNorm(models.Model):
    """Нормы потерь при обработке продуктов"""

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

    # Потери при холодной (механической) обработке, %
    cold_loss_percent = models.DecimalField(max_digits=5, decimal_places=1, default=0,
                                            verbose_name='Потери при холодной обработке, %')

    # Потери при тепловой обработке, %
    heat_loss_percent = models.DecimalField(max_digits=5, decimal_places=1, default=0,
                                            verbose_name='Потери при тепловой обработке, %')

    # Примечание по сезону (для овощей)
    season_note = models.CharField(max_length=100, blank=True, verbose_name='Сезон/Примечание')

    # Источник данных
    source = models.CharField(max_length=100, default='Сборник рецептур', verbose_name='Источник')

    PROCESSING_BEHAVIOR = [
        ('loss', 'Потери (уменьшение веса)'),
        ('gain', 'Увеличение веса (впитывание воды)'),
    ]

    processing_behavior = models.CharField(
        max_length=10,
        choices=PROCESSING_BEHAVIOR,
        default='loss',
        verbose_name='Поведение при обработке'
    )

    # Для продуктов, увеличивающихся в весе - коэффициент увеличения
    # (например, 2.5 для риса: 100г риса = 250г готового)
    gain_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Коэффициент увеличения веса'
    )

    # Для продуктов с потерями - процент потерь
    # (поля cold_loss_percent и heat_loss_percent уже есть)

    class Meta:
        verbose_name = 'Норма потерь'
        verbose_name_plural = 'Нормы потерь'
        unique_together = ['product_name', 'processing_method', 'season_note']

    def __str__(self):
        return f'{self.product_name} → {self.processing_method.name}'

    @property
    def total_loss_percent(self):
        """Общий процент потерь (холодные + тепловые)"""
        return (self.cold_loss_percent or 0) + (self.heat_loss_percent or 0)

    @property
    def yield_coefficient(self):
        """Коэффициент выхода (1 - потери/100)"""
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


# ======================= 8. РЕЦЕПТЫ (ссылаются на многие модели) =======================
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

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def calculate_total_time(self):
        return self.steps.aggregate(total=models.Sum('duration'))['total'] or 0

    def save(self, *args, **kwargs):
        if self.pk:
            self.total_time = self.calculate_total_time()
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


# ======================= 10. ИНГРЕДИЕНТЫ РЕЦЕПТА =======================
class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='recipe_uses')
    quantity = models.FloatField(validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='г')
    notes = models.CharField(max_length=500, blank=True)
    is_scalable = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        unique_together = ['recipe', 'ingredient']

    def __str__(self):
        return f"{self.ingredient.name}: {self.quantity} {self.unit}"


# ======================= 11. ПРОФЕССИОНАЛЬНЫЙ ИНГРЕДИЕНТ =======================
class ProfessionalIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='pro_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
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
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, null=True, blank=True)
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


# ======================= 13. ШАГИ ПРИГОТОВЛЕНИЯ =======================
class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps')
    order = models.IntegerField()
    title = models.CharField(max_length=200)
    instruction = models.TextField()
    duration = models.IntegerField(default=0)
    temperature = models.IntegerField(null=True, blank=True)
    recipe_step_image = models.ImageField(upload_to=recipe_step_image_path, null=True, blank=True)
    subrecipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='used_in_steps')
    subrecipe_base_ingredient = models.ForeignKey(RecipeIngredient, on_delete=models.SET_NULL, null=True, blank=True,
                                                  related_name='base_for_steps')
    subrecipe_base_quantity = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    cooking_method = models.ForeignKey(CookingMethod, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='steps')
    ingredient_preparation = models.ForeignKey(IngredientPreparation, on_delete=models.SET_NULL, null=True, blank=True,
                                               related_name='steps')
    recommended_utensils = models.ManyToManyField(RecommendedUtensil, blank=True, related_name='steps')

    class Meta:
        ordering = ['order']
        constraints = [models.UniqueConstraint(fields=['recipe', 'order'], name='unique_recipe_step_order')]

    def __str__(self):
        return f"{self.order}. {self.title}"

    def save(self, *args, **kwargs):
        # Удаляем старое изображение при обновлении
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
    """Удаляет файл изображения при удалении шага рецепта"""
    if instance.recipe_step_image:
        if os.path.isfile(instance.recipe_step_image.path):
            os.remove(instance.recipe_step_image.path)


# ======================= 14. ЗАМЕНЫ =======================
class IngredientSubstitution(models.Model):
    recipe_ingredient = models.ForeignKey(RecipeIngredient, on_delete=models.CASCADE, related_name='substitutions')
    substitute_ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='substitutions')
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

@receiver(pre_save, sender=Recipe)
def update_recipe_nutrition(sender, instance, **kwargs):
    if instance.pk:
        # Пересчитать КБЖУ из ингредиентов
        pass