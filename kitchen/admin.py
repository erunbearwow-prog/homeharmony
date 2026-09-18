# kitchen/admin.py

# ======================= ВРЕМЕННОЕ ОТКЛЮЧЕНИЕ АДМИНОК ДО МИГРАЦИЙ =======================
# TODO: вернуть после миграций и переписать под новые модели
SKIP_BROKEN_ADMIN = True

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
    UnitConversion,
    CutShape,
    StepIngredient,
    RecipeIngredientOption,
    MeasurementSystem,
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
if not SKIP_BROKEN_ADMIN:
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


class RecipeStepForm(forms.ModelForm):
    class Meta:
        model = RecipeStep
        fields = [
            'order', 'title', 'instruction', 'duration', 'temperature',
            'recipe_step_image', 'subrecipe',
            'subrecipe_base_ingredient', 'subrecipe_base_quantity',
            'recommended_utensils'
        ]
        widgets = {
            'instruction': forms.Textarea(attrs={'rows': 4, 'cols': 80}),
            'recommended_utensils': forms.SelectMultiple(attrs={'style': 'height: 100px;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subrecipe'].queryset = Recipe.objects.all().order_by('title')
        # RecipeFoodItem вместо HomeIngredient
        self.fields['subrecipe_base_ingredient'].queryset = RecipeFoodItem.objects.select_related('abstract_ingredient').all()


# ======================= INLINES =======================

if not SKIP_BROKEN_ADMIN:
    class HomeIngredientInline(admin.TabularInline):
        model = HomeIngredient
        form = HomeIngredientInlineForm
        extra = 3
        fields = ['ingredient', 'quantity', 'unit', 'notes', 'is_scalable']
        show_change_link = True
        autocomplete_fields = ['ingredient']

        def get_queryset(self, request):
            return super().get_queryset(request).select_related('ingredient')




if not SKIP_BROKEN_ADMIN:
    class IngredientSubstitutionInline(admin.TabularInline):
        model = IngredientSubstitution
        extra = 1
        fields = ['substitute_ingredient', 'substitute_unit', 'ratio', 'notes']
        autocomplete_fields = ['substitute_ingredient']

        def get_queryset(self, request):
            return super().get_queryset(request).select_related('substitute_ingredient')


class StepIngredientForm(forms.ModelForm):
    """Форма для ингредиента в шаге — фильтрует food_item по рецепту."""

    class Meta:
        model = StepIngredient
        fields = ['order', 'food_item', 'preparation', 'cooking_method', 'cooking_note']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем food_item — только ингредиенты этого же рецепта
        if self.instance and self.instance.step_id:
            recipe_id = self.instance.step.recipe_id
        elif self.data.get('step'):
            recipe_id = None  # не всегда доступно
        else:
            recipe_id = None

        # Пытаемся достать recipe_id из initial/parent
        step = self.instance.step if self.instance and self.instance.pk else None
        if step:
            self.fields['food_item'].queryset = RecipeFoodItem.objects.filter(
                recipe=step.recipe
            ).select_related('abstract_ingredient', 'branded_ingredient', 'subrecipe')
        else:
            self.fields['food_item'].queryset = RecipeFoodItem.objects.none()

        self.fields['preparation'].queryset = IngredientPreparation.objects.all().order_by('name')
        self.fields['cooking_method'].queryset = CookingMethod.objects.all().order_by('name')


class RecipeStepInline(admin.StackedInline):
    model = RecipeStep
    form = RecipeStepForm
    fk_name = 'recipe'
    extra = 1
    fieldsets = (
        ('Основная информация', {
            'fields': ('order', 'title', 'instruction', 'duration', 'temperature', 'recipe_step_image')
        }),
        ('Вложенный рецепт (полуфабрикат)', {
            'fields': ('subrecipe', 'subrecipe_base_ingredient', 'subrecipe_base_quantity'),
            'classes': ('collapse',),
        }),
        ('Утварь', {
            'fields': ('recommended_utensils',),
        }),
    )
    autocomplete_fields = ['subrecipe']
    show_change_link = True  # ← добавили — ведёт на страницу шага

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'subrecipe', 'subrecipe_base_ingredient'
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


# ======================= РЕЦЕПТ: ИНГРЕДИЕНТЫ =======================

class RecipeFoodItemInlineForm(forms.ModelForm):
    """Форма ингредиента рецепта с учётом абстрактных/брендированных/полуфабрикатов."""

    class Meta:
        model = RecipeFoodItem
        fields = [
            'abstract_ingredient', 'branded_ingredient', 'subrecipe',
            'quantity', 'unit', 'cut_shape', 'override_cooking_method',
            'notes', 'is_scalable',
        ]
        widgets = {
            'notes': forms.TextInput(attrs={'style': 'width: 200px;'}),
            'quantity': forms.NumberInput(attrs={'style': 'width: 80px;', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['abstract_ingredient'].queryset = AbstractIngredient.objects.filter(
            is_active=True
        ).order_by('name')
        self.fields['branded_ingredient'].queryset = BrandedIngredient.objects.all().order_by('brand', 'product_name')
        self.fields['subrecipe'].queryset = Recipe.objects.filter(
            recipe_type__in=['semi_finished', 'home']
        ).order_by('title')
        self.fields['cut_shape'].queryset = CutShape.objects.filter(is_active=True).order_by('sort_order')
        self.fields['override_cooking_method'].queryset = CookingMethod.objects.all().order_by('name')

    def clean(self):
        cleaned = super().clean()
        abs_ing = cleaned.get('abstract_ingredient')
        branded = cleaned.get('branded_ingredient')
        subrecipe = cleaned.get('subrecipe')

        sources = [abs_ing, branded, subrecipe]
        if not any(sources):
            raise forms.ValidationError(
                'Укажите абстрактный ингредиент, брендированный продукт или полуфабрикат'
            )
        if branded and subrecipe:
            raise forms.ValidationError(
                'Нельзя одновременно указать бренд и полуфабрикат'
            )
        if branded and abs_ing and branded.abstract_id != abs_ing.id:
            raise forms.ValidationError(
                'Брендированный продукт не соответствует абстрактному ингредиенту'
            )
        return cleaned


class RecipeFoodItemInline(admin.TabularInline):
    """Inline для домашних рецептов."""
    model = RecipeFoodItem
    form = RecipeFoodItemInlineForm
    fk_name = 'recipe'
    extra = 1
    fields = [
        'abstract_ingredient', 'branded_ingredient', 'subrecipe',
        'quantity', 'unit', 'cut_shape', 'override_cooking_method',
        'notes', 'is_scalable',
    ]
    show_change_link = True
    autocomplete_fields = ['abstract_ingredient', 'branded_ingredient', 'subrecipe', 'cut_shape',
                           'override_cooking_method']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'abstract_ingredient', 'branded_ingredient', 'subrecipe',
            'cut_shape', 'override_cooking_method',
        )


# ======================= ADMIN CLASSES =======================

class FoodTypeFilter(admin.SimpleListFilter):
    title = 'тип источника'
    parameter_name = 'food_type'

    def lookups(self, request, model_admin):
        return (
            ('abstract', '🔸 Абстрактный'),
            ('branded', '🏷️ Брендированный'),
            ('subrecipe', '🥣 Полуфабрикат'),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if v == 'abstract':
            return queryset.filter(
                abstract_ingredient__isnull=False,
                branded_ingredient__isnull=True,
                subrecipe__isnull=True,
            )
        if v == 'branded':
            return queryset.filter(branded_ingredient__isnull=False)
        if v == 'subrecipe':
            return queryset.filter(subrecipe__isnull=False)
        return queryset


@admin.register(RecipeFoodItem)
class RecipeFoodItemAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipe', 'get_food_name', 'get_food_type',
        'quantity', 'unit', 'cut_shape', 'get_weight_hint',
    ]
    list_filter = [FoodTypeFilter, 'unit', 'cut_shape']
    search_fields = [
        'recipe__title', 'abstract_ingredient__name',
        'branded_ingredient__product_name', 'subrecipe__title',
    ]
    autocomplete_fields = ['recipe', 'abstract_ingredient', 'branded_ingredient', 'subrecipe', 'cut_shape',
                           'override_cooking_method']

    fieldsets = (
        ('Рецепт', {'fields': ('recipe',)}),
        ('Источник', {
            'fields': ('abstract_ingredient', 'branded_ingredient', 'subrecipe'),
            'description': 'Укажите <b>абстрактный ингредиент</b>, опционально уточните <b>бренд</b> или <b>полуфабрикат</b>',
        }),
        ('Количество', {
            'fields': ('quantity', 'unit', 'is_scalable'),
        }),
        ('Обработка', {
            'fields': ('cut_shape', 'override_cooking_method'),
            'description': 'Форма нарезки и переопределение метода обработки',
        }),
        ('Примечание', {'fields': ('notes',)}),
    )

    @admin.display(description='Название')
    def get_food_name(self, obj):
        return obj.food_name

    @admin.display(description='Тип')
    def get_food_type(self, obj):
        type_map = {
            'abstract': '🔸 Абстрактный',
            'branded': '🏷️ Брендированный',
            'subrecipe': '🥣 Полуфабрикат',
            'unknown': '❓ —',
        }
        return type_map.get(obj.food_type, obj.food_type)

    @admin.display(description='Вес, г')
    def get_weight_hint(self, obj):
        """Приблизительный вес без учёта потерь и масла."""
        from kitchen.utils.nutrition import convert_to_grams
        try:
            grams = convert_to_grams(obj.quantity, obj.unit, obj.abstract_ingredient)
            return f"{grams:.1f}"
        except Exception:
            return '—'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'recipe', 'abstract_ingredient', 'branded_ingredient', 'subrecipe',
        )


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
        'get_calories_summary', 'total_weight',
        'created_at', 'ingredients_count', 'steps_count',
    ]

    list_filter = [
        RecipeTypeFilter,
        'is_saved_variant',
        'is_professional',
        'difficulty',
        'cuisine',
        'created_at',
        RecipeWithSubrecipeFilter,
    ]

    search_fields = ['title', 'description', 'author', 'ttk_code']

    readonly_fields = [
        'total_time',
        'calories', 'protein', 'fat', 'carbs',
        'calories_per_100g', 'protein_per_100g', 'fat_per_100g', 'carbs_per_100g',
        'total_weight',
        'nutrition_calculated_at',
        'created_at', 'updated_at', 'saved_at',
        'get_nutrition_summary',
    ]

    fieldsets = (
        ('Тип рецепта', {
            'fields': ('recipe_type', 'ttk_code'),
            'description': 'Выберите тип рецепта',
        }),
        ('Основная информация', {
            'fields': ('title', 'author', 'cuisine', 'description', 'difficulty', 'servings', 'is_professional'),
        }),
        ('Для ТТК (Технико-технологическая карта)', {
            'fields': (
                'technological_process',
                'quality_requirements',
                'yield_weight',
                'portion_size',
            ),
            'classes': ('collapse',),
            'description': 'Заполняется только для ТТК и полуфабрикатов',
        }),
        ('📊 Расчёт КБЖУ', {
            'fields': (
                'get_nutrition_summary',
                'total_weight',
                'nutrition_calculated_at',
            ),
            'description': (
                'КБЖУ рассчитывается автоматически из состава рецепта. '
                'Используйте действие «Пересчитать КБЖУ» в списке рецептов.'
            ),
        }),
        ('КБЖУ на порцию', {
            'fields': ('calories', 'protein', 'fat', 'carbs'),
            'classes': ('collapse',),
        }),
        ('КБЖУ на 100 г', {
            'fields': ('calories_per_100g', 'protein_per_100g', 'fat_per_100g', 'carbs_per_100g'),
            'classes': ('collapse',),
        }),
        ('Оформление и подача', {
            'fields': ('plating', 'plating_image'),
            'classes': ('wide',),
            'description': 'Рекомендации по оформлению и фото готового блюда',
        }),
        ('Условия и сроки хранения', {
            'fields': ('storage_conditions',),
            'classes': ('wide',),
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

    filter_horizontal = ['diet_tags', 'related_recipes', 'components']
    autocomplete_fields = ['cuisine', 'original_recipe']
    save_on_top = True
    actions = ['action_recalculate_nutrition']

    def get_inlines(self, request, obj):
        """Разные наборы инлайн-форм для разных типов рецептов."""
        base = [RecipeStepInline, ComponentInline]

        if obj and obj.recipe_type in ('ttk', 'semi_finished'):
            # ТТК и полуфабрикаты: профессиональные ингредиенты (брутто/нетто)
            return base + [ProfessionalIngredientInline]

        # Домашние рецепты: обычные ингредиенты
        return base + [RecipeFoodItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            ingredients_count=Count('food_items', distinct=True),
            steps_count=Count('steps', distinct=True),
        )

    # ==================== Отображаемые поля ====================

    @admin.display(description='Ингредиентов')
    def ingredients_count(self, obj):
        return obj.ingredients_count

    @admin.display(description='Шагов')
    def steps_count(self, obj):
        return obj.steps_count

    @admin.display(description='КБЖУ')
    def get_calories_summary(self, obj):
        if obj.calories is None or obj.calories == 0:
            return '—'
        return format_html(
            '<b>{} ккал</b> / порция',
            obj.calories,
        )

    @admin.display(description='Сводка по расчёту КБЖУ')
    def get_nutrition_summary(self, obj):
        if not obj or not obj.pk:
            return 'Сохраните рецепт, чтобы увидеть расчёт'

        if not obj.nutrition_calculated_at:
            return format_html(
                '<div style="padding: 10px; background: #fff3cd; border-radius: 6px;">'
                '⚠️ КБЖУ ещё не рассчитывалось. Используйте действие «Пересчитать КБЖУ» в списке рецептов.'
                '</div>'
            )

        items = obj.food_items.count()
        pro = obj.pro_ingredients.count()
        steps = obj.steps.count()

        # Форматируем числа ЗАРАНЕЕ, чтобы не передавать их в format_html
        calc_at = obj.nutrition_calculated_at.strftime('%d.%m.%Y %H:%M')
        calories = obj.calories or 0
        servings = obj.servings or 1
        total_weight = obj.total_weight or 0
        cal_100 = f"{(obj.calories_per_100g or 0):.1f}"
        prot_100 = f"{(obj.protein_per_100g or 0):.1f}"
        fat_100 = f"{(obj.fat_per_100g or 0):.1f}"
        carbs_100 = f"{(obj.carbs_per_100g or 0):.1f}"

        port_word = 'порция' if servings == 1 else ('порции' if 2 <= servings <= 4 else 'порций')

        return format_html(
            '<div style="padding: 12px; background: #d4edda; border-radius: 6px; line-height: 1.6;">'
            '<b>Последний пересчёт:</b> {}<br>'
            '<b>Ингредиентов (RecipeFoodItem):</b> {}<br>'
            '<b>Профессиональных ингредиентов:</b> {}<br>'
            '<b>Шагов:</b> {}<br>'
            '<b>Итог:</b> {} ккал на порцию ({} {})<br>'
            '<b>Всего веса:</b> {} г<br>'
            '<b>На 100 г:</b> {} ккал / Б {} / Ж {} / У {}'
            '</div>',
            calc_at,
            items,
            pro,
            steps,
            calories,
            servings,
            port_word,
            total_weight,
            cal_100,
            prot_100,
            fat_100,
            carbs_100,
        )

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
        return '—'

    # ==================== Действия ====================

    @admin.action(description='🔄 Пересчитать КБЖУ выбранных рецептов')
    def action_recalculate_nutrition(self, request, queryset):
        from kitchen.utils.nutrition import recalculate_recipe_nutrition

        success = 0
        errors = 0

        # Сначала полуфабрикаты (чтобы родители могли их использовать)
        order = {'semi_finished': 0, 'home': 1, 'ttk': 2}
        ordered = sorted(queryset, key=lambda r: order.get(r.recipe_type, 99))

        for recipe in ordered:
            try:
                recalculate_recipe_nutrition(recipe)
                success += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f'❌ {recipe.title}: {e}',
                    level='ERROR',
                )

        if success:
            self.message_user(
                request,
                f'✅ Пересчитано рецептов: {success}',
                level='SUCCESS',
            )
        if errors:
            self.message_user(
                request,
                f'⚠️ Ошибок: {errors}',
                level='WARNING',
            )

    def save_model(self, request, obj, form, change):
        if obj.recipe_type in ['ttk', 'semi_finished']:
            obj.is_professional = True
        super().save_model(request, obj, form, change)


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


# ======================= ПЕРЕСЧЁТ ЕДИНИЦ =======================

@admin.register(UnitConversion)
class UnitConversionAdmin(admin.ModelAdmin):
    list_display = [
        'get_target', 'from_unit', 'grams_per_unit',
        'system', 'conversion_type', 'is_active', 'note_short',
    ]
    list_filter = [
        'system', 'conversion_type', 'from_unit', 'is_active',
    ]
    search_fields = [
        'ingredient__name', 'category__name', 'note',
    ]
    autocomplete_fields = ['ingredient', 'category']
    list_editable = ['grams_per_unit', 'is_active']

    fieldsets = (
        ('Что пересчитываем', {
            'fields': ('ingredient', 'category'),
            'description': (
                'Укажите <b>либо ингредиент</b>, <b>либо категорию</b>, '
                'либо <b>ничего</b> (тогда правило общее). '
                'Нельзя указывать оба одновременно.'
            ),
        }),
        ('Правило', {
            'fields': ('from_unit', 'grams_per_unit', 'conversion_type', 'system'),
        }),
        ('Служебное', {
            'fields': ('note', 'is_active', 'created_at', 'updated_at'),
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='К чему применяется')
    def get_target(self, obj):
        if obj.ingredient:
            return f"🔸 {obj.ingredient.name}"
        if obj.category:
            return f"📁 {obj.category.full_hierarchy}"
        return "🌐 Общее правило"

    @admin.display(description='Примечание')
    def note_short(self, obj):
        if obj.note and len(obj.note) > 50:
            return obj.note[:50] + '…'
        return obj.note or '—'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ingredient', 'category', 'category__parent')


# ======================= ФОРМЫ НАРЕЗКИ =======================

@admin.register(CutShape)
class CutShapeAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = [
        'preview_icon', 'name', 'slug', 'factor',
        'dish_count', 'is_active', 'sort_order',
    ]
    list_display_links = ['preview_icon', 'name']
    list_filter = ['is_active']
    search_fields = ['name', 'slug', 'description', 'short_description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['factor', 'is_active', 'sort_order']
    filter_horizontal = ['typical_dishes']
    readonly_fields = ['created_at', 'updated_at', 'preview_image_large']

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'icon', 'factor', 'sort_order', 'is_active')
        }),
        ('Описание', {
            'fields': ('short_description', 'description'),
        }),
        ('Медиа', {
            'fields': ('image', 'video_url', 'preview_image_large'),
        }),
        ('Типичные блюда', {
            'fields': ('typical_dishes',),
            'classes': ('collapse',),
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Иконка')
    def preview_icon(self, obj):
        return format_html('<span style="font-size: 20px;">{}</span>', obj.icon or '—')

    @admin.display(description='Превью')
    def preview_image_large(self, obj):
        if obj.image and obj.image.url:
            return format_html(
                '<img src="{}" style="max-height: 200px; border-radius: 8px;" />',
                obj.image.url
            )
        return '—'

    @admin.display(description='Блюд')
    def dish_count(self, obj):
        return obj.typical_dishes.count()


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
            'fields': ('oil_absorption_rates', 'default_oil'),
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


class StepIngredientInline(admin.TabularInline):
    """Inline для ингредиентов внутри шага."""
    model = StepIngredient
    form = StepIngredientForm
    fk_name = 'step'
    extra = 1
    fields = [
        'order', 'food_item', 'preparation', 'cooking_method', 'cooking_note',
    ]
    autocomplete_fields = ['food_item', 'preparation', 'cooking_method']
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'food_item', 'preparation', 'cooking_method',
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Ограничиваем food_item ингредиентами того же рецепта."""
        if db_field.name == 'food_item':
            # Получаем step_id из URL или POST
            step_id = None
            if 'step_id' in request.resolver_match.kwargs:
                step_id = request.resolver_match.kwargs['step_id']
            elif request.resolver_match.kwargs.get('object_id'):
                # Если мы на странице шага
                from kitchen.models import RecipeStep
                step = RecipeStep.objects.filter(
                    pk=request.resolver_match.kwargs['object_id']
                ).first()
                if step:
                    step_id = step.pk

            if step_id:
                from kitchen.models import RecipeStep
                step = RecipeStep.objects.filter(pk=step_id).first()
                if step:
                    kwargs['queryset'] = RecipeFoodItem.objects.filter(
                        recipe=step.recipe
                    ).select_related('abstract_ingredient', 'branded_ingredient', 'subrecipe')
                else:
                    kwargs['queryset'] = RecipeFoodItem.objects.none()
            else:
                kwargs['queryset'] = RecipeFoodItem.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(RecipeStep)
class RecipeStepAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipe', 'order', 'title', 'duration',
        'step_ingredients_count',
    ]
    list_filter = ['recipe__recipe_type']
    search_fields = ['title', 'instruction', 'recipe__title']
    autocomplete_fields = ['recipe', 'subrecipe']
    filter_horizontal = ['recommended_utensils']
    inlines = [StepIngredientInline]
    save_on_top = True

    fieldsets = (
        ('Основное', {
            'fields': ('recipe', 'order', 'title', 'instruction'),
        }),
        ('Тайминг и температура', {
            'fields': ('duration', 'temperature'),
        }),
        ('Медиа', {
            'fields': ('recipe_step_image',),
        }),
        ('Вложенный рецепт (полуфабрикат)', {
            'fields': ('subrecipe', 'subrecipe_base_ingredient', 'subrecipe_base_quantity'),
            'classes': ('collapse',),
        }),
        ('Утварь', {
            'fields': ('recommended_utensils',),
        }),
    )

    @admin.display(description='Ингредиентов')
    def step_ingredients_count(self, obj):
        return obj.step_ingredients.count()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'recipe', 'subrecipe',
        ).prefetch_related('step_ingredients')


register_if_not_registered(RecipeStep, RecipeStepAdmin)

if not SKIP_BROKEN_ADMIN:
    class HomeIngredientAdmin(admin.ModelAdmin):
        list_display = ['recipe', 'ingredient', 'quantity', 'unit', 'is_scalable']
        list_filter = ['unit', 'is_scalable']
        search_fields = ['ingredient__name', 'recipe__title']
        autocomplete_fields = ['recipe', 'ingredient']


    register_if_not_registered(HomeIngredient, HomeIngredientAdmin)

if not SKIP_BROKEN_ADMIN:
    class IngredientSubstitutionAdmin(admin.ModelAdmin):
        list_display = ['recipe_ingredient', 'substitute_ingredient', 'ratio', 'substitute_unit']
        list_filter = ['substitute_unit']
        autocomplete_fields = ['recipe_ingredient', 'substitute_ingredient']


    register_if_not_registered(IngredientSubstitution, IngredientSubstitutionAdmin)



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