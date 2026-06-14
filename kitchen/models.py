from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator
from slugify import slugify
from django.urls import reverse
from django.db.models.functions import Lower
import os
from django.db.models.signals import post_delete
from django.dispatch import receiver

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
        ordering = ['sort_order', 'name']

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
        """Возвращает корневую категорию (1 уровень)"""
        if self.level == 0:
            return None
        elif self.level == 1:
            return self
        else:  # level == 2
            return self.parent

    @property
    def second_level_parent(self):
        """Возвращает родителя 2 уровня"""
        if self.level == 2:
            return self.parent
        return None


# ======================= 3. ИНГРЕДИЕНТЫ =======================
class Ingredient(models.Model):
    fdc_id = models.IntegerField(unique=True, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=300, db_index=True)
    name_normalized = models.CharField(max_length=300, blank=True, null=True, db_index=True)
    description = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    data_source = models.CharField(max_length=50, default='USDA Foundation', blank=True)

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

    # Витамины
    vitamin_a = models.FloatField(null=True, blank=True)
    vitamin_b1 = models.FloatField(null=True, blank=True)
    vitamin_b2 = models.FloatField(null=True, blank=True)
    vitamin_b3 = models.FloatField(null=True, blank=True)
    vitamin_b6 = models.FloatField(null=True, blank=True)
    vitamin_b9 = models.FloatField(null=True, blank=True)
    vitamin_b12 = models.FloatField(null=True, blank=True)
    vitamin_c = models.FloatField(null=True, blank=True)
    vitamin_d = models.FloatField(null=True, blank=True)
    vitamin_e = models.FloatField(null=True, blank=True)
    vitamin_k = models.FloatField(null=True, blank=True)

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

    # Дополнительно
    water = models.FloatField(null=True, blank=True)
    ash = models.FloatField(null=True, blank=True)

    # Локальные поля
    image = models.ImageField(upload_to=ingredient_image_path, null=True, blank=True)
    category = models.ForeignKey(IngredientCategory, on_delete=models.SET_NULL, null=True, blank=True)
    is_common = models.BooleanField(default=False)

    # Служебные
    last_update = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    CATEGORY_CHOICES = [
        ('thermal', 'Тепловая обработка'),
        ('preparation', 'Подготовка продуктов'),
        ('shaping', 'Формование'),
        ('other', 'Прочее'),
    ]
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='thermal')
    short_description = models.CharField(max_length=200)
    description = models.TextField()
    scientific_background = models.TextField(blank=True)
    typical_temperature = models.CharField(max_length=50, blank=True)
    typical_duration = models.CharField(max_length=50, blank=True)
    tips = models.TextField(blank=True)
    common_mistakes = models.TextField(blank=True)
    advanced_notes = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-fire')
    color = models.CharField(max_length=20, default='amber')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Метод приготовления'
        verbose_name_plural = 'Методы приготовления'

    def __str__(self):
        return self.name


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