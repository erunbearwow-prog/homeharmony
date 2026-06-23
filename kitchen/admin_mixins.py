# admin_mixins.py (создайте новый файл в папке kitchen)

from django import forms
from .models import IngredientCategory


class CategoryLevelMixin:
    """Миксин для трехуровневого выбора категории"""

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Получаем текущую категорию
        current_category = None
        if self.instance and self.instance.pk:
            if hasattr(self.instance, 'category'):
                current_category = self.instance.category
            elif hasattr(self.instance, 'abstract') and self.instance.abstract:
                current_category = self.instance.abstract.category

        if current_category:
            self._setup_category_fields(current_category)
        else:
            self.fields['category_level_2'].queryset = IngredientCategory.objects.none()
            self.fields['category_level_3'].queryset = IngredientCategory.objects.none()

        # Динамическая загрузка при POST
        if self.is_bound:
            self._handle_bound_data()

    def _setup_category_fields(self, category):
        """Настраивает поля в зависимости от уровня категории"""
        if category.level == 0:
            self.fields['category_level_1'].initial = category
            self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                parent=category
            ).order_by('name')
        elif category.level == 1:
            self.fields['category_level_1'].initial = category.parent
            self.fields['category_level_2'].initial = category
            self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                parent=category.parent
            ).order_by('name')
            self.fields['category_level_3'].queryset = IngredientCategory.objects.filter(
                parent=category
            ).order_by('name')
        elif category.level == 2:
            root = category.root_parent
            second = category.second_level_parent
            self.fields['category_level_1'].initial = root
            self.fields['category_level_2'].initial = second
            self.fields['category_level_3'].initial = category
            self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                parent=root
            ).order_by('name')
            self.fields['category_level_3'].queryset = IngredientCategory.objects.filter(
                parent=second
            ).order_by('name')

    def _handle_bound_data(self):
        """Обрабатывает данные POST для динамической загрузки"""
        if 'category_level_1' in self.data and self.data.get('category_level_1'):
            try:
                level_1_id = int(self.data.get('category_level_1'))
                self.fields['category_level_2'].queryset = IngredientCategory.objects.filter(
                    parent_id=level_1_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass

        if 'category_level_2' in self.data and self.data.get('category_level_2'):
            try:
                level_2_id = int(self.data.get('category_level_2'))
                self.fields['category_level_3'].queryset = IngredientCategory.objects.filter(
                    parent_id=level_2_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        level_1 = cleaned_data.get('category_level_1')
        level_2 = cleaned_data.get('category_level_2')
        level_3 = cleaned_data.get('category_level_3')

        if level_3:
            selected_category = level_3
        elif level_2:
            selected_category = level_2
        elif level_1:
            selected_category = level_1
        else:
            selected_category = None

        cleaned_data['selected_category'] = selected_category
        return cleaned_data