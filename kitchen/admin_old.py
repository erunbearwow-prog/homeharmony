from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db.models import F
from .models import (
    Cuisine, Diet, IngredientCategory, Ingredient,
    Recipe, RecipeStep, CookingMethod,
    IngredientPreparation, RecommendedUtensil, IngredientSubstitution,
    CookingMethodSubstitution, UtensilSubstitution, ProfessionalIngredient,
    Product, RecipeFoodItem,
    AbstractIngredient,  # <-- ДОБАВЛЕНО
    BrandedIngredient, RelationType, SemanticRelation,  # <-- ДОБАВЛЕНО
    HomeIngredient, SemanticTag,
)
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.admin.widgets import FilteredSelectMultiple


#======================= БАЗОВЫЕ РЕГИСТРАЦИИ =======================
class IngredientSubstitutionInline(admin.TabularInline):
    model = IngredientSubstitution
    extra = 1
    fields = ['substitute_ingredient', 'substitute_unit', 'ratio', 'notes']
    autocomplete_fields = ['substitute_ingredient']
    verbose_name = '✅ Замена'
    verbose_name_plural = '✅ Возможные замены (прямо в этом рецепте)'
    classes = ['collapse']


@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'region', 'created_at']
    list_filter = ['parent', 'region']
    search_fields = ['name', 'region', 'description']
    list_editable = ['region']
    readonly_fields = ['slug']


@admin.register(Diet)
class DietAdmin(admin.ModelAdmin):
    list_display = ['name', 'authority', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['allowed_ingredients', 'prohibited_ingredients']


@admin.register(HomeIngredient)
class HomeIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'quantity', 'unit']
    list_filter = ['unit', 'is_scalable']
    search_fields = ['recipe__title', 'ingredient__name']
    autocomplete_fields = ['recipe', 'ingredient']
    inlines = [IngredientSubstitutionInline]


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


class RecipeStepForm(forms.ModelForm):
    class Meta:
        model = RecipeStep
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'subrecipe_base_ingredient' in self.fields:
            subrecipe_id = None

            if self.data and self.data.get('subrecipe'):
                try:
                    subrecipe_id = int(self.data.get('subrecipe'))
                except (ValueError, TypeError):
                    pass

            if not subrecipe_id and self.instance and self.instance.pk:
                subrecipe_id = self.instance.subrecipe_id

            if not subrecipe_id and self.initial.get('subrecipe'):
                subrecipe_id = self.initial.get('subrecipe')

            if subrecipe_id:
                # ИСПРАВЛЕНО: RecipeIngredient → HomeIngredient
                self.fields['subrecipe_base_ingredient'].queryset = HomeIngredient.objects.filter(
                    recipe_id=subrecipe_id
                ).select_related('ingredient')
            else:
                self.fields['subrecipe_base_ingredient'].queryset = HomeIngredient.objects.none()


class RecipeStepInline(admin.StackedInline):
    model = RecipeStep
    form = RecipeStepForm
    fk_name = 'recipe'
    extra = 1
    ordering = ['order']
    classes = ['collapse']

    fieldsets = [
        ('Номер и описание', {
            'fields': ['order', 'title', 'instruction', 'duration', 'temperature', 'recipe_step_image'],
            'classes': ['collapse'],
        }),
        ('Метод и подготовка', {
            'fields': ['cooking_method', 'ingredient_preparation'],
            'classes': ['collapse'],
        }),
        ('Время и температура', {
            'fields': ['duration', 'temperature'],
            'classes': ['collapse'],
        }),
        ('Утварь', {
            'fields': ['recommended_utensils'],
            'classes': ['collapse'],
        }),
        ('Вложенный рецепт', {
            'fields': ['subrecipe', 'subrecipe_base_ingredient', 'subrecipe_base_quantity'],
            'classes': ['collapse'],
        }),
    ]

    autocomplete_fields = ['subrecipe', 'cooking_method', 'ingredient_preparation']
    filter_horizontal = ['recommended_utensils']
    verbose_name = 'Шаг приготовления'
    verbose_name_plural = 'Шаги приготовления'


class RecipeFoodItemForm(forms.ModelForm):
    """Форма для выбора ингредиента или продукта"""

    class Meta:
        model = RecipeFoodItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем оба поля, но один будет скрыт через JS
        self.fields['ingredient'].queryset = Ingredient.objects.all().order_by('name_normalized')
        self.fields['product'].queryset = Product.objects.all().order_by('name')
        self.fields['ingredient'].widget.attrs['class'] = 'ingredient-select'
        self.fields['product'].widget.attrs['class'] = 'product-select'
        self.fields['unit'].widget.attrs['style'] = 'width: 100px;'


class RecipeFoodItemInline(admin.TabularInline):
    """Inline для добавления ингредиентов/продуктов в рецепт"""
    model = RecipeFoodItem
    form = RecipeFoodItemForm
    extra = 1
    fields = ['ingredient', 'product', 'quantity', 'unit', 'notes', 'is_scalable']
    verbose_name = "Ингредиент / продукт"
    verbose_name_plural = "Ингредиенты и продукты"
    classes = ['collapse']

    class Media:
        css = {
            'all': ('admin/css/food_item.css',)
        }


# ======================= ОСНОВНАЯ РЕГИСТРАЦИЯ RECIPE =======================

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ['title', 'cuisine', 'difficulty', 'servings', 'created_at']
    list_filter = ['cuisine', 'difficulty', 'is_professional', 'created_at', 'updated_at']
    search_fields = ['title', 'description', 'author']
    filter_horizontal = ['diet_tags', 'related_recipes']
    date_hierarchy = 'created_at'
    readonly_fields = ['total_time']

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

    def get_inlines(self, request, obj=None):
        """Динамически подставляем inline в зависимости от is_professional"""
        if obj and obj.is_professional:
            return [RecipeStepInline, ProfessionalIngredientInline]
        return [RecipeStepInline, RecipeFoodItemInline]

    def recipe_type_badge(self, obj):
        """Отображаем красивый бейдж в списке рецептов"""
        if obj.is_professional:
            return format_html(
                '<span style="background:#d97706; color:white; padding:2px 8px; border-radius:12px; font-size:11px;">📋 ТТК</span>')
        return format_html(
            '<span style="background:#10b981; color:white; padding:2px 8px; border-radius:12px; font-size:11px;">🍳 Рецепт</span>')

    recipe_type_badge.short_description = 'Тип'
    recipe_type_badge.admin_order_field = 'is_professional'


# ======================= ОСТАЛЬНЫЕ РЕГИСТРАЦИИ =======================


@admin.register(RecipeStep)
class RecipeStepAdmin(admin.ModelAdmin):
    list_display = ['order', 'title', 'recipe', 'duration']
    list_filter = ['recipe']
    search_fields = ['title', 'instruction']
    autocomplete_fields = ['recipe', 'subrecipe']


@admin.register(CookingMethod)
class CookingMethodAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'code',
        'difficulty_badge',
        'is_heat_treatment',
        'can_cook_with_children',
        'sort_order'
    ]
    list_filter = ['is_heat_treatment', 'difficulty', 'can_cook_with_children']
    search_fields = ['name', 'code', 'description']
    list_editable = ['sort_order']

    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'code', 'description', 'is_heat_treatment', 'sort_order']
        }),
        ('Для начинающих', {
            'fields': [
                'difficulty',
                'can_cook_with_children',
                'child_friendly_notes',
                'beginner_tips'
            ],
            'classes': ('collapse',)
        }),
        ('Подробное руководство', {
            'fields': [
                'step_by_step_guide',
                'tips',
                'common_mistakes'
            ],
            'classes': ('collapse',)
        }),
        ('Научная база', {
            'fields': ['scientific_background', 'advanced_notes'],
            'classes': ('collapse',)
        }),
        ('Параметры приготовления', {
            'fields': [
                'recommended_temperature_min',
                'recommended_temperature_max',
                'breading_type'
            ],
            'classes': ('collapse',)
        }),
        ('Коэффициенты', {
            'fields': ['oil_absorption_rates', 'cut_shape_factors'],
            'classes': ('collapse',)
        }),
        ('Визуал', {
            'fields': ['icon', 'image', 'video_url'],
            'classes': ('collapse',)
        }),
        ('Связи', {
            'fields': ['best_ingredients'],
            'classes': ('collapse',)
        }),
    ]

    def difficulty_badge(self, obj):
        """Отображает сложность в виде бейджа"""
        colors = {
            'easy': '🟢',
            'medium': '🟡',
            'hard': '🔴',
        }
        labels = {
            'easy': 'Простая',
            'medium': 'Средняя',
            'hard': 'Сложная',
        }
        return f"{colors.get(obj.difficulty, '⚪')} {labels.get(obj.difficulty, 'Не указана')}"

    difficulty_badge.short_description = 'Сложность'


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


# ======================= ФОРМА ДЛЯ КАТЕГОРИЙ (иерархический выбор родителя) =======================
class CategoryForm(forms.ModelForm):
    """Форма для категорий с иерархическим выбором родителя"""

    class Meta:
        model = IngredientCategory
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def build_tree(parent=None, level=0, prefix=""):
            options = []
            children = IngredientCategory.objects.filter(parent=parent).order_by('name')
            for i, child in enumerate(children):
                if self.instance and self.instance.pk == child.pk:
                    continue
                is_last = (i == len(children) - 1)
                connector = "└── " if is_last else "├── "
                display_name = f"{prefix}{connector}{child.name}"
                options.append((child.id, display_name))
                next_prefix = prefix + ("    " if is_last else "│   ")
                options.extend(build_tree(child, level + 1, next_prefix))
            return options

        tree_options = build_tree()
        choices = [(None, "--------- (корневая категория)")]
        choices.extend(tree_options)

        self.fields['parent'].choices = choices
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = None

        if self.instance and self.instance.pk and self.instance.parent:
            self.fields['parent'].initial = self.instance.parent.id


# ======================= ФОРМА ДЛЯ ИНГРЕДИЕНТОВ (трехуровневый выбор) =======================
class IngredientCategorySelectForm(forms.ModelForm):
    """Форма для Ingredient с трехуровневым выбором категории"""

    category_level_1 = forms.ModelChoiceField(
        queryset=IngredientCategory.objects.filter(parent__isnull=True).order_by('name'),
        required=False,
        label='Категория 1-го уровня'
    )
    category_level_2 = forms.ModelChoiceField(
        queryset=IngredientCategory.objects.none(),
        required=False,
        label='Категория 2-го уровня'
    )
    category_level_3 = forms.ModelChoiceField(
        queryset=IngredientCategory.objects.none(),
        required=False,
        label='Категория 3-го уровня'
    )

    class Meta:
        model = Ingredient
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_categories()

    def _setup_categories(self):
        current_category = None
        if self.instance and self.instance.pk and self.instance.abstract:
            current_category = self.instance.abstract.category

        if current_category:
            level = current_category.level
            if level == 0:
                self.fields['category_level_1'].initial = current_category
                self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                    parent=current_category
                ).order_by('name')
            elif level == 1:
                self.fields['category_level_1'].initial = current_category.parent
                self.fields['category_level_2'].initial = current_category
                self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                    parent=current_category.parent
                ).order_by('name')
                self.fields['category_level_3'].queryset = IngredientCategory.objects.filter(
                    parent=current_category
                ).order_by('name')
            elif level == 2:
                root = current_category.root_parent
                second = current_category.second_level_parent
                self.fields['category_level_1'].initial = root
                self.fields['category_level_2'].initial = second
                self.fields['category_level_3'].initial = current_category
                self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                    parent=root
                ).order_by('name')
                self.fields['category_level_3'].queryset = IngredientCategory.objects.filter(
                    parent=second
                ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()

        level_1 = cleaned_data.get('category_level_1')
        level_2 = cleaned_data.get('category_level_2')
        level_3 = cleaned_data.get('category_level_3')

        if level_1:
            self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                parent=level_1
            ).order_by('name')
        else:
            self.fields['category_level_2'].queryset = IngredientCategory.objects.none()

        if level_2:
            self.fields['category_level_3'].queryset = IngredientCategory.objects.filter(
                parent=level_2
            ).order_by('name')
        else:
            self.fields['category_level_3'].queryset = IngredientCategory.objects.none()

        if level_3:
            cleaned_data['selected_category'] = level_3
        elif level_2:
            cleaned_data['selected_category'] = level_2
        elif level_1:
            cleaned_data['selected_category'] = level_1
        else:
            cleaned_data['selected_category'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected_category = self.cleaned_data.get('selected_category')

        if instance.abstract:
            instance.abstract.category = selected_category
            if commit:
                instance.abstract.save()
        else:
            abstract = AbstractIngredient.objects.create(
                name=instance.name,
                category=selected_category,
                data_source=instance.data_source or 'manual',
            )
            instance.abstract = abstract

        if commit:
            instance.save()
            self.save_m2m()

        return instance


# ======================= ФОРМА ДЛЯ ABSTRACTINGREDIENT =======================
class AbstractIngredientCategoryForm(forms.ModelForm):
    """Форма для AbstractIngredient с трехуровневым выбором категории"""

    category_level_1 = forms.ModelChoiceField(
        queryset=IngredientCategory.objects.filter(parent__isnull=True).order_by('name'),
        required=False,
        label='Категория 1-го уровня'
    )
    category_level_2 = forms.ModelChoiceField(
        queryset=IngredientCategory.objects.none(),
        required=False,
        label='Категория 2-го уровня'
    )
    category_level_3 = forms.ModelChoiceField(
        queryset=IngredientCategory.objects.none(),
        required=False,
        label='Категория 3-го уровня'
    )

    class Meta:
        model = AbstractIngredient
        fields = '__all__'
        exclude = ['category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_categories()

        if self.is_bound and 'category_level_1' in self.data:
            level_1_id = self.data.get('category_level_1')
            if level_1_id:
                try:
                    level_1 = IngredientCategory.objects.get(id=level_1_id)
                    self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                        parent=level_1
                    ).order_by('name')
                except (ValueError, IngredientCategory.DoesNotExist):
                    pass

            level_2_id = self.data.get('category_level_2')
            if level_2_id:
                try:
                    level_2 = IngredientCategory.objects.get(id=level_2_id)
                    self.fields['category_level_3'].queryset = IngredientCategory.objects.filter(
                        parent=level_2
                    ).order_by('name')
                except (ValueError, IngredientCategory.DoesNotExist):
                    pass

    def _setup_categories(self):
        current_category = None
        if self.instance and self.instance.pk:
            current_category = self.instance.category

        if current_category:
            level = current_category.level
            if level == 0:
                self.fields['category_level_1'].initial = current_category
                self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                    parent=current_category
                ).order_by('name')
            elif level == 1:
                self.fields['category_level_1'].initial = current_category.parent
                self.fields['category_level_2'].initial = current_category
                self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                    parent=current_category.parent
                ).order_by('name')
                self.fields['category_level_3'].queryset = IngredientCategory.objects.filter(
                    parent=current_category
                ).order_by('name')
            elif level == 2:
                root = current_category.root_parent
                second = current_category.second_level_parent
                self.fields['category_level_1'].initial = root
                self.fields['category_level_2'].initial = second
                self.fields['category_level_3'].initial = current_category
                self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                    parent=root
                ).order_by('name')
                self.fields['category_level_3'].queryset = IngredientCategory.objects.filter(
                    parent=second
                ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()

        level_1 = cleaned_data.get('category_level_1')
        level_2 = cleaned_data.get('category_level_2')
        level_3 = cleaned_data.get('category_level_3')

        if level_3:
            cleaned_data['selected_category'] = level_3
        elif level_2:
            cleaned_data['selected_category'] = level_2
        elif level_1:
            cleaned_data['selected_category'] = level_1
        else:
            cleaned_data['selected_category'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.category = self.cleaned_data.get('selected_category')

        if commit:
            instance.save()
            self.save_m2m()
        return instance


# ======================= РЕГИСТРАЦИЯ КАТЕГОРИЙ =======================
@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display_links = ['name', 'parent']
    list_editable = ['sort_order']
    list_filter = ['parent']
    search_fields = ['name']
    list_per_page = 100
    ordering = ['name']

    def get_queryset(self, request):
        """Сортируем категории по иерархии"""
        qs = super().get_queryset(request)
        # Сортируем по родителю и имени
        return qs.order_by('parent__name', 'name')

    def name_with_parent(self, obj):
        """Отображаем категорию с родителем в списке"""
        if obj.parent:
            return f"{obj.parent.name} → {obj.name}"
        return obj.name

    name_with_parent.short_description = 'Категория'
    name_with_parent.admin_order_field = 'name'

    list_display = ['name', 'parent', 'sort_order']


    actions = ['bulk_assign_parent']

    def bulk_assign_parent(self, request, queryset):
        """Массовое назначение родительской категории"""
        from django.shortcuts import render
        from django.http import HttpResponseRedirect

        # ШАГ 1: Это форма подтверждения (пришла с выбором родителя)
        if request.method == 'POST' and request.POST.get('parent_id'):
            parent_id = request.POST.get('parent_id')

            if parent_id and parent_id.isdigit():
                try:
                    parent = IngredientCategory.objects.get(id=int(parent_id))

                    # Проверка на циклическую зависимость
                    for category in queryset:
                        if category.id == parent.id:
                            self.message_user(
                                request,
                                f'❌ Нельзя назначить категорию "{category.name}" родителем самой себя!',
                                level='ERROR'
                            )
                            return HttpResponseRedirect(request.get_full_path())

                    # Обновляем
                    count = 0
                    for category in queryset:
                        category.parent = parent
                        category.save(update_fields=['parent'])
                        count += 1

                    self.message_user(
                        request,
                        f'✅ Родительская категория "{parent.name}" назначена для {count} категорий'
                    )
                    return HttpResponseRedirect(request.get_full_path())

                except IngredientCategory.DoesNotExist:
                    self.message_user(request, '❌ Выбранная категория не найдена', level='ERROR')
                    return HttpResponseRedirect(request.get_full_path())
            else:
                self.message_user(request, '❌ Пожалуйста, выберите родительскую категорию', level='ERROR')
                return HttpResponseRedirect(request.get_full_path())

        # ШАГ 2: Показываем форму выбора родителя (первый шаг)
        def build_category_tree(parent=None, level=0):
            options = []
            children = IngredientCategory.objects.filter(parent=parent).order_by('name')
            for cat in children:
                if cat in queryset:
                    continue
                indent = '—' * level
                options.append({
                    'id': cat.id,
                    'name': f"{indent} {cat.name}" if level > 0 else cat.name,
                    'level': level
                })
                options.extend(build_category_tree(cat, level + 1))
            return options

        category_tree = build_category_tree()

        # Получаем ID выбранных объектов из POST
        selected_ids = request.POST.getlist('_selected_action')

        context = {
            'queryset': queryset,
            'categories': category_tree,
            'selected_ids': selected_ids,
            'title': 'Назначить родительскую категорию',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }

        return render(request, 'admin/kitchen/ingredientcategory/bulk_assign_parent.html', context)

    bulk_assign_parent.short_description = "Назначить родительскую категорию"

# ======================= РЕГИСТРАЦИЯ АБСТРАКТНЫХ ИНГРЕДИЕНТОВ =======================
@admin.register(AbstractIngredient)
class AbstractIngredientAdmin(admin.ModelAdmin):
    form = AbstractIngredientCategoryForm
    list_per_page = 30
    save_on_top = True

    # ❌ Убираем filter_horizontal — он не работает с related_name
    # filter_horizontal = ['semantic_tags']

    list_display = [
        'name',
        'category_display',
        'tags_display',
        'calories_display',
        'protein_display',
        'fat_display',
        'carbohydrates_display',
        'is_active'
    ]

    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['name']

    fieldsets = (
        ('Категория', {
            'fields': ('category_level_1', 'category_level_2', 'category_level_3'),
            'description': 'Выберите категорию ингредиента (три уровня вложенности)'
        }),
        ('Основное', {
            'fields': ('name', 'description', 'description_ru')
        }),
        ('КБЖУ', {
            'fields': ('calories', 'protein', 'fat', 'carbohydrates'),
            'classes': ('collapse',)
        }),
        ('Дополнительные нутриенты', {
            'fields': ('fiber', 'sugar', 'water', 'ash', 'starch'),
            'classes': ('collapse',)
        }),
        ('Витамины', {
            'fields': ('vitamin_a', 'beta_carotene', 'vitamin_b1', 'vitamin_b2',
                       'vitamin_b3', 'vitamin_b4', 'vitamin_b5', 'vitamin_b6',
                       'vitamin_b7', 'vitamin_b9_folate', 'vitamin_b12',
                       'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k'),
            'classes': ('collapse',)
        }),
        ('Минералы', {
            'fields': ('potassium', 'calcium', 'magnesium', 'sodium', 'phosphorus',
                       'iron', 'manganese', 'copper', 'selenium', 'zinc'),
            'classes': ('collapse',)
        }),
        ('Жирные кислоты', {
            'fields': ('saturated_fat', 'trans_fat', 'cholesterol', 'omega_3', 'omega_6'),
            'classes': ('collapse',)
        }),
        ('Изображение и источник', {
            'fields': ('image', 'data_source', 'fdc_id', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Служебное', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # ✅ Определяем методы для list_display
    def category_display(self, obj):
        return obj.category.name if obj.category else '-'
    category_display.short_description = 'Категория'
    category_display.admin_order_field = 'category__name'

    def tags_display(self, obj):
        """Отображение семантических тегов в списке"""
        tags = obj.semantic_tags.all()
        if tags:
            return ", ".join([tag.name for tag in tags[:5]]) + ("..." if tags.count() > 5 else "")
        return "-"
    tags_display.short_description = 'Теги'

    def calories_display(self, obj):
        return obj.calories if obj.calories is not None else '-'
    calories_display.short_description = 'Калории, ккал'

    def protein_display(self, obj):
        return obj.protein if obj.protein is not None else '-'
    protein_display.short_description = 'Белки, г'

    def fat_display(self, obj):
        return obj.fat if obj.fat is not None else '-'
    fat_display.short_description = 'Жиры, г'

    def carbohydrates_display(self, obj):
        return obj.carbohydrates if obj.carbohydrates is not None else '-'
    carbohydrates_display.short_description = 'Углеводы, г'

    actions = ['bulk_assign_category']

    def bulk_assign_category(self, request, queryset):
        # ... ваш код
        pass

    class Media:
        js = ['admin/js/category_chain.js']
        css = {
            'all': ('admin/css/category_select.css',)
        }


# ======================= РЕГИСТРАЦИЯ БРЕНДИРОВАННЫХ ПРОДУКТОВ =======================
@admin.register(BrandedIngredient)
class BrandedIngredientAdmin(admin.ModelAdmin):
    list_display = [
        'brand',
        'product_name',
        'abstract',
        'price',
        'weight',
        'price_per_100g',  # <-- оставляем здесь (это метод)
        'store',
        'is_available'
    ]
    list_filter = ['brand', 'store', 'is_available']
    search_fields = ['brand', 'product_name', 'barcode']
    autocomplete_fields = ['abstract']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Связь с абстрактным ингредиентом', {
            'fields': ('abstract',)
        }),
        ('Основная информация', {
            'fields': ('brand', 'product_name', 'barcode')
        }),
        ('КБЖУ (если отличается)', {
            'fields': ('calories', 'protein', 'fat', 'carbohydrates'),
            'classes': ('collapse',)
        }),
        ('Цена и вес', {
            'fields': ('price', 'weight'),  # <-- убрали price_per_100g и price_per_kg
        }),
        ('Магазин', {
            'fields': ('store', 'store_url', 'is_available', 'last_checked')
        }),
        ('Служебная информация', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def price_per_100g(self, obj):
        """Цена за 100 грамм"""
        if obj.price_per_100g:
            return f"{obj.price_per_100g:.2f} руб."
        return "-"
    price_per_100g.short_description = 'Цена за 100г'

    def price_per_kg(self, obj):
        """Цена за 1 кг"""
        if obj.price_per_kg:
            return f"{obj.price_per_kg:.2f} руб."
        return "-"
    price_per_kg.short_description = 'Цена за 1 кг'


# ======================= РЕГИСТРАЦИЯ ИНГРЕДИЕНТОВ =======================
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    form = IngredientCategorySelectForm
    list_per_page = 30
    save_on_top = True

    list_display = [
        'name',
        'category_display',
        'calories_display',
        'protein_display',
        'fat_display',
        'carbohydrates_display',
        'fiber',
        'sugar',
        'relations_count',
        'is_common'
    ]

    list_filter = [
        'abstract__category',
        'is_semi_finished',
        'branded__store',
    ]

    search_fields = ['name', 'abstract__name', 'branded__brand', 'branded__product_name']
    readonly_fields = ['id']
    ordering = ['name_normalized']

    # Убираем category_level_* из fieldsets
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'abstract', 'branded')
        }),
        ('Пользовательские корректировки', {
            'fields': ('custom_calories', 'custom_protein', 'custom_fat', 'custom_carbohydrates'),
            'classes': ('collapse',)
        }),
        ('Жиры и холестерин', {
            'fields': ('saturated_fat', 'trans_fat', 'cholesterol'),
            'classes': ('collapse',)
        }),
        ('Витамины', {
            'fields': ('vitamin_a', 'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b6',
                       'vitamin_b9', 'vitamin_b12', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k'),
            'classes': ('collapse',)
        }),
        ('Минералы', {
            'fields': ('calcium', 'iron', 'magnesium', 'phosphorus', 'potassium', 'sodium',
                       'zinc', 'copper', 'manganese', 'selenium'),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('water', 'ash', 'data_source'),
            'classes': ('collapse',)
        }),
    )

    # Поля category_level_* добавляются через форму (IngredientCategoryForm)
    # Они НЕ ДОЛЖНЫ быть в fieldsets

    def calories_display(self, obj):
        return obj.calories if obj.calories is not None else '-'
    calories_display.short_description = 'Калории, ккал'
    calories_display.admin_order_field = 'abstract__calories'

    def protein_display(self, obj):
        return obj.protein if obj.protein is not None else '-'
    protein_display.short_description = 'Белки, г'
    protein_display.admin_order_field = 'abstract__protein'

    def fat_display(self, obj):
        return obj.fat if obj.fat is not None else '-'
    fat_display.short_description = 'Жиры, г'
    fat_display.admin_order_field = 'abstract__fat'

    def carbohydrates_display(self, obj):
        return obj.carbohydrates if obj.carbohydrates is not None else '-'
    carbohydrates_display.short_description = 'Углеводы, г'
    carbohydrates_display.admin_order_field = 'abstract__carbohydrates'

    def category_display(self, obj):
        if obj.abstract and obj.abstract.category:
            return obj.abstract.category.name
        return '-'
    category_display.short_description = 'Категория'
    category_display.admin_order_field = 'abstract__category__name'

    # actions = ['bulk_assign_category']

    def bulk_assign_category(self, request, queryset):
        """Массовое назначение категории выбранным ингредиентам"""
        from django.shortcuts import render
        from django.http import HttpResponseRedirect

        if request.method == 'POST' and 'apply' in request.POST:
            category_id = request.POST.get('category_id')

            if category_id:
                try:
                    category = IngredientCategory.objects.get(id=category_id)
                    updated = 0
                    for ingredient in queryset:
                        if ingredient.abstract:
                            ingredient.abstract.category = category
                            ingredient.abstract.save()
                            updated += 1
                        else:
                            from .models import AbstractIngredient
                            abstract = AbstractIngredient.objects.create(
                                name=ingredient.name,
                                category=category,
                                data_source=ingredient.data_source,
                            )
                            ingredient.abstract = abstract
                            ingredient.save()
                            updated += 1

                    self.message_user(request, f'Категория "{category}" назначена {updated} ингредиентам')
                    return HttpResponseRedirect(request.get_full_path())
                except IngredientCategory.DoesNotExist:
                    self.message_user(request, 'Выбранная категория не найдена', level='ERROR')
                    return HttpResponseRedirect(request.get_full_path())
            else:
                self.message_user(request, 'Пожалуйста, выберите категорию', level='ERROR')
                return HttpResponseRedirect(request.get_full_path())

        all_categories = IngredientCategory.objects.all()

        return render(request, 'admin/kitchen/ingredient/bulk_assign_category.html', {
            'queryset': queryset,
            'categories': all_categories,
            'title': 'Массовое назначение категории ингредиентам'
        })

    bulk_assign_category.short_description = "Назначить категорию выбранным ингредиентам"

    class Media:
        js = ['admin/js/category_chain.js']
        css = {
            'all': ('admin/css/category_select.css',)
        }

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Добавляем кнопки навигации в контекст"""
        if object_id:
            extra_context = extra_context or {}
            current = Ingredient.objects.select_related('abstract', 'branded').get(id=object_id)

            next_ingredient = Ingredient.objects.filter(id__gt=current.id).order_by('id').first()
            prev_ingredient = Ingredient.objects.filter(id__lt=current.id).order_by('-id').first()

            extra_context['next_ingredient'] = next_ingredient
            extra_context['prev_ingredient'] = prev_ingredient
            extra_context['current_id'] = int(object_id)
            extra_context['total_count'] = Ingredient.objects.count()
            extra_context['current_index'] = Ingredient.objects.filter(id__lte=current.id).count()

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def relations_count(self, obj):
        """Количество семантических связей у ингредиента"""
        if obj.abstract:
            count = SemanticRelation.objects.filter(
                from_category=obj.abstract.category
            ).count()
            return count
        return 0

    relations_count.short_description = 'Связей'


# ======================= РЕГИСТРАЦИЯ ПРОДУКТОВ =======================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'nutriscore_grade', 'nova_group']
    list_filter = ['nutriscore_grade', 'nova_group']
    search_fields = ['name', 'brand', 'code']
    fieldsets = (
        ('Основная информация', {'fields': ('code', 'name', 'brand', 'quantity')}),
        ('Состав', {'fields': ('categories', 'ingredients_text', 'countries_tags')}),
        ('Оценки', {'fields': ('nutriscore_grade', 'nova_group', 'image')}),
    )


#================================= семантические связи ===============================
@admin.register(RelationType)
class RelationTypeAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'reverse_name', 'slug', 'is_symmetric', 'order']
    list_filter = ['is_symmetric']
    search_fields = ['name', 'reverse_name', 'slug', 'description']
    list_editable = ['order']
    list_display_links = ['icon', 'name']
    ordering = ['order', 'name']
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'reverse_name', 'description')
        }),
        ('Визуал', {
            'fields': ('icon', 'color')
        }),
        ('Настройки', {
            'fields': ('is_symmetric', 'order')
        }),
    )

# kitchen/admin.py

@admin.register(SemanticRelation)
class SemanticRelationAdmin(admin.ModelAdmin):
    list_display = [
        'from_display',
        'relation_type_display',
        'to_display',
        'weight',
        'created_at'
    ]
    list_filter = ['relation_type', 'created_at']
    search_fields = [
        'from_category__name', 'to_category__name',
        'from_tag__name', 'to_tag__name',
        'from_method__name', 'to_method__name',
        'from_utensil__name', 'to_utensil__name',
        'from_cuisine__name', 'to_cuisine__name',  # ← НОВОЕ!
        'notes'
    ]
    autocomplete_fields = [
        'from_category', 'to_category',
        'from_tag', 'to_tag',
        'from_method', 'to_method',
        'from_utensil', 'to_utensil',
        'from_cuisine', 'to_cuisine'  # ← НОВОЕ!
    ]
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = (
        ('От (источник)', {
            'fields': (
                ('from_category', 'from_tag', 'from_method', 'from_utensil', 'from_cuisine'),  # ← НОВОЕ!
            )
        }),
        ('К (цель)', {
            'fields': (
                ('to_category', 'to_tag', 'to_method', 'to_utensil', 'to_cuisine'),  # ← НОВОЕ!
            )
        }),
        ('Тип связи', {
            'fields': ('relation_type',)
        }),
        ('Дополнительно', {
            'fields': ('weight', 'order', 'notes')
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def from_display(self, obj):
        if obj.from_category:
            return f"📁 {obj.from_category.name}"
        if obj.from_tag:
            return f"🏷️ {obj.from_tag.name}"
        if obj.from_method:
            return f"🍳 {obj.from_method.name}"
        if obj.from_utensil:
            return f"🔧 {obj.from_utensil.name}"
        if obj.from_cuisine:  # ← НОВОЕ!
            return f"🌍 {obj.from_cuisine.name}"
        return "-"
    from_display.short_description = 'От'

    def to_display(self, obj):
        if obj.to_category:
            return f"📁 {obj.to_category.name}"
        if obj.to_tag:
            return f"🏷️ {obj.to_tag.name}"
        if obj.to_method:
            return f"🍳 {obj.to_method.name}"
        if obj.to_utensil:
            return f"🔧 {obj.to_utensil.name}"
        if obj.to_cuisine:  # ← НОВОЕ!
            return f"🌍 {obj.to_cuisine.name}"
        return "-"
    to_display.short_description = 'К'

    def relation_type_display(self, obj):
        return f"{obj.relation_type.icon} {obj.relation_type.name}"
    relation_type_display.short_description = 'Тип связи'


@admin.register(SemanticTag)
class SemanticTagAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'tag_type',
        'icon',
        'sort_order',
        'is_active',
        'ingredient_count'
    ]
    list_filter = ['tag_type', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['sort_order', 'is_active']
    ordering = ['tag_type', 'name']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['ingredients']
    readonly_fields = ['ingredient_count']

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'tag_type', 'icon', 'color')
        }),
        ('Описание', {
            'fields': ('description',)
        }),
        ('Связи', {
            'fields': ('ingredients',)
        }),
        ('Настройки', {
            'fields': ('sort_order', 'is_active')
        }),
        ('Служебное', {
            'fields': ('ingredient_count',),
            'classes': ('collapse',)
        }),
    )

    def ingredient_count(self, obj):
        """Количество связанных ингредиентов"""
        return obj.ingredient_count

    ingredient_count.short_description = 'Ингредиентов'