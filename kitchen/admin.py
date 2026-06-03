from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import (
    Cuisine, Diet, IngredientCategory, Ingredient,
    Recipe, RecipeStep, RecipeIngredient, CookingMethod,
    IngredientPreparation, RecommendedUtensil, IngredientSubstitution,
    CookingMethodSubstitution, UtensilSubstitution  # ← добавьте эти две
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


class IngredientSubstitutionInline(admin.TabularInline):
    model = IngredientSubstitution
    extra = 1
    fields = ['substitute_name', 'substitute_unit', 'ratio', 'notes']
    verbose_name = 'Допустимая замена'
    verbose_name_plural = 'Допустимые замены'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 3
    fields = ['ingredient', 'quantity', 'unit', 'notes', 'is_scalable']
    autocomplete_fields = ['ingredient']


class RecipeStepForm(forms.ModelForm):
    class Meta:
        model = RecipeStep
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subrecipe_id = None

        if self.data.get('subrecipe'):
            try:
                subrecipe_id = int(self.data.get('subrecipe'))
            except (ValueError, TypeError):
                pass
        elif self.instance and self.instance.subrecipe_id:
            subrecipe_id = self.instance.subrecipe_id

        if subrecipe_id:
            self.fields['subrecipe_base_ingredient'].queryset = RecipeIngredient.objects.filter(
                recipe_id=subrecipe_id
            ).select_related('ingredient')
        else:
            self.fields['subrecipe_base_ingredient'].queryset = RecipeIngredient.objects.none()


class RecipeStepInline(admin.TabularInline):
    model = RecipeStep
    form = RecipeStepForm
    fk_name = 'recipe'
    extra = 1
    ordering = ['order']
    fields = [
        'order', 'title', 'instruction', 'duration', 'temperature',
        'cooking_method', 'ingredient_preparation', 'recommended_utensils',
        'subrecipe', 'subrecipe_base_ingredient', 'subrecipe_base_quantity'
    ]
    autocomplete_fields = ['subrecipe', 'subrecipe_base_ingredient', 'cooking_method', 'ingredient_preparation']
    filter_horizontal = ['recommended_utensils']
    verbose_name = 'Шаг приготовления'
    verbose_name_plural = 'Шаги приготовления'


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


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'quantity', 'unit']
    list_filter = ['unit', 'is_scalable']
    search_fields = ['recipe__title', 'ingredient__name']
    autocomplete_fields = ['recipe', 'ingredient']
    inlines = [IngredientSubstitutionInline]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    save_on_top = True
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


@admin.register(IngredientSubstitution)
class IngredientSubstitutionAdmin(admin.ModelAdmin):
    list_display = ['recipe_ingredient', 'substitute_name', 'substitute_unit', 'ratio']
    list_filter = ['substitute_unit']
    search_fields = ['substitute_name', 'recipe_ingredient__ingredient__name']
    autocomplete_fields = ['recipe_ingredient']