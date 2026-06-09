from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import (
    Cuisine, Diet, IngredientCategory, Ingredient,
    Recipe, RecipeStep, RecipeIngredient, CookingMethod,
    IngredientPreparation, RecommendedUtensil, IngredientSubstitution,
    CookingMethodSubstitution, UtensilSubstitution, ProfessionalIngredient
)


# ======================= БАЗОВЫЕ РЕГИСТРАЦИИ =======================

@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'created_at']
    list_filter = ['region']
    search_fields = ['name', 'region', 'description']


@admin.register(Diet)
class DietAdmin(admin.ModelAdmin):
    list_display = ['name', 'authority', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['allowed_ingredients', 'prohibited_ingredients']


# ======================= INLINE КЛАССЫ =======================

# ========== INLINE ДЛЯ ПРОФЕССИОНАЛЬНЫХ ИНГРЕДИЕНТОВ ==========
class ProfessionalIngredientInline(admin.TabularInline):
    """Inline-форма для брутто/нетто ингредиентов (проф. режим)"""
    model = ProfessionalIngredient
    extra = 1
    fields = ['ingredient', 'gross_weight', 'net_weight', 'unit']
    autocomplete_fields = ['ingredient']
    verbose_name = 'Ингредиент (профессиональный)'
    verbose_name_plural = 'Ингредиенты (брутто/нетто)'

    # Отображаем коэффициент потерь только для чтения
    readonly_fields = ['loss_factor_display']

    def loss_factor_display(self, obj):
        """Отображаем коэффициент потерь, если он есть"""
        if obj.pk and obj.loss_factor:
            return f"{obj.loss_factor:.2f}"
        return "-"

    loss_factor_display.short_description = 'Коэф. потерь (брутто/нетто)'


class IngredientSubstitutionInline(admin.TabularInline):
    model = IngredientSubstitution
    extra = 1
    fields = ['substitute_ingredient', 'substitute_unit', 'ratio', 'notes']
    autocomplete_fields = ['substitute_ingredient']
    verbose_name = '✅ Замена'
    verbose_name_plural = '✅ Возможные замены (прямо в этом рецепте)'
    classes = ['collapse']


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0  # ← не создаём пустых форм
    min_num = 0  # ← минимум 0 форм
    fields = ['ingredient', 'quantity', 'unit', 'notes', 'is_scalable', 'edit_substitutions']
    autocomplete_fields = ['ingredient']
    readonly_fields = ['edit_substitutions']
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Добавляем проверку на пустоту
        formset.validate_min = False
        return formset

    def edit_substitutions(self, obj):
        """Ссылка на редактирование замен для этого ингредиента"""
        if obj and obj.pk:
            from django.urls import reverse
            url = reverse('admin:kitchen_recipeingredient_change', args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank" style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; text-decoration: none; color: #0d6efd;">'
                '🔄 Управление заменами</a>', url
            )
        return '—'
    edit_substitutions.short_description = 'Замены'


class RecipeStepForm(forms.ModelForm):
    class Meta:
        model = RecipeStep
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        print("=== RecipeStepForm.__init__ ===")
        print(f"args: {args}")
        print(f"kwargs keys: {kwargs.keys()}")

        if 'subrecipe_base_ingredient' in self.fields:
            subrecipe_id = None

            # Способ 1: из данных POST (при сохранении)
            if self.data and self.data.get('subrecipe'):
                try:
                    subrecipe_id = int(self.data.get('subrecipe'))
                    print(f"Found subrecipe_id from data: {subrecipe_id}")
                except (ValueError, TypeError):
                    pass

            # Способ 2: из instance (при редактировании существующего)
            if not subrecipe_id and self.instance and self.instance.pk:
                subrecipe_id = self.instance.subrecipe_id
                print(f"Found subrecipe_id from instance: {subrecipe_id}")

            # Способ 3: из initial (при создании нового, если передали)
            if not subrecipe_id and self.initial.get('subrecipe'):
                subrecipe_id = self.initial.get('subrecipe')
                print(f"Found subrecipe_id from initial: {subrecipe_id}")

            if subrecipe_id:
                self.fields['subrecipe_base_ingredient'].queryset = RecipeIngredient.objects.filter(
                    recipe_id=subrecipe_id
                ).select_related('ingredient')
                print(f"Filtered queryset count: {self.fields['subrecipe_base_ingredient'].queryset.count()}")
            else:
                self.fields['subrecipe_base_ingredient'].queryset = RecipeIngredient.objects.none()
                print("No subrecipe_id found, queryset set to none")


class RecipeStepInline(admin.StackedInline):
    model = RecipeStep
    form = RecipeStepForm
    fk_name = 'recipe'
    extra = 1
    ordering = ['order']

    fields = (
        ('order', 'title'),
        ('instruction',),
        ('cooking_method', 'ingredient_preparation'),
        ('duration', 'temperature'),
        ('recommended_utensils',),
        ('subrecipe', 'subrecipe_base_ingredient', 'subrecipe_base_quantity'),
    )

    # autocomplete_fields = ['subrecipe', 'subrecipe_base_ingredient', 'cooking_method', 'ingredient_preparation']


    autocomplete_fields = ['subrecipe', 'cooking_method', 'ingredient_preparation']
    filter_horizontal = ['recommended_utensils']
    verbose_name = 'Шаг приготовления'
    verbose_name_plural = 'Шаги приготовления'


# ======================= ОСНОВНАЯ РЕГИСТРАЦИЯ RECIPE =======================

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ['title', 'cuisine', 'difficulty', 'servings', 'created_at']
    list_filter = ['cuisine', 'difficulty', 'is_professional', 'created_at', 'updated_at']
    search_fields = ['title', 'description', 'author']
    filter_horizontal = ['diet_tags', 'related_recipes']
    date_hierarchy = 'created_at'

    fieldsets = [
        ('Основная информация', {
            'fields': ['title', 'cuisine', 'author', 'description', 'image', 'is_professional'],
            'classes': ['collapse']
        }),
        ('Параметры', {
            'fields': ['servings', 'difficulty', 'total_time'],
            'classes': ['collapse']
        }),
        ('Пищевая ценность', {
            'fields': ['calories', 'protein', 'fat', 'carbs'],
            'classes': ['collapse']
        }),
        ('Диеты и связи', {
            'fields': ['diet_tags', 'related_recipes', 'components'],
            'classes': ['collapse']
        }),
    ]

    # ДОБАВИТЬ ЭТОТ МЕТОД
    def get_inlines(self, request, obj=None):
        """Динамически подставляем inline в зависимости от is_professional"""
        if obj and obj.is_professional:
            return [RecipeStepInline, ProfessionalIngredientInline]
        return [RecipeStepInline, RecipeIngredientInline]

    # ДОБАВИТЬ ЭТОТ МЕТОД
    def recipe_type_badge(self, obj):
        """Отображаем красивый бейдж в списке рецептов"""
        if obj.is_professional:
            return format_html(
                '<span style="background:#d97706; color:white; padding:2px 8px; border-radius:12px; font-size:11px;">📋 ТТК</span>')
        return format_html(
            '<span style="background:#10b981; color:white; padding:2px 8px; border-radius:12px; font-size:11px;">🍳 Рецепт</span>')

    recipe_type_badge.short_description = 'Тип'
    recipe_type_badge.admin_order_field = 'is_professional'

    # inlines = [RecipeStepInline, RecipeIngredientInline]


# ======================= ОСТАЛЬНЫЕ РЕГИСТРАЦИИ =======================

@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'quantity', 'unit']
    list_filter = ['unit', 'is_scalable']
    search_fields = ['recipe__title', 'ingredient__name']
    autocomplete_fields = ['recipe', 'ingredient']
    inlines = [IngredientSubstitutionInline]


@admin.register(RecipeStep)
class RecipeStepAdmin(admin.ModelAdmin):
    list_display = ['order', 'title', 'recipe', 'duration']
    list_filter = ['recipe']
    search_fields = ['title', 'instruction']
    autocomplete_fields = ['recipe', 'subrecipe']


@admin.register(CookingMethod)
class CookingMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'typical_temperature', 'typical_duration']
    list_filter = ['category']
    search_fields = ['name', 'description']
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'category', 'short_description', 'icon', 'color']
        }),
        ('Подробное описание', {
            'fields': ['description', 'scientific_background']
        }),
        ('Параметры', {
            'fields': ['typical_temperature', 'typical_duration']
        }),
        ('Советы и ошибки', {
            'fields': ['tips', 'common_mistakes', 'advanced_notes']
        }),
    ]


@admin.register(IngredientPreparation)
class IngredientPreparationAdmin(admin.ModelAdmin):
    list_display = ['name', 'time_factor', 'waste_percentage']
    search_fields = ['name', 'description']


@admin.register(RecommendedUtensil)
class RecommendedUtensilAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_preview']
    search_fields = ['name', 'description']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="40" height="40" style="object-fit: cover; border-radius: 8px;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Изображение'


@admin.register(CookingMethodSubstitution)
class CookingMethodSubstitutionAdmin(admin.ModelAdmin):
    list_display = ['original_method', 'substitute_method', 'reason']
    list_filter = ['original_method__category']
    search_fields = ['original_method__name', 'substitute_method__name', 'reason']
    autocomplete_fields = ['original_method', 'substitute_method']


@admin.register(UtensilSubstitution)
class UtensilSubstitutionAdmin(admin.ModelAdmin):
    list_display = ['original_utensil', 'substitute_utensil', 'reason']
    search_fields = ['original_utensil__name', 'substitute_utensil__name', 'reason']
    autocomplete_fields = ['original_utensil', 'substitute_utensil']


@admin.register(IngredientSubstitution)
class IngredientSubstitutionAdmin(admin.ModelAdmin):
    list_display = ['recipe_ingredient', 'substitute_ingredient', 'ratio', 'substitute_unit']
    list_filter = ['substitute_unit']
    search_fields = ['recipe_ingredient__ingredient__name', 'substitute_ingredient__name']
    autocomplete_fields = ['recipe_ingredient', 'substitute_ingredient']
    fields = ['recipe_ingredient', 'substitute_ingredient', 'substitute_unit', 'ratio', 'notes']


# kitchen/admin.py - добавить в конец файла
from .models import Ingredient, IngredientCategory

@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'sort_order']
    list_filter = ['parent']
    search_fields = ['name']
    list_editable = ['sort_order']

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ['name', 'name_ru', 'category', 'calories', 'protein', 'fat', 'carbohydrates', 'is_common']
    list_filter = ['category', 'is_common']
    search_fields = ['name', 'name_ru']
    list_editable = ['name_ru', 'calories', 'protein', 'fat', 'carbohydrates', 'is_common']
    fieldsets = (
        ('Основная информация', {'fields': ('name', 'name_ru', 'fdc_id', 'description', 'description_ru', 'image', 'category', 'is_common')}),
        ('Макронутриенты (на 100г)', {'fields': ('calories', 'protein', 'fat', 'carbohydrates', 'fiber', 'sugar')}),
        ('Жиры и холестерин', {'fields': ('saturated_fat', 'trans_fat', 'cholesterol')}),
        ('Витамины', {'fields': ('vitamin_a', 'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b6', 'vitamin_b9', 'vitamin_b12', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k')}),
        ('Минералы', {'fields': ('calcium', 'iron', 'magnesium', 'phosphorus', 'potassium', 'sodium', 'zinc', 'copper', 'manganese', 'selenium')}),
        ('Дополнительно', {'fields': ('water', 'ash', 'data_source'), 'classes': ('collapse',)}),
    )