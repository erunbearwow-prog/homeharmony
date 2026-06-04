# kitchen/improvements_to_apply_later.py
"""
Улучшения для импорта рецептов (TODO после отладки)
====================================================

1. Нормализация названий ингредиентов
   - Лук репчатый → лук
   - Использовать словарь синонимов или pymorphy2

2. Обновление default_unit
   - Анализировать все использования ингредиента
   - Устанавливать самую частую единицу измерения

3. Preview-режим
   - Показывать, какие ингредиенты будут созданы
   - Показывать, какие рецепты будут добавлены
   - Без фактического сохранения в БД

4. Объединение дубликатов
   - Поиск ингредиентов с одинаковыми названиями
   - Перенаправление RecipeIngredient на основной
"""


# Код для нормализации
def normalize_ingredient_name(name: str) -> str:
    """Нормализует название ингредиента (для будущего использования)"""
    import re
    name = name.lower().strip()
    name = re.sub(r'\s*\([^)]*\)', '', name)
    name = re.sub(r'\s+', ' ', name)

    synonyms = {
        'лук репчатый': 'лук',
        'репчатый лук': 'лук',
        'лук белый': 'лук белый',
        'перец чёрный молотый': 'чёрный перец',
        'масло подсолнечное': 'подсолнечное масло',
    }
    return synonyms.get(name, name)


# Код для обновления default_unit
def update_default_unit(ingredient):
    """Обновляет default_unit на самую частую единицу"""
    from collections import Counter
    units = RecipeIngredient.objects.filter(ingredient=ingredient).values_list('unit', flat=True)
    if units:
        most_common = Counter(units).most_common(1)[0][0]
        if ingredient.default_unit != most_common:
            ingredient.default_unit = most_common
            ingredient.save()