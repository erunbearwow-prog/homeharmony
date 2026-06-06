from django.db import models
from django.core.validators import MinValueValidator
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


# ======================= КУХНИ МИРА =======================
class Cuisine(models.Model):
    """Кухня мира"""
    name = models.CharField(max_length=100, verbose_name='Название')
    region = models.CharField(max_length=100, blank=True, verbose_name='Регион')
    description = models.TextField(blank=True, verbose_name='Описание')
    traditions = models.TextField(blank=True, verbose_name='Традиции')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Кухня мира'
        verbose_name_plural = 'Кухни мира'

    def __str__(self):
        return self.name


# ======================= ДИЕТЫ =======================
class Diet(models.Model):
    """Диета"""
    name = models.CharField(max_length=100, verbose_name='Название')
    authority = models.CharField(max_length=200, blank=True, verbose_name='Утвердивший орган')
    description = models.TextField(blank=True, verbose_name='Описание')
    allowed_ingredients = models.ManyToManyField('Ingredient', blank=True, related_name='allowed_for_diets')
    prohibited_ingredients = models.ManyToManyField('Ingredient', blank=True, related_name='prohibited_for_diets')
    allowed_methods = models.TextField(blank=True, verbose_name='Разрешённые методы приготовления')
    nutritional_guidelines = models.TextField(blank=True, verbose_name='Нормы КБЖУ')
    medical_indications = models.TextField(blank=True, verbose_name='Медицинские показания')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Диета'
        verbose_name_plural = 'Диеты'

    def __str__(self):
        return self.name


# ======================= КАТЕГОРИИ ИНГРЕДИЕНТОВ =======================
class IngredientCategory(models.Model):
    """Категория ингредиентов"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='subcategories', verbose_name='Родительская категория')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Иконка')
    sort_order = models.IntegerField(default=0, verbose_name='Порядок сортировки')

    class Meta:
        verbose_name = 'Категория ингредиентов'
        verbose_name_plural = 'Категории ингредиентов'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


# ======================= ИНГРЕДИЕНТЫ =======================
class Ingredient(models.Model):
    """Ингредиент"""
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

    name = models.CharField(max_length=200, unique=True, verbose_name='Название')
    category = models.ForeignKey(IngredientCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='ingredients', verbose_name='Категория')
    description = models.TextField(blank=True, verbose_name='Описание')
    default_unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='г', verbose_name='Единица измерения')

    # Пищевая ценность
    calories_per_100g = models.IntegerField(default=0, verbose_name='Калории (ккал на 100г)')
    protein_per_100g = models.FloatField(default=0, verbose_name='Белки (г на 100г)')
    fat_per_100g = models.FloatField(default=0, verbose_name='Жиры (г на 100г)')
    carbs_per_100g = models.FloatField(default=0, verbose_name='Углеводы (г на 100г)')

    # Сезонность
    season_start = models.IntegerField(null=True, blank=True, verbose_name='Начало сезона (месяц)')
    season_end = models.IntegerField(null=True, blank=True, verbose_name='Конец сезона (месяц)')

    # Хранение
    storage_conditions = models.TextField(blank=True, verbose_name='Условия хранения')
    shelf_life_days = models.IntegerField(default=7, verbose_name='Срок хранения (дни)')

    # Аллергены
    allergens = models.JSONField(default=list, blank=True, verbose_name='Аллергены')

    # Плотность
    density_data = models.JSONField(default=dict, blank=True, verbose_name='Плотность')

    # Диетические метки
    is_common = models.BooleanField(default=False, verbose_name='Часто используемый')
    is_vegetarian = models.BooleanField(default=True, verbose_name='Вегетарианский')
    is_vegan = models.BooleanField(default=True, verbose_name='Веганский')
    is_gluten_free = models.BooleanField(default=True, verbose_name='Без глютена')

    # Изображение
    image = models.ImageField(upload_to='ingredients/', null=True, blank=True, verbose_name='Изображение')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return self.name


# ======================= РЕЦЕПТЫ =======================
class Recipe(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Лёгкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]

    title = models.CharField(max_length=200, verbose_name='Название')
    cuisine = models.ForeignKey(Cuisine, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Кухня')
    author = models.CharField(max_length=100, blank=True, verbose_name='Автор')
    description = models.TextField(blank=True, verbose_name='Описание')

    total_time = models.IntegerField(default=0, verbose_name='Время приготовления (мин)')
    servings = models.IntegerField(default=4, verbose_name='Порций')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium', verbose_name='Сложность')

    # МЕТКА ПРОФЕССИОНАЛЬНОГО РЕЦЕПТА
    is_professional = models.BooleanField(default=False, verbose_name='Профессиональный')

    # Компоненты составного блюда (связь многие-ко-многим с самим собой)
    components = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='parent_recipes',
        verbose_name='Компоненты блюда'
    )

    # Изображения
    image = models.ImageField(upload_to='recipes/', null=True, blank=True, verbose_name='Изображение')
    video = models.URLField(blank=True, verbose_name='Видео')

    # Пищевая ценность блюда
    calories = models.IntegerField(default=0, verbose_name='Калории')
    protein = models.IntegerField(default=0, verbose_name='Белки')
    fat = models.IntegerField(default=0, verbose_name='Жиры')
    carbs = models.IntegerField(default=0, verbose_name='Углеводы')

    # Диеты
    diet_tags = models.ManyToManyField(Diet, blank=True, verbose_name='Диеты')
    related_recipes = models.ManyToManyField('self', blank=True, verbose_name='Связанные рецепты')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.title


# ======================= ПРОФЕССИОНАЛЬНЫЙ РЕЦЕПТ ===================
class ProfessionalIngredient(models.Model):
    """ Ингредиент в профессиональном рецепте с брутто и нетто """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='pro_ingredients',
        verbose_name='Рецепт',
    )

    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.PROTECT,
        verbose_name='Ингредиент',
    )

    gross_weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=False,  # ← добавить
        null=False,  # ← добавить
        validators=[MinValueValidator(0.01)],
        verbose_name='Брутто (вес с отходами)',
        help_text='Например, 150г неочищенного лука',
    )

    net_weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=False,  # ← добавить
        null=False,  # ← добавить
        validators=[MinValueValidator(0.01)],
        verbose_name='Нетто (чистый вес)',
        help_text='Например, 120г очищенного лука'
    )

    unit = models.CharField(
        max_length=10,
        choices=Ingredient.UNIT_CHOICES,
        default='г',
        verbose_name='Единица измерения'
    )

    # Коэффициент потерь (рассчитывается автоматически, потом переопределим)
    loss_factor = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name='Коэффициент потерь (брутто/нетто)',
        help_text='Обычно рассчитывается как gross/net. Для сезонных поправок можно указать вручную'
    )

    # Пересчет по продуктам
    is_base_allowed = models.BooleanField(
        default=True,
        verbose_name='Может быть базовым ингредиентом для пересчета'
    )

    class Meta:
        verbose_name='Ингредиент (профессиональный)'
        verbose_name_plural = 'Ингредиенты (профессиональные)'

    def save(self, *args, **kwargs):
        # автоматически рассчитываем коэффициент потерь
        if self.gross_weight and self.net_weight and self.gross_weight > 0:
            self.loss_factor = self.gross_weight / self.net_weight
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.ingredient.name}: {self.net_weight}/{self.gross_weight}{self.unit}'


# ======================= ИНГРЕДИЕНТЫ РЕЦЕПТА =======================
class RecipeIngredient(models.Model):
    """Связь рецепта и ингредиента"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='recipe_uses')
    quantity = models.FloatField(
        verbose_name='Количество',
        validators=[MinValueValidator(0.01)],  # ← добавить валидатор
    )
    unit = models.CharField(
        max_length=20,
        choices=Ingredient.UNIT_CHOICES,
        default='г',
        blank=False,  # ← добавить
    )
    notes = models.CharField(max_length=500, blank=True)
    is_scalable = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        unique_together = ['recipe', 'ingredient']

    def __str__(self):
        return f"{self.ingredient.name}: {self.quantity} {self.unit}"


# ======================= МЕТОДЫ ПРИГОТОВЛЕНИЯ =======================
class CookingMethod(models.Model):
    """Метод приготовления"""
    CATEGORY_CHOICES = [
        ('thermal', 'Тепловая обработка'),
        ('preparation', 'Подготовка продуктов'),
        ('shaping', 'Формование'),
        ('other', 'Прочее'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='thermal', verbose_name='Категория')
    short_description = models.CharField(max_length=200, verbose_name='Краткое описание')
    description = models.TextField(verbose_name='Подробное описание')
    scientific_background = models.TextField(blank=True, verbose_name='Научное обоснование')

    typical_temperature = models.CharField(max_length=50, blank=True, verbose_name='Типичная температура')
    typical_duration = models.CharField(max_length=50, blank=True, verbose_name='Типичная длительность')

    tips = models.TextField(blank=True, verbose_name='Советы')
    common_mistakes = models.TextField(blank=True, verbose_name='Типичные ошибки')
    advanced_notes = models.TextField(blank=True, verbose_name='Для опытных')

    icon = models.CharField(max_length=50, default='fa-fire', verbose_name='Иконка')
    color = models.CharField(max_length=20, default='amber', verbose_name='Цвет')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Метод приготовления'
        verbose_name_plural = 'Методы приготовления'

    def __str__(self):
        return self.name


# ======================= ПОДГОТОВКА ПРОДУКТОВ =======================
class IngredientPreparation(models.Model):
    """Способ подготовки продуктов (нарезка, замачивание)"""
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='preparations/', null=True, blank=True, verbose_name='Изображение')
    video_url = models.URLField(blank=True, verbose_name='Видео')
    time_factor = models.FloatField(default=1.0, verbose_name='Коэффициент времени')
    waste_percentage = models.FloatField(default=0, verbose_name='Процент отходов')
    tips = models.TextField(blank=True, verbose_name='Советы')

    class Meta:
        verbose_name = 'Подготовка продукта'
        verbose_name_plural = 'Подготовка продуктов'

    def __str__(self):
        return self.name


# ======================= РЕКОМЕНДОВАННАЯ УТВАРЬ =======================
class RecommendedUtensil(models.Model):
    """Рекомендованная утварь"""
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='utensils/', null=True, blank=True, verbose_name='Изображение')
    alternative = models.CharField(max_length=200, blank=True, verbose_name='Чем заменить')
    care_instructions = models.TextField(blank=True, verbose_name='Уход')

    class Meta:
        verbose_name = 'Утварь'
        verbose_name_plural = 'Утварь'

    def __str__(self):
        return self.name


# ======================= ДОПУСТИМАЯ ЗАМЕНА ИНГРЕДИЕНТА =======================
class IngredientSubstitution(models.Model):
    """Допустимая замена для ингредиента в конкретном рецепте"""
    recipe_ingredient = models.ForeignKey(
        'RecipeIngredient',
        on_delete=models.CASCADE,
        related_name='substitutions',
        verbose_name='Исходный ингредиент в рецепте'
    )
    substitute_ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,  # ← меняем с SET_NULL на CASCADE
        related_name='substitutions',
        verbose_name='Ингредиент-заменитель'
    )
    substitute_unit = models.CharField(
        max_length=20,
        choices=Ingredient.UNIT_CHOICES,
        verbose_name='Единица измерения заменителя'
    )
    ratio = models.FloatField(
        default=1.0,
        verbose_name='Коэффициент пересчёта',
        help_text='Например: 1 ст.л. пасты = 2 ст.л. помидоров'
    )
    notes = models.CharField(max_length=500, blank=True, verbose_name='Примечания по замене')

    class Meta:
        verbose_name = 'Допустимая замена'
        verbose_name_plural = 'Допустимые замены'
        unique_together = ['recipe_ingredient', 'substitute_ingredient']  # ← защита от дублей

    def __str__(self):
        return f"{self.recipe_ingredient.ingredient.name} → {self.substitute_ingredient.name}"


# ======================= ЗАМЕНА МЕТОДА ПРИГОТОВЛЕНИЯ =======================
class CookingMethodSubstitution(models.Model):
    """Замена метода приготовления (например, для диет)"""
    original_method = models.ForeignKey(
        CookingMethod,
        on_delete=models.CASCADE,
        related_name='substitutions',
        verbose_name='Исходный метод'
    )
    substitute_method = models.ForeignKey(
        CookingMethod,
        on_delete=models.CASCADE,
        related_name='original_for',
        verbose_name='Метод-заменитель'
    )
    reason = models.CharField(max_length=200, blank=True, verbose_name='Причина замены')
    notes = models.TextField(blank=True, verbose_name='Примечания')

    class Meta:
        verbose_name = 'Замена метода приготовления'
        verbose_name_plural = 'Замены методов приготовления'
        unique_together = ['original_method', 'substitute_method']

    def __str__(self):
        return f"{self.original_method.name} → {self.substitute_method.name}"


# ======================= ЗАМЕНА УТВАРИ =======================
class UtensilSubstitution(models.Model):
    """Замена утвари"""
    original_utensil = models.ForeignKey(
        RecommendedUtensil,
        on_delete=models.CASCADE,
        related_name='substitutions',
        verbose_name='Исходная утварь'
    )
    substitute_utensil = models.ForeignKey(
        RecommendedUtensil,
        on_delete=models.CASCADE,
        related_name='original_for',
        verbose_name='Утварь-заменитель'
    )
    reason = models.CharField(max_length=200, blank=True, verbose_name='Причина замены')
    notes = models.TextField(blank=True, verbose_name='Примечания')

    class Meta:
        verbose_name = 'Замена утвари'
        verbose_name_plural = 'Замены утвари'
        unique_together = ['original_utensil', 'substitute_utensil']

    def __str__(self):
        return f"{self.original_utensil.name} → {self.substitute_utensil.name}"


# ======================= ШАГИ ПРИГОТОВЛЕНИЯ =======================
class RecipeStep(models.Model):
    """Шаг приготовления"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps')
    order = models.IntegerField(verbose_name='Порядок')
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    instruction = models.TextField(verbose_name='Инструкция')
    duration = models.IntegerField(default=0, verbose_name='Длительность (мин)')
    temperature = models.IntegerField(null=True, blank=True, verbose_name='Температура')

    # Вложенный рецепт
    subrecipe = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_in_steps',
        verbose_name='Вложенный рецепт'
    )

    # Базовый ингредиент из вложенного рецепта
    subrecipe_base_ingredient = models.ForeignKey(
        'RecipeIngredient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='base_for_steps',
        verbose_name='Базовый ингредиент из вложенного рецепта'
    )
    subrecipe_base_quantity = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Количество базового ингредиента'
    )

    # Метод приготовления для этого шага
    cooking_method = models.ForeignKey(
        CookingMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='steps',
        verbose_name='Метод приготовления'
    )

    # Подготовка продуктов для этого шага
    ingredient_preparation = models.ForeignKey(
        IngredientPreparation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='steps',
        verbose_name='Подготовка продуктов'
    )

    # Рекомендованная утварь для этого шага
    recommended_utensils = models.ManyToManyField(
        RecommendedUtensil,
        blank=True,
        related_name='steps',
        verbose_name='Рекомендованная утварь'
    )

    class Meta:
        verbose_name = 'Шаг приготовления'
        verbose_name_plural = 'Шаги приготовления'
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'order'], name='unique_recipe_step_order')
        ]

    def __str__(self):
        return f"{self.order}. {self.title}"