# scripts/analyze_categories.py
# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Анализ категорий ингредиентов
Запуск: python scripts/analyze_categories.py
"""

import os
import sys
from pathlib import Path
from collections import Counter
from django.db.models import Count

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import IngredientCategory, AbstractIngredient


def analyze_categories():
    """Анализирует категории"""
    print("=" * 70)
    print("📊 АНАЛИЗ КАТЕГОРИЙ")
    print("=" * 70)

    total_categories = IngredientCategory.objects.count()
    print(f"\n📂 Всего категорий: {total_categories}")

    # Категории с количеством ингредиентов
    categories_with_count = IngredientCategory.objects.annotate(
        count=Count('abstractingredient')
    ).order_by('-count')

    print("\n📊 КАТЕГОРИИ С ИНГРЕДИЕНТАМИ (топ 20):")
    print("-" * 70)
    for cat in categories_with_count[:20]:
        print(f"  {cat.name}: {cat.count} ингредиентов")

    # Пустые категории
    empty_categories = categories_with_count.filter(count=0)
    print(f"\n📂 Пустых категорий: {empty_categories.count()}")

    # Категории с одинаковыми названиями (дубликаты)
    duplicates = IngredientCategory.objects.values('name').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    if duplicates.exists():
        print("\n🔄 ДУБЛИКАТЫ КАТЕГОРИЙ:")
        print("-" * 70)
        for dup in duplicates:
            print(f"  '{dup['name']}' повторяется {dup['count']} раз")
            # Показываем ID дубликатов
            ids = IngredientCategory.objects.filter(name=dup['name']).values_list('id', flat=True)
            print(f"    ID: {', '.join(map(str, ids))}")

    # Категории без родителя (корневые)
    root_categories = IngredientCategory.objects.filter(parent__isnull=True)
    print(f"\n📂 Корневых категорий: {root_categories.count()}")

    # Проверяем иерархию
    print("\n📊 ИЕРАРХИЯ КАТЕГОРИЙ:")
    print("-" * 70)
    for cat in root_categories[:10]:
        children = IngredientCategory.objects.filter(parent=cat)
        print(f"  {cat.name} ({children.count()} подкатегорий)")
        for child in children[:5]:
            grandchildren = IngredientCategory.objects.filter(parent=child)
            print(f"    └── {child.name} ({grandchildren.count()})")
            for grand in grandchildren[:3]:
                print(f"        └── {grand.name}")
        if children.count() > 5:
            print(f"    ... и еще {children.count() - 5}")

    # Рекомендации
    print("\n" + "=" * 70)
    print("💡 РЕКОМЕНДАЦИИ")
    print("=" * 70)

    if empty_categories.exists():
        print(f"  1. Удалить {empty_categories.count()} пустых категорий")

    if duplicates.exists():
        print(f"  2. Объединить {duplicates.count()} дублирующихся категорий")

    if root_categories.count() > 50:
        print(f"  3. Сократить количество корневых категорий ({root_categories.count()} -> 20-30)")

    print("=" * 70)


if __name__ == "__main__":
    analyze_categories()