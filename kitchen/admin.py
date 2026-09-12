# kitchen/admin.py

from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count
from django.utils.safestring import mark_safe
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import (
    Recipe, HomeIngredient, RecipeStep,
    IngredientSubstitution, RecipeFoodItem,
    Cuisine, Diet, AbstractIngredient, Product,
    BrandedIngredient,
    IngredientCategory, SemanticTag, CookingMethod,
    IngredientPreparation, RecommendedUtensil, ProfessionalIngredient,
    IngredientSubstitutionRule,
)


# ======================= КАСТОМНЫЙ ВИДЖЕТ =======================

class HierarchicalCategoryWidget(forms.Select):
    """
    Виджет для выбора категории с иерархическим отображением и поиском.
    Рендерит HTML напрямую, без использования внешних шаблонов.
    """

    def get_choices(self):
        """Ленивая загрузка choices - только при рендеринге"""
        if not hasattr(self, '_cached_choices'):
            categories = []

            def build_flat_list(parent=None, level=0):
                children = IngredientCategory.objects.filter(parent=parent).order_by('sort_order', 'name')
                for cat in children:
                    if level > 0:
                        prefix = '—' * level
                        display_name = f"{prefix} {cat.name}"
                    else:
                        display_name = cat.name
                    categories.append((cat.id, display_name))
                    build_flat_list(cat, level + 1)

            build_flat_list()
            self._cached_choices = [('', '---------')] + categories

        return self._cached_choices

    def render(self, name, value, attrs=None, renderer=None):
        """Рендерим виджет без внешнего шаблона"""
        self.choices = self.get_choices()

        # Строим HTML для select с опциями
        options_html = ''
        for option_value, option_label in self.choices:
            selected = 'selected' if str(option_value) == str(value) else ''
            options_html += f'<option value="{option_value}" {selected}>{option_label}</option>'

        # Получаем выбранную категорию для превью
        preview_html = ''
        if value:
            try:
                category = IngredientCategory.objects.get(id=value)
                preview_html = f'''
                <div class="selected-category-info">
                    <span class="category-path">
                        <span class="current">{category.full_hierarchy}</span>
                    </span>
                </div>
                '''
            except IngredientCategory.DoesNotExist:
                pass

        # Собираем атрибуты
        attrs_str = ''
        if attrs:
            for attr_name, attr_value in attrs.items():
                attrs_str += f' {attr_name}="{attr_value}"'

        # Полный HTML виджета
        html = f'''
        <div class="hierarchical-category-widget">
            <div class="category-search-container">
                <input type="text" 
                       class="category-search-input" 
                       placeholder="🔍 Поиск категории..."
                       autocomplete="off">
                <div class="category-search-results" style="display: none;"></div>
            </div>
            <div class="category-select-wrapper">
                <select name="{name}"{attrs_str}>
                    {options_html}
                </select>
            </div>
            <div class="category-hierarchy-preview">
                {preview_html}
            </div>
        </div>
        '''

        return mark_safe(html)


# ======================= ФОРМА ДЛЯ ABSTRACTINGREDIENT =======================

class AbstractIngredientForm(forms.ModelForm):
    """
    Форма для AbstractIngredient с иерархическим выбором категории
    """

    class Meta:
        model = AbstractIngredient
        fields = '__all__'
        widgets = {
            'category': HierarchicalCategoryWidget(),
            'semantic_tags': admin.widgets.FilteredSelectMultiple('Семантические теги', is_stacked=False),
            'description': forms.Textarea(attrs={'rows': 15, 'cols': 80}),
            'short_description': forms.TextInput(attrs={'size': 80}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['semantic_tags'].queryset = SemanticTag.objects.filter(is_active=True)


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


# ======================= КАСТОМНЫЕ ФИЛЬТРЫ =======================

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
        pass


# ======================= ADMIN CLASSES =======================
class RecipeAdminForm(forms.ModelForm):
    """Форма с CKEditor 5 для текстовых полей"""

    class Meta:
        model = Recipe
        fields = '__all__'
        widgets = {
            'description': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='recipe_editor'
            ),
            'technological_process': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='recipe_editor'
            ),
            'quality_requirements': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='recipe_editor'
            ),
            'plating': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='recipe_editor'
            ),
            'storage_conditions': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='recipe_editor'
            ),
        }

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm

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
        ('Для ТТК (Технико-технологическая карта)', {
            'fields': (
                'technological_process',
                'quality_requirements',
                'yield_weight',
                'portion_size',
            ),
            'classes': ('collapse',),
            'description': 'Заполняется только для ТТК и полуфабрикатов'
        }),
        ('Оформление и подача', {
            'fields': ('plating', 'plating_image'),
            'classes': ('wide',),
            'description': 'Рекомендации по оформлению и фото готового блюда'
        }),
        ('Условия и сроки хранения', {
            'fields': ('storage_conditions',),
            'classes': ('wide',),
            'description': 'Условия хранения, температура, срок годности'
        }),
        ('Визуальные материалы', {
            'fields': ('image', 'video'),
            'classes': ('collapse',),
        }),
        ('Дополнительно', {
            'fields': ('diet_tags', 'related_recipes', 'components'),
            'classes': ('collapse',),
        }),
    )

    inlines = [
        RecipeStepInline,
        ComponentInline,
        ProfessionalIngredientInline,
        RecipeFoodItemInline,
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
        if obj.recipe_type in ['ttk', 'semi_finished']:
            obj.is_professional = True
        super().save_model(request, obj, form, change)
        obj.save()


class CuisineAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'region', 'created_at']
    search_fields = ['name', 'region', 'description']
    list_filter = ['parent', 'region']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['parent']


register_if_not_registered(Cuisine, CuisineAdmin)


class DietAdmin(admin.ModelAdmin):
    list_display = ['name', 'authority', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['allowed_ingredients', 'prohibited_ingredients']


register_if_not_registered(Diet, DietAdmin)


@admin.register(AbstractIngredient)
class AbstractIngredientAdmin(admin.ModelAdmin):
    form = AbstractIngredientForm
    save_on_top = True

    list_per_page = 13
    list_display = [
        'preview_image', 'name', 'name_normalized', 'category',
        'short_description_preview',  # Вместо description_ru
        'calories', 'protein', 'fat', 'carbohydrates',
        'is_active', 'data_source'
    ]
    list_display_links = ['name']
    list_filter = ['category', 'is_active', 'data_source', 'created_at']
    # search_fields = ['name', 'name_normalized', 'short_description', 'description']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['assign_category']
    filter_horizontal = ['semantic_tags']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'name_normalized', 'category',)
        }),
        ('Описание', {
            'fields': ('short_description', 'description'),
            'description': '''
                <strong>Краткое описание:</strong> используется в карточках и списках (до 500 символов)<br>
                <strong>Полное описание:</strong> детальная информация для страницы ингредиента
            '''
        }),
        ('Изображение', {
            'fields': ('image',),
        }),
        ('Семантические теги', {
            'fields': ('semantic_tags',),
            'classes': ('collapse',),
        }),

        ('КБЖУ', {
            'fields': ('calories', 'protein', 'fat', 'carbohydrates'),
            'classes': ('collapse',),
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
        ('Семантические данные (структурированные)', {
            'fields': ('semantic_data',),
            'classes': ('collapse',),
            'description': '''
                <strong>Структура JSON:</strong><br>
                - properties: свойства ингредиента (постный, жирный, сладкий и т.д.)<br>
                - preparations: способы подготовки<br>
                - cooking_methods: методы приготовления (с приоритетом)<br>
                - applications: кулинарное применение<br>
                - pairings: сочетаемость (белки, овощи, соусы, травы, специи)<br>
                - substitutes: возможные замены
            '''
        }),
        ('Служебная информация', {
            'fields': ('data_source', 'fdc_id', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Краткое описание')
    def short_description_preview(self, obj):
        if obj.short_description:
            return obj.short_description[:40] + '...' if len(obj.short_description) > 80 else obj.short_description
        return '-'

    @admin.display(description='Фото')
    def preview_image(self, obj):
        if obj.image and obj.image.url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 4px;" />',
                obj.image.url
            )
        return '-'

    @admin.action(description='Назначить категорию выбранным ингредиентам')
    def assign_category(self, request, queryset):
        """Массовое назначение категории выбранным ингредиентам."""
        from django.shortcuts import render
        from django.http import HttpResponseRedirect

        if 'apply' in request.POST:
            category_id = request.POST.get('category')
            if category_id:
                try:
                    category = IngredientCategory.objects.get(id=category_id)
                    count = queryset.update(category=category)
                    self.message_user(
                        request,
                        f'✅ Категория "{category.name}" назначена для {count} ингредиентов.',
                        level='SUCCESS'
                    )
                except IngredientCategory.DoesNotExist:
                    self.message_user(request, '❌ Категория не найдена', level='ERROR')
            else:
                count = queryset.update(category=None)
                self.message_user(
                    request,
                    f'✅ Категория удалена у {count} ингредиентов.',
                    level='SUCCESS'
                )
            return HttpResponseRedirect(request.get_full_path())

        # Строим плоский список категорий с префиксами
        categories = []

        def build_flat_list(parent=None, level=0):
            children = IngredientCategory.objects.filter(parent=parent).order_by('sort_order', 'name')
            for cat in children:
                prefix = '—' * level
                display_name = f"{prefix} {cat.name}" if level > 0 else cat.name
                categories.append({
                    'id': cat.id,
                    'name': display_name,
                    'level': level,
                    'full_hierarchy': cat.full_hierarchy,
                })
                build_flat_list(cat, level + 1)

        build_flat_list()

        if not categories:
            categories = [{
                'id': cat.id,
                'name': cat.name,
                'level': 0,
                'full_hierarchy': cat.name,
            } for cat in IngredientCategory.objects.all().order_by('name')]

        with_category = queryset.filter(category__isnull=False).count()
        without_category = queryset.filter(category__isnull=True).count()

        context = {
            'title': 'Назначить категорию ингредиентам',
            'queryset': queryset,
            'categories': categories,
            'with_category': with_category,
            'without_category': without_category,
            'total_count': queryset.count(),
            'action': 'assign_category',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/kitchen/abstractingredient/bulk_assign_category.html', context)


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'code', 'nutriscore_grade', 'nova_group', 'last_update']
    search_fields = ['name', 'brand', 'code', 'ingredients_text']
    list_filter = ['nutriscore_grade', 'nova_group', 'data_source', 'last_update']


register_if_not_registered(Product, ProductAdmin)


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


class SemanticTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'tag_type', 'group', 'parent', 'is_active', 'ingredient_count']
    list_filter = ['tag_type', 'group', 'is_active', 'parent']
    search_fields = ['name', 'group', 'description']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['parent', 'created_by']
    readonly_fields = ['created_at', 'updated_at', 'ingredient_count']

    def ingredient_count(self, obj):
        return obj.abstract_ingredients.count()

    ingredient_count.short_description = 'Ингредиентов'


register_if_not_registered(SemanticTag, SemanticTagAdmin)


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


class IngredientPreparationAdmin(admin.ModelAdmin):
    list_display = ['name', 'time_factor', 'waste_percentage']
    search_fields = ['name', 'description', 'tips']


register_if_not_registered(IngredientPreparation, IngredientPreparationAdmin)


class RecommendedUtensilAdmin(admin.ModelAdmin):
    list_display = ['name', 'alternative']
    search_fields = ['name', 'description']


register_if_not_registered(RecommendedUtensil, RecommendedUtensilAdmin)


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


class HomeIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'quantity', 'unit', 'is_scalable']
    list_filter = ['unit', 'is_scalable']
    search_fields = ['ingredient__name', 'recipe__title']
    autocomplete_fields = ['recipe', 'ingredient']


register_if_not_registered(HomeIngredient, HomeIngredientAdmin)


class IngredientSubstitutionAdmin(admin.ModelAdmin):
    list_display = ['recipe_ingredient', 'substitute_ingredient', 'ratio', 'substitute_unit']
    list_filter = ['substitute_unit']
    autocomplete_fields = ['recipe_ingredient', 'substitute_ingredient']


register_if_not_registered(IngredientSubstitution, IngredientSubstitutionAdmin)


class RecipeFoodItemAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'food_name', 'food_type', 'quantity', 'unit', 'is_scalable']
    list_filter = ['unit', 'is_scalable']
    search_fields = ['ingredient__name', 'product__name', 'recipe__title']
    autocomplete_fields = ['recipe', 'ingredient', 'product']


register_if_not_registered(RecipeFoodItem, RecipeFoodItemAdmin)


@admin.register(IngredientSubstitutionRule)
class IngredientSubstitutionRuleAdmin(admin.ModelAdmin):
    list_display = [
        'original_ingredient',
        'get_target_display',
        'substitution_type',
        'ratio',
        'unit',
        'priority',
        'is_active'
    ]
    list_filter = ['substitution_type', 'is_active']
    search_fields = ['original_ingredient__name', 'substitute_ingredient__name', 'substitute_branded__product_name']
    autocomplete_fields = ['original_ingredient', 'substitute_ingredient', 'substitute_branded']
    filter_horizontal = ['required_tags', 'optional_tags', 'forbidden_tags']

    fieldsets = (
        ('Исходный ингредиент', {
            'fields': ('original_ingredient',)
        }),
        ('Замена (ручной выбор)', {
            'fields': ('substitute_ingredient', 'substitute_branded'),
            'description': 'Выберите конкретный ингредиент или брендированный продукт'
        }),
        ('Автоматический подбор по тегам', {
            'fields': ('required_tags', 'optional_tags', 'forbidden_tags'),
            'classes': ('collapse',),
            'description': 'Теги для автоматического поиска замен (если не выбран конкретный ингредиент)'
        }),
        ('Параметры', {
            'fields': ('substitution_type', 'ratio', 'unit', 'priority')
        }),
        ('Дополнительно', {
            'fields': ('notes', 'is_active', 'created_by')
        }),
    )

    def get_target_display(self, obj):
        return obj.get_target_display()

    get_target_display.short_description = 'Замена'

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ======================= ОФОРМЛЕНИЕ АДМИНКИ =======================

admin.site.site_header = 'Кулинарная книга'
admin.site.site_title = 'Кулинарная книга'
admin.site.index_title = 'Управление рецептами и ингредиентами'