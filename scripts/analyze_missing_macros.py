# scripts/analyze_missing_macros.py
# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Анализ недостающих макронутриентов
Запуск: python scripts/analyze_missing_macros.py
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


def analyze():
    """Анализирует, каких макронутриентов не хватает"""
    print("=" * 70)
    print("🔍 АНАЛИЗ НЕДОСТАЮЩИХ МАКРОНУТРИЕНТОВ")
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

    # Проверяем, есть ли ингредиенты без белков, но с калориями
    no_protein = Ingredient.objects.filter(
        protein__isnull=True,
        calories__isnull=False
    ).count()
    print(f"\n  Без белков, но с калориями: {no_protein}")

    # Без жиров, но с калориями
    no_fat = Ingredient.objects.filter(
        fat__isnull=True,
        calories__isnull=False
    ).count()
    print(f"  Без жиров, но с калориями: {no_fat}")

    # Без углеводов, но с калориями
    no_carbs = Ingredient.objects.filter(
        carbohydrates__isnull=True,
        calories__isnull=False
    ).count()
    print(f"  Без углеводов, но с калориями: {no_carbs}")

    # Категории ингредиентов с неполным КБЖУ
    print("\n📊 КАТЕГОРИИ ИНГРЕДИЕНТОВ С НЕПОЛНЫМ КБЖУ:")
    print("=" * 70)

    incomplete = Ingredient.objects.filter(
        calories__isnull=False
    ).exclude(
        protein__isnull=False,
        fat__isnull=False,
        carbohydrates__isnull=False
    )

    category_stats = defaultdict(int)
    for ing in incomplete:
        if ing.category:
            category_stats[ing.category.name] += 1
        else:
            category_stats['Без категории'] += 1

    for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {category}: {count}")

    # Показываем примеры
    print("\n📊 ПРИМЕРЫ ИНГРЕДИЕНТОВ С НЕПОЛНЫМ КБЖУ:")
    print("=" * 70)

    for ing in incomplete[:20]:
        missing = []
        if ing.protein is None: missing.append('белки')
        if ing.fat is None: missing.append('жиры')
        if ing.carbohydrates is None: missing.append('углеводы')

        print(f"  {ing.name[:50]}: нет {', '.join(missing)}")

    # Проверяем ингредиенты без категорий
    no_category = Ingredient.objects.filter(category__isnull=True)
    print(f"\n📊 Без категории: {no_category.count()}")
    for ing in no_category:
        print(f"  - {ing.name}")

    # Рекомендации
    print("\n" + "=" * 70)
    print("💡 РЕКОМЕНДАЦИИ")
    print("=" * 70)

    if no_protein > 0 or no_fat > 0 or no_carbs > 0:
        print("  1. Добавить недостающие макронутриенты для ингредиентов")
        print(f"     - Без белков: {no_protein}")
        print(f"     - Без жиров: {no_fat}")
        print(f"     - Без углеводов: {no_carbs}")

    if no_category.exists():
        print(f"\n  2. Назначить категории для {no_category.count()} ингредиентов")
        for ing in no_category:
            print(f"     - {ing.name}")


if __name__ == "__main__":
    analyze()