#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Автоматическое создание связей "богат" на основе КБЖУ
Запуск: python scripts/auto_create_nutrient_relations.py
"""

import os
import sys
from pathlib import Path
from django.db.models import Avg, F, Q

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import AbstractIngredient, IngredientCategory, RelationType, SemanticRelation

# Нутриенты, для которых будем создавать связи
NUTRIENT_MAPPING = {
    # Энергия
    'calories': {'name': 'Калорийность', 'icon': '🔥', 'category': 'Энергия'},

    # Макронутриенты
    'protein': {'name': 'Белок', 'icon': '💪', 'category': 'Белки'},
    'fat': {'name': 'Жиры', 'icon': '🧈', 'category': 'Жиры'},
    'carbohydrates': {'name': 'Углеводы', 'icon': '🍞', 'category': 'Углеводы'},
    'fiber': {'name': 'Клетчатка', 'icon': '🌾', 'category': 'Клетчатка'},

    # Минералы
    'calcium': {'name': 'Кальций', 'icon': '🦴', 'category': 'Минералы'},
    'iron': {'name': 'Железо', 'icon': '🩸', 'category': 'Минералы'},
    'magnesium': {'name': 'Магний', 'icon': '⚡', 'category': 'Минералы'},
    'potassium': {'name': 'Калий', 'icon': '🍌', 'category': 'Минералы'},
    'sodium': {'name': 'Натрий', 'icon': '🧂', 'category': 'Минералы'},
    'zinc': {'name': 'Цинк', 'icon': '🔋', 'category': 'Минералы'},
    'phosphorus': {'name': 'Фосфор', 'icon': '🦷', 'category': 'Минералы'},
    'copper': {'name': 'Медь', 'icon': '🔶', 'category': 'Минералы'},
    'manganese': {'name': 'Марганец', 'icon': '🔷', 'category': 'Минералы'},
    'selenium': {'name': 'Селен', 'icon': '🧬', 'category': 'Минералы'},

    # Витамины
    'vitamin_a': {'name': 'Витамин A', 'icon': '👁️', 'category': 'Витамины'},
    'beta_carotene': {'name': 'Бета-каротин', 'icon': '🥕', 'category': 'Витамины'},
    'vitamin_b1': {'name': 'Витамин B1 (тиамин)', 'icon': '⚡', 'category': 'Витамины'},
    'vitamin_b2': {'name': 'Витамин B2 (рибофлавин)', 'icon': '⚡', 'category': 'Витамины'},
    'vitamin_b3': {'name': 'Витамин B3 (ниацин)', 'icon': '⚡', 'category': 'Витамины'},
    'vitamin_b4': {'name': 'Витамин B4 (холин)', 'icon': '🧠', 'category': 'Витамины'},
    'vitamin_b5': {'name': 'Витамин B5 (пантотеновая)', 'icon': '⚡', 'category': 'Витамины'},
    'vitamin_b6': {'name': 'Витамин B6', 'icon': '⚡', 'category': 'Витамины'},
    'vitamin_b7': {'name': 'Витамин B7 (биотин)', 'icon': '💇', 'category': 'Витамины'},
    'vitamin_b9_folate': {'name': 'Витамин B9 (фолаты)', 'icon': '🤰', 'category': 'Витамины'},
    'vitamin_b12': {'name': 'Витамин B12', 'icon': '💉', 'category': 'Витамины'},
    'vitamin_c': {'name': 'Витамин C', 'icon': '🍊', 'category': 'Витамины'},
    'vitamin_d': {'name': 'Витамин D', 'icon': '☀️', 'category': 'Витамины'},
    'vitamin_e': {'name': 'Витамин E', 'icon': '✨', 'category': 'Витамины'},
    'vitamin_k': {'name': 'Витамин K', 'icon': '🩸', 'category': 'Витамины'},

    # Жиры
    'cholesterol': {'name': 'Холестерин', 'icon': '❤️', 'category': 'Жиры'},
    'omega_3': {'name': 'Омега-3', 'icon': '🐟', 'category': 'Жирные кислоты'},
    'omega_6': {'name': 'Омега-6', 'icon': '🌻', 'category': 'Жирные кислоты'},
    'saturated_fat': {'name': 'Насыщенные жиры', 'icon': '🧈', 'category': 'Жиры'},
    'trans_fat': {'name': 'Трансжиры', 'icon': '🚫', 'category': 'Жиры'},
}


def get_or_create_nutrient_category(nutrient_name):
    """Создает категорию для нутриента, если её нет"""
    cat, created = IngredientCategory.objects.get_or_create(
        name=nutrient_name,
        defaults={'parent': None}
    )
    if created:
        print(f"  📁 Создана категория: {nutrient_name}")
    return cat


def auto_create_relations():
    """Автоматически создает связи 'богат' для ингредиентов"""
    print("=" * 70)
    print("🧠 АВТОМАТИЧЕСКОЕ СОЗДАНИЕ СВЯЗЕЙ 'БОГАТ'")
    print("=" * 70)

    # Получаем тип связи "богат"
    rich_in = RelationType.objects.get(slug='rich_in')

    stats = {'created': 0, 'skipped': 0, 'errors': 0}

    # Для каждого нутриента
    for field, info in NUTRIENT_MAPPING.items():
        nutrient_name = info['name']
        print(f"\n📊 Обработка: {nutrient_name}")

        # Создаем категорию для нутриента
        nutrient_category = get_or_create_nutrient_category(nutrient_name)

        # Находим ингредиенты с этим нутриентом
        ingredients = AbstractIngredient.objects.filter(
            **{f"{field}__isnull": False}
        ).exclude(**{f"{field}": 0})

        if not ingredients.exists():
            print(f"  ⚠️ Нет ингредиентов с {nutrient_name}")
            continue

        # Считаем среднее и 90-й процентиль
        values = list(ingredients.values_list(field, flat=True))
        avg_value = sum(values) / len(values) if values else 0
        values_sorted = sorted(values)
        percentile_90 = values_sorted[int(len(values_sorted) * 0.9)] if values_sorted else 0

        print(f"  Среднее: {avg_value:.2f}, 90-й процентиль: {percentile_90:.2f}")

        # Ищем ингредиенты, которые значительно выше среднего
        threshold = max(avg_value * 2, percentile_90 * 0.8)

        top_ingredients = ingredients.filter(
            **{f"{field}__gte": threshold}
        ).order_by(f'-{field}')[:5]

        if not top_ingredients:
            # Если нет по порогу, берем топ-3
            top_ingredients = ingredients.order_by(f'-{field}')[:3]

        print(f"  Найдено лидеров: {top_ingredients.count()}")

        for ing in top_ingredients:
            value = getattr(ing, field)
            try:
                # Проверяем, существует ли уже связь
                exists = SemanticRelation.objects.filter(
                    from_category=ing.category,
                    to_category=nutrient_category,
                    relation_type=rich_in
                ).exists()

                if exists:
                    stats['skipped'] += 1
                    print(f"    ⏭️ Уже существует: {ing.name} → {nutrient_name}")
                    continue

                # Создаем связь
                relation = SemanticRelation.objects.create(
                    from_category=ing.category,
                    to_category=nutrient_category,
                    relation_type=rich_in,
                    weight=round(value / avg_value, 2) if avg_value > 0 else 1.0,
                    notes=f"Содержит {value:.2f} {info.get('unit', '')} (в {round(value / avg_value, 1)}x выше среднего)"
                )
                stats['created'] += 1
                print(f"    ✅ {ing.name} → {nutrient_name} ({value:.2f})")

            except Exception as e:
                stats['errors'] += 1
                print(f"    ❌ Ошибка: {e}")

    # Итог
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    print(f"  Создано связей: {stats['created']}")
    print(f"  Пропущено (уже есть): {stats['skipped']}")
    print(f"  Ошибок: {stats['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    auto_create_relations()