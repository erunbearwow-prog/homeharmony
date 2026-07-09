# kitchen/admin.py

from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    Recipe, HomeIngredient, RecipeStep,
    IngredientSubstitution, RecipeFoodItem,
    Cuisine, Diet, AbstractIngredient, Product,
    BrandedIngredient,  # <-- Добавляем BrandedIngredient
    IngredientCategory, SemanticTag, CookingMethod,
    IngredientPreparation, RecommendedUtensil, ProfessionalIngredient,
)


# ======================= INLINE FORMS =======================

class HomeIngredientInlineForm(forms.ModelForm):
    class Meta:
        model = HomeIngredient
        fields = ['ingredient', 'quantity', 'unit', 'notes', 'is_scalable']
        widgets = {
            'notes': forms.TextInput(attrs={'style': 'width: 200px;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ingredient'].queryset = AbstractIngredient.objects.filter(is_active=True).order_by('name')

        class ProfessionalIngredientInline(admin.TabularInline):
            """Inline для профессиональных ингредиентов (брутто/нетто)"""
            model = ProfessionalIngredient
            extra = 1
            fields = ['ingredient', 'gross_weight', 'net_weight', 'unit', 'loss_factor', 'is_base_allowed']
            autocomplete_fields = ['ingredient']

            def get_queryset(self, request):
                return super().get_queryset(request).select_related('ingredient')


class ProfessionalIngredientInline(admin.TabularInline):
    """Inline для профессиональных ингредиентов (брутто/нетто)"""
    model = ProfessionalIngredient
    extra = 1
    fields = ['ingredient', 'gross_weight', 'net_weight', 'unit', 'loss_factor', 'is_base_allowed']
    autocomplete_fields = ['ingredient']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ingredient')


class RecipeFoodItemInlineForm(forms.ModelForm):
    class Meta:
        model = RecipeFoodItem
        fields = ['ingredient', 'product', 'quantity', 'unit', 'notes', 'is_scalable']
        widgets = {
            'notes': forms.TextInput(attrs={'style': 'width: 200px;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ingredient'].queryset = AbstractIngredient.objects.filter(is_active=True).order_by('name')
        self.fields['product'].queryset = Product.objects.all().order_by('name')


class RecipeStepForm(forms.ModelForm):
    class Meta:
        model = RecipeStep
        fields = [
            'order', 'title', 'instruction', 'duration', 'temperature',
            'recipe_step_image', 'subrecipe',
            'subrecipe_base_ingredient', 'subrecipe_base_quantity',
            'cooking_method', 'ingredient_preparation', 'recommended_utensils'
        ]
        widgets = {
            'instruction': forms.Textarea(attrs={'rows': 4, 'cols': 80}),
            'recommended_utensils': forms.SelectMultiple(attrs={'style': 'height: 100px;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subrecipe'].queryset = Recipe.objects.all().order_by('title')
        self.fields['subrecipe_base_ingredient'].queryset = HomeIngredient.objects.select_related('ingredient').all()


# ======================= INLINES =======================

class HomeIngredientInline(admin.TabularInline):
    model = HomeIngredient
    form = HomeIngredientInlineForm
    extra = 3
    fields = ['ingredient', 'quantity', 'unit', 'notes', 'is_scalable']
    show_change_link = True
    autocomplete_fields = ['ingredient']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ingredient')


class RecipeFoodItemInline(admin.TabularInline):
    model = RecipeFoodItem
    form = RecipeFoodItemInlineForm
    extra = 2
    fields = ['ingredient', 'product', 'quantity', 'unit', 'notes', 'is_scalable']
    show_change_link = True
    autocomplete_fields = ['ingredient', 'product']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ingredient', 'product')


class IngredientSubstitutionInline(admin.TabularInline):
    model = IngredientSubstitution
    extra = 1
    fields = ['substitute_ingredient', 'substitute_unit', 'ratio', 'notes']
    autocomplete_fields = ['substitute_ingredient']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('substitute_ingredient')


class RecipeStepInline(admin.StackedInline):
    model = RecipeStep
    form = RecipeStepForm
    fk_name = 'recipe'
    extra = 3
    fieldsets = (
        ('Основная информация', {
            'fields': ('order', 'title', 'instruction', 'duration', 'temperature', 'recipe_step_image')
        }),
        ('Вложенный рецепт (полуфабрикат)', {
            'fields': ('subrecipe', 'subrecipe_base_ingredient', 'subrecipe_base_quantity'),
            'classes': ('collapse',),
        }),
        ('Методы и утварь', {
            'fields': ('cooking_method', 'ingredient_preparation', 'recommended_utensils'),
        }),
    )
    autocomplete_fields = ['subrecipe', 'cooking_method', 'ingredient_preparation']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cooking_method', 'ingredient_preparation', 'subrecipe', 'subrecipe_base_ingredient'
        ).prefetch_related('recommended_utensils')


class ComponentInline(admin.TabularInline):
    model = Recipe.components.through
    fk_name = 'from_recipe'
    verbose_name = 'Компонент (вложенный рецепт)'
    verbose_name_plural = 'Компоненты (вложенные рецепты)'
    extra = 1
    fields = ['to_recipe', 'get_component_link']
    readonly_fields = ['get_component_link']
    autocomplete_fields = ['to_recipe']

    def get_component_link(self, obj):
        if obj.to_recipe:
            url = reverse('admin:kitchen_recipe_change', args=[obj.to_recipe.id])
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.to_recipe.title)
        return '-'

    get_component_link.short_description = 'Ссылка на компонент'


# ======================= КАСТОМНЫЙ ФИЛЬТР =======================

class RecipeWithSubrecipeFilter(admin.SimpleListFilter):
    title = 'наличие вложенных рецептов'
    parameter_name = 'has_subrecipe'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть вложенные рецепты'),
            ('no', 'Нет вложенных рецептов'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(steps__subrecipe__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.exclude(steps__subrecipe__isnull=False).distinct()
        return queryset


class RecipeTypeFilter(admin.SimpleListFilter):
    title = 'тип рецепта'
    parameter_name = 'recipe_type'

    def lookups(self, request, model_admin):
        return (
            ('home', 'Домашние рецепты'),
            ('ttk', 'ТТК'),
            ('semi_finished', 'Полуфабрикаты'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(recipe_type=self.value())
        return queryset


# ======================= ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ =======================

def register_if_not_registered(model, admin_class):
    """Регистрирует модель в админке, если она ещё не зарегистрирована"""
    try:
        admin.site.register(model, admin_class)
    except admin.sites.AlreadyRegistered:
        # Модель уже зарегистрирована, пропускаем
        pass


# ======================= ADMIN CLASSES =======================

# kitchen/admin.py - обновить RecipeAdmin

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'recipe_type', 'is_saved_variant', 'original_recipe',
        'ttk_code', 'cuisine', 'author', 'difficulty', 'servings',
        'total_time', 'created_at', 'ingredients_count', 'steps_count'
    ]
    list_filter = [
        RecipeTypeFilter,
        'is_saved_variant',
        'is_professional',
        'difficulty',
        'cuisine',
        'created_at',
        RecipeWithSubrecipeFilter
    ]
    search_fields = ['title', 'description', 'author', 'ttk_code']

    readonly_fields = [
        'total_time', 'calories', 'protein', 'fat', 'carbs',
        'created_at', 'updated_at', 'saved_at'
    ]

    fieldsets = (
        ('Тип рецепта', {
            'fields': ('recipe_type', 'ttk_code'),
            'description': 'Выберите тип рецепта'
        }),
        ('Основная информация', {
            'fields': ('title', 'author', 'cuisine', 'description', 'difficulty', 'servings', 'is_professional')
        }),
        ('Сохраненный вариант', {
            'fields': (
            'is_saved_variant', 'original_recipe', 'saved_by_session', 'saved_by_user', 'is_favorite', 'saved_notes'),
            'classes': ('collapse',),
            'description': 'Информация о сохраненном варианте рецепта'
        }),
        ('Для ТТК (Технико-технологическая карта)', {
            'fields': (
                'technological_process',
                'quality_requirements',
                'yield_weight',
                'portion_size',
                'consumption_rates',
                'tech_card_data'
            ),
            'classes': ('collapse',),
            'description': 'Заполняется только для ТТК и полуфабрикатов'
        }),
        ('Оформление и подача', {
            'fields': ('plating', 'plating_image'),
            'classes': ('wide',),
            'description': 'Рекомендации по оформлению и фото готового блюда'
        }),
        ('Визуальные материалы', {
            'fields': ('image', 'video'),
            'classes': ('collapse',),
        }),
        ('Пищевая ценность (рассчитывается автоматически)', {
            'fields': ('calories', 'protein', 'fat', 'carbs', 'total_time'),
            'classes': ('collapse',),
        }),
        ('Дополнительно', {
            'fields': ('diet_tags', 'related_recipes', 'components'),
            'classes': ('collapse',),
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    inlines = [
        RecipeStepInline,
        ComponentInline,
        ProfessionalIngredientInline,  # <-- добавляем для ТТК
        RecipeFoodItemInline,  # <-- для домашних
    ]
    filter_horizontal = ['diet_tags', 'related_recipes', 'components']
    autocomplete_fields = ['cuisine', 'original_recipe']
    save_on_top = True

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            ingredients_count=Count('home_ingredients', distinct=True),
            steps_count=Count('steps', distinct=True)
        )

    def ingredients_count(self, obj):
        return obj.ingredients_count

    ingredients_count.short_description = 'Ингредиентов'

    def steps_count(self, obj):
        return obj.steps_count

    steps_count.short_description = 'Шагов'

    @admin.display(description='Вложенные рецепты')
    def components_list(self, obj):
        components = obj.components.all()
        if components:
            return format_html(
                '<br>'.join([
                    f'<a href="{reverse("admin:kitchen_recipe_change", args=[c.id])}">{c.title}</a>'
                    for c in components
                ])
            )
        return '-'

    def save_model(self, request, obj, form, change):
        # Если выбран ТТК или полуфабрикат, автоматически включаем профессиональный режим
        if obj.recipe_type in ['ttk', 'semi_finished']:
            obj.is_professional = True
        super().save_model(request, obj, form, change)
        obj.save()


register_if_not_registered(Recipe, RecipeAdmin)


# Cuisine
class CuisineAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'region', 'created_at']
    search_fields = ['name', 'region', 'description']
    list_filter = ['parent', 'region']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['parent']


register_if_not_registered(Cuisine, CuisineAdmin)


# Diet
class DietAdmin(admin.ModelAdmin):
    list_display = ['name', 'authority', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['allowed_ingredients', 'prohibited_ingredients']


register_if_not_registered(Diet, DietAdmin)


# AbstractIngredient
class AbstractIngredientAdmin(admin.ModelAdmin):
    list_display = [
        'preview_image', 'name', 'name_normalized', 'category',
        'calories', 'protein', 'fat', 'carbohydrates',
        'is_active', 'data_source'
    ]
    list_filter = ['category', 'is_active', 'data_source', 'created_at']
    search_fields = ['name', 'name_normalized', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'name_normalized', 'description', 'description_ru', 'category')
        }),
        ('Изображение', {
            'fields': ('image',),
            'classes': ('collapse',),
        }),
        ('КБЖУ', {
            'fields': ('calories', 'protein', 'fat', 'carbohydrates'),
        }),
        ('Микронутриенты', {
            'fields': ('fiber', 'sugar', 'water', 'ash', 'starch'),
            'classes': ('collapse',),
        }),
        ('Витамины', {
            'fields': (
                'vitamin_a', 'beta_carotene', 'vitamin_b1', 'vitamin_b2',
                'vitamin_b3', 'vitamin_b4', 'vitamin_b5', 'vitamin_b6',
                'vitamin_b7', 'vitamin_b9_folate', 'vitamin_b12', 'vitamin_c',
                'vitamin_d', 'vitamin_e', 'vitamin_k'
            ),
            'classes': ('collapse',),
        }),
        ('Минералы (макро)', {
            'fields': ('potassium', 'calcium', 'magnesium', 'sodium', 'phosphorus', 'sulfur', 'silicon', 'chlorine'),
            'classes': ('collapse',),
        }),
        ('Минералы (микро)', {
            'fields': (
                'iron', 'manganese', 'copper', 'selenium', 'zinc',
                'aluminum', 'boron', 'vanadium', 'iodine', 'cobalt',
                'lithium', 'molybdenum', 'nickel', 'rubidium', 'fluorine', 'chromium'
            ),
            'classes': ('collapse',),
        }),
        ('Жирные кислоты', {
            'fields': ('saturated_fat', 'trans_fat', 'cholesterol', 'omega_3', 'omega_6'),
            'classes': ('collapse',),
        }),
        ('Служебная информация', {
            'fields': ('data_source', 'fdc_id', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    filter_horizontal = ['semantic_tags']
    autocomplete_fields = ['category']

    @admin.display(description='Фото')
    def preview_image(self, obj):
        if obj.image and obj.image.url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 4px;" />',
                obj.image.url
            )
        return '-'


register_if_not_registered(AbstractIngredient, AbstractIngredientAdmin)


# Product
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'code', 'nutriscore_grade', 'nova_group', 'last_update']
    search_fields = ['name', 'brand', 'code', 'ingredients_text']
    list_filter = ['nutriscore_grade', 'nova_group', 'data_source', 'last_update']


register_if_not_registered(Product, ProductAdmin)


# BrandedIngredient
class BrandedIngredientAdmin(admin.ModelAdmin):
    list_display = ['brand', 'product_name', 'abstract', 'barcode', 'store', 'is_available']
    search_fields = ['brand', 'product_name', 'barcode']
    list_filter = ['brand', 'store', 'is_available', 'created_at']
    autocomplete_fields = ['abstract', 'created_by']
    readonly_fields = ['price_per_100g', 'price_per_kg', 'created_at', 'updated_at']


register_if_not_registered(BrandedIngredient, BrandedIngredientAdmin)


@admin.register(ProfessionalIngredient)
class ProfessionalIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'gross_weight', 'net_weight', 'unit', 'loss_factor']
    list_filter = ['unit', 'is_base_allowed']
    search_fields = ['ingredient__name', 'recipe__title']
    autocomplete_fields = ['recipe', 'ingredient']


# IngredientCategory
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'level', 'full_hierarchy', 'icon', 'sort_order']
    list_filter = ['parent']
    search_fields = ['name']
    ordering = ['sort_order', 'name']
    autocomplete_fields = ['parent']

    @admin.display(description='Полная иерархия')
    def full_hierarchy(self, obj):
        return obj.full_hierarchy


register_if_not_registered(IngredientCategory, IngredientCategoryAdmin)


# SemanticTag
class SemanticTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'tag_type', 'group', 'parent', 'is_active', 'ingredient_count']
    list_filter = ['tag_type', 'group', 'is_active', 'parent']
    search_fields = ['name', 'group', 'description']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['parent', 'created_by']
    readonly_fields = ['created_at', 'updated_at', 'ingredient_count']

    def ingredient_count(self, obj):
        return obj.ingredient_count

    ingredient_count.short_description = 'Ингредиентов'


register_if_not_registered(SemanticTag, SemanticTagAdmin)


# CookingMethod
class CookingMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_heat_treatment', 'difficulty', 'sort_order', 'breading_type']
    search_fields = ['name', 'code', 'description']
    list_filter = ['is_heat_treatment', 'difficulty', 'breading_type']
    filter_horizontal = ['best_ingredients']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'description', 'icon', 'image', 'video_url')
        }),
        ('Тип обработки', {
            'fields': ('is_heat_treatment', 'breading_type', 'difficulty')
        }),
        ('Температура', {
            'fields': ('recommended_temperature_min', 'recommended_temperature_max')
        }),
        ('Сложность и обучение', {
            'fields': (
                'tips', 'common_mistakes', 'scientific_background',
                'advanced_notes', 'beginner_tips', 'step_by_step_guide'
            ),
            'classes': ('collapse',),
        }),
        ('Данные для расчётов', {
            'fields': ('oil_absorption_rates', 'cut_shape_factors'),
            'classes': ('collapse',),
        }),
        ('Лучшие ингредиенты', {
            'fields': ('best_ingredients',),
            'classes': ('collapse',),
        }),
        ('Для детей', {
            'fields': ('can_cook_with_children', 'child_friendly_notes'),
            'classes': ('collapse',),
        }),
        ('Служебное', {
            'fields': ('sort_order',),
            'classes': ('collapse',),
        }),
    )


register_if_not_registered(CookingMethod, CookingMethodAdmin)


# IngredientPreparation
class IngredientPreparationAdmin(admin.ModelAdmin):
    list_display = ['name', 'time_factor', 'waste_percentage']
    search_fields = ['name', 'description', 'tips']


register_if_not_registered(IngredientPreparation, IngredientPreparationAdmin)


# RecommendedUtensil
class RecommendedUtensilAdmin(admin.ModelAdmin):
    list_display = ['name', 'alternative']
    search_fields = ['name', 'description']


register_if_not_registered(RecommendedUtensil, RecommendedUtensilAdmin)


# RecipeStep
class RecipeStepAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipe', 'order', 'title', 'duration', 'cooking_method']
    list_filter = ['cooking_method', 'ingredient_preparation']
    search_fields = ['title', 'instruction']
    autocomplete_fields = ['recipe', 'subrecipe', 'cooking_method', 'ingredient_preparation']
    filter_horizontal = ['recommended_utensils']

    @admin.display(description='Картинка')
    def preview_step_image(self, obj):
        if obj.recipe_step_image and obj.recipe_step_image.url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 4px; object-fit: cover;" />',
                obj.recipe_step_image.url
            )
        return '-'


register_if_not_registered(RecipeStep, RecipeStepAdmin)


# HomeIngredient
class HomeIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'quantity', 'unit', 'is_scalable']
    list_filter = ['unit', 'is_scalable']
    search_fields = ['ingredient__name', 'recipe__title']
    autocomplete_fields = ['recipe', 'ingredient']


register_if_not_registered(HomeIngredient, HomeIngredientAdmin)


# IngredientSubstitution
class IngredientSubstitutionAdmin(admin.ModelAdmin):
    list_display = ['recipe_ingredient', 'substitute_ingredient', 'ratio', 'substitute_unit']
    list_filter = ['substitute_unit']
    autocomplete_fields = ['recipe_ingredient', 'substitute_ingredient']


register_if_not_registered(IngredientSubstitution, IngredientSubstitutionAdmin)


# RecipeFoodItem
class RecipeFoodItemAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'food_name', 'food_type', 'quantity', 'unit', 'is_scalable']
    list_filter = ['unit', 'is_scalable']
    search_fields = ['ingredient__name', 'product__name', 'recipe__title']
    autocomplete_fields = ['recipe', 'ingredient', 'product']


register_if_not_registered(RecipeFoodItem, RecipeFoodItemAdmin)

# ======================= ОФОРМЛЕНИЕ АДМИНКИ =======================

admin.site.site_header = 'Кулинарная книга'
admin.site.site_title = 'Кулинарная книга'
admin.site.index_title = 'Управление рецептами и ингредиентами'