# scripts/analyze_missing_nutrients.py
# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Анализ недостающего КБЖУ
Запуск: python scripts/analyze_missing_nutrients.py
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import Ingredient


def analyze_missing():
    """Анализирует, каких нутриентов не хватает"""
    print("=" * 70)
    print("🔍 АНАЛИЗ НЕДОСТАЮЩЕГО КБЖУ")
    print("=" * 70)

    total = Ingredient.objects.count()

    # Статистика по каждому нутриенту
    stats = {
        'calories': Ingredient.objects.filter(calories__isnull=True).count(),
        'protein': Ingredient.objects.filter(protein__isnull=True).count(),
        'fat': Ingredient.objects.filter(fat__isnull=True).count(),
        'carbohydrates': Ingredient.objects.filter(carbohydrates__isnull=True).count(),
    }

    print("\n📊 НЕДОСТАЮЩИЕ НУТРИЕНТЫ:")
    print("=" * 70)
    for nutrient, count in stats.items():
        print(f"  {nutrient}: {count} ({count / total * 100:.1f}%)")

    # Какие комбинации отсутствуют
    print("\n📊 КОМБИНАЦИИ ОТСУТСТВУЮЩИХ НУТРИЕНТОВ:")
    print("=" * 70)

    # Полное КБЖУ
    full = Ingredient.objects.filter(
        calories__isnull=False,
        protein__isnull=False,
        fat__isnull=False,
        carbohydrates__isnull=False
    ).count()
    print(f"  Полное КБЖУ: {full} ({full / total * 100:.1f}%)")

    # Только без калорий
    only_no_calories = Ingredient.objects.filter(
        calories__isnull=True,
        protein__isnull=False,
        fat__isnull=False,
        carbohydrates__isnull=False
    ).count()
    print(f"  Только без калорий: {only_no_calories}")

    # Без белков
    no_protein = Ingredient.objects.filter(protein__isnull=True).count()
    print(f"  Без белков: {no_protein}")

    # Без жиров
    no_fat = Ingredient.objects.filter(fat__isnull=True).count()
    print(f"  Без жиров: {no_fat}")

    # Без углеводов
    no_carbs = Ingredient.objects.filter(carbohydrates__isnull=True).count()
    print(f"  Без углеводов: {no_carbs}")

    # Есть только калории
    only_calories = Ingredient.objects.filter(
        calories__isnull=False,
        protein__isnull=True,
        fat__isnull=True,
        carbohydrates__isnull=True
    ).count()
    print(f"\n  Только калории: {only_calories}")

    # Анализ источников данных
    print("\n📊 ИСТОЧНИКИ ДАННЫХ ДЛЯ ИНГРЕДИЕНТОВ БЕЗ КБЖУ:")
    print("=" * 70)

    missing = Ingredient.objects.filter(
        calories__isnull=True
    )

    sources = defaultdict(int)
    for ing in missing:
        source = ing.data_source or 'Не указан'
        # Очищаем от лишнего текста
        if 'Основной источник' in source:
            source = source.replace('Основной источник: ', '').replace('.Подробнее.', '')
        sources[source] += 1

    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")

    # Показываем примеры
    print("\n📊 ПРИМЕРЫ ИНГРЕДИЕНТОВ БЕЗ КБЖУ:")
    print("=" * 70)

    for ing in missing[:20]:
        fields = []
        if ing.calories is None: fields.append('калории')
        if ing.protein is None: fields.append('белки')
        if ing.fat is None: fields.append('жиры')
        if ing.carbohydrates is None: fields.append('углеводы')

        print(f"  {ing.name[:50]}: нет {', '.join(fields)}")

    # Категории ингредиентов без КБЖУ
    print("\n📊 КАТЕГОРИИ ИНГРЕДИЕНТОВ БЕЗ КБЖУ:")
    print("=" * 70)

    category_stats = defaultdict(int)
    for ing in missing:
        if ing.category:
            category_stats[ing.category.name] += 1
        else:
            category_stats['Без категории'] += 1

    for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {category}: {count}")


def suggest_fixes():
    """Предлагает варианты исправления"""
    print("\n" + "=" * 70)
    print("💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ")
    print("=" * 70)

    # 1. Пересчет калорий из макронутриентов
    can_fix = Ingredient.objects.filter(
        calories__isnull=True,
        protein__isnull=False,
        fat__isnull=False,
        carbohydrates__isnull=False
    ).count()

    print(f"\n  1. Можно пересчитать калории из макронутриентов: {can_fix} ингредиентов")
    print(f"     (белки*4 + жиры*9 + углеводы*4)")

    # 2. Заполнение из других источников
    has_some = Ingredient.objects.filter(
        calories__isnull=True,
        protein__isnull=False
    ).count()

    print(f"\n  2. Имеют хотя бы один макронутриент: {has_some}")
    print(f"     (можно пополнить из внешних источников)")

    # 3. Ручная проверка
    no_nutrients = Ingredient.objects.filter(
        calories__isnull=True,
        protein__isnull=True,
        fat__isnull=True,
        carbohydrates__isnull=True
    ).count()

    print(f"\n  3. Не имеют НИКАКИХ данных: {no_nutrients}")
    print(f"     (требуют ручной проверки или импорта)")


if __name__ == "__main__":
    analyze_missing()
    suggest_fixes()