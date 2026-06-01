from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Cuisine, Diet, IngredientCategory, Ingredient,
    Recipe, RecipeStep, RecipeIngredient, CookingMethod,
    IngredientPreparation, RecommendedUtensil
)


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


@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'sort_order', 'icon_preview']
    list_filter = ['parent']
    search_fields = ['name']
    list_editable = ['sort_order']

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<i class="fas fa-{}"></i>', obj.icon)
        return '-'

    icon_preview.short_description = 'Иконка'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'default_unit', 'calories_per_100g', 'is_common', 'image_preview']
    list_filter = ['category', 'default_unit', 'is_common', 'is_vegetarian', 'is_vegan', 'is_gluten_free']
    search_fields = ['name', 'description']
    list_editable = ['calories_per_100g', 'is_common']

    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'category', 'description', 'default_unit', 'image']
        }),
        ('Пищевая ценность (на 100г)', {
            'fields': ['calories_per_100g', 'protein_per_100g', 'fat_per_100g', 'carbs_per_100g']
        }),
        ('Сезонность и хранение', {
            'fields': ['season_start', 'season_end', 'storage_conditions', 'shelf_life_days']
        }),
        ('Аллергены и диеты', {
            'fields': ['allergens', 'is_vegetarian', 'is_vegan', 'is_gluten_free']
        }),
        ('Дополнительно', {
            'fields': ['density_data', 'is_common'],
            'classes': ['collapse']
        }),
    ]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 8px;" />',
                               obj.image.url)
        return '-'

    image_preview.short_description = 'Изображение'


class RecipeStepInline(admin.TabularInline):
    """Встроенная форма для шагов приготовления"""
    model = RecipeStep
    fk_name = 'recipe'  # ← указываем, какой ForeignKey использовать
    extra = 1
    ordering = ['order']
    fields = ['order', 'title', 'instruction', 'duration', 'subrecipe']
    autocomplete_fields = ['subrecipe']


class RecipeIngredientInline(admin.TabularInline):
    """Встроенная форма для ингредиентов рецепта"""
    model = RecipeIngredient
    extra = 3
    fields = ['ingredient', 'quantity', 'unit', 'notes', 'is_scalable']
    autocomplete_fields = ['ingredient']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'cuisine', 'difficulty', 'total_time', 'servings', 'created_at']
    list_filter = ['cuisine', 'difficulty', 'created_at', 'updated_at']
    search_fields = ['title', 'description', 'author']
    filter_horizontal = ['diet_tags', 'related_recipes']
    date_hierarchy = 'created_at'

    fieldsets = [
        ('Основная информация', {
            'fields': ['title', 'cuisine', 'author', 'description', 'image', 'video']
        }),
        ('Параметры', {
            'fields': ['total_time', 'servings', 'difficulty']
        }),
        ('Пищевая ценность', {
            'fields': ['calories', 'protein', 'fat', 'carbs'],
            'classes': ['collapse']
        }),
        ('Диеты и связи', {
            'fields': ['diet_tags', 'related_recipes']
        }),
    ]

    inlines = [RecipeStepInline, RecipeIngredientInline]


@admin.register(RecipeStep)
class RecipeStepAdmin(admin.ModelAdmin):
    list_display = ['order', 'title', 'recipe', 'duration']
    list_filter = ['recipe']
    search_fields = ['title', 'instruction']
    autocomplete_fields = ['recipe', 'subrecipe']


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'quantity', 'unit']
    list_filter = ['unit', 'is_scalable']
    search_fields = ['recipe__title', 'ingredient__name']
    autocomplete_fields = ['recipe', 'ingredient']


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
            return format_html('<img src="{}" width="40" height="40" style="object-fit: cover; border-radius: 8px;" />',
                               obj.image.url)
        return '-'

    image_preview.short_description = 'Изображение'