#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Проверка спарсенных данных
Запуск: просто запустите этот файл в PyCharm
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')

import django

django.setup()

from kitchen.models import Ingredient
from django.db import connection


def main():
    print("=" * 70)
    print("🔍 ПРОВЕРКА СПАРСЕННЫХ ДАННЫХ")
    print("=" * 70)

    total = Ingredient.objects.count()
    print(f"\n📊 Всего ингредиентов: {total}")

    if total == 0:
        print("❌ В базе нет ингредиентов!")
        return

    # 1. Проверяем КБЖУ
    print("\n" + "=" * 70)
    print("📊 1. СТАТИСТИКА КБЖУ")
    print("=" * 70)

    has_calories = Ingredient.objects.filter(calories__isnull=False).count()
    has_protein = Ingredient.objects.filter(protein__isnull=False).count()
    has_fat = Ingredient.objects.filter(fat__isnull=False).count()
    has_carbs = Ingredient.objects.filter(carbohydrates__isnull=False).count()

    print(f"  С калориями:      {has_calories:>5} ({has_calories / total * 100:>5.1f}%)")
    print(f"  С белками:        {has_protein:>5} ({has_protein / total * 100:>5.1f}%)")
    print(f"  С жирами:         {has_fat:>5} ({has_fat / total * 100:>5.1f}%)")
    print(f"  С углеводами:     {has_carbs:>5} ({has_carbs / total * 100:>5.1f}%)")

    # Полное КБЖУ
    full_nutrients = Ingredient.objects.filter(
        calories__isnull=False,
        protein__isnull=False,
        fat__isnull=False,
        carbohydrates__isnull=False
    ).count()
    print(f"\n  С полным КБЖУ:    {full_nutrients:>5} ({full_nutrients / total * 100:>5.1f}%)")

    # 2. Проверяем источник данных
    print("\n" + "=" * 70)
    print("📊 2. ИСТОЧНИКИ ДАННЫХ")
    print("=" * 70)

    sources = Ingredient.objects.values('data_source').distinct()
    for source in sources:
        name = source['data_source'] or 'Не указан'
        count = Ingredient.objects.filter(data_source=source['data_source']).count()
        print(f"  {name}: {count} ({count / total * 100:.1f}%)")

    # 3. Показываем примеры
    print("\n" + "=" * 70)
    print("📊 3. ПРИМЕРЫ ИНГРЕДИЕНТОВ")
    print("=" * 70)

    # С КБЖУ
    print("\n  ✅ С КБЖУ (первые 5):")
    with_nutrients = Ingredient.objects.filter(
        calories__isnull=False
    )[:5]

    if with_nutrients:
        for ing in with_nutrients:
            print(f"    • {ing.name[:50]}")
            print(
                f"      Калории: {ing.calories}, Белки: {ing.protein}, Жиры: {ing.fat}, Углеводы: {ing.carbohydrates}")
    else:
        print("    ❌ Нет ингредиентов с КБЖУ!")

    # Без КБЖУ
    print("\n  ❌ БЕЗ КБЖУ (первые 5):")
    without_nutrients = Ingredient.objects.filter(
        calories__isnull=True
    )[:5]

    if without_nutrients:
        for ing in without_nutrients:
            # Проверяем, есть ли другие данные
            has_other = any([
                ing.protein is not None,
                ing.fat is not None,
                ing.carbohydrates is not None,
                ing.fiber is not None,
                ing.sugar is not None,
            ])
            status = "есть другие данные" if has_other else "НЕТ НИКАКИХ ДАННЫХ!"
            print(f"    • {ing.name[:50]} - {status}")
    else:
        print("    ✅ Все ингредиенты имеют КБЖУ!")

    # 4. Проверяем другие поля
    print("\n" + "=" * 70)
    print("📊 4. ДРУГИЕ ПОЛЯ")
    print("=" * 70)

    other_fields = [
        'fiber', 'sugar', 'water', 'ash',
        'vitamin_a', 'vitamin_b1', 'vitamin_b2', 'vitamin_c', 'vitamin_d', 'vitamin_e',
        'potassium', 'calcium', 'magnesium', 'sodium', 'phosphorus',
        'iron', 'zinc', 'copper', 'manganese', 'selenium',
        'saturated_fat', 'cholesterol'
    ]

    found_fields = []
    for field in other_fields:
        count = Ingredient.objects.filter(**{f"{field}__isnull": False}).exclude(**{f"{field}": 0}).count()
        if count > 0:
            found_fields.append((field, count))

    if found_fields:
        for field, count in sorted(found_fields, key=lambda x: x[1], reverse=True):
            print(f"  {field}: {count} ({count / total * 100:.1f}%)")
    else:
        print("  Нет данных в дополнительных полях")

    # 5. Проверяем категории
    print("\n" + "=" * 70)
    print("📊 5. КАТЕГОРИИ")
    print("=" * 70)

    has_category = Ingredient.objects.filter(category__isnull=False).count()
    print(f"  С категориями: {has_category} ({has_category / total * 100:.1f}%)")

    if has_category > 0:
        # Топ категорий
        from django.db.models import Count
        top_categories = Ingredient.objects.filter(
            category__isnull=False
        ).values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        print("\n  Топ 10 категорий:")
        for cat in top_categories:
            print(f"    • {cat['category__name']}: {cat['count']}")

    # 6. Рекомендации
    print("\n" + "=" * 70)
    print("💡 РЕКОМЕНДАЦИИ")
    print("=" * 70)

    issues = []

    if has_calories == 0:
        issues.append("❌ НЕТ ДАННЫХ О КАЛОРИЯХ! Парсер не сработал или данные не сохранились.")
    elif has_calories < total * 0.5:
        issues.append(f"⚠️ Только {has_calories / total * 100:.1f}% ингредиентов имеют калории. Нужно дозаполнить.")

    if full_nutrients < total * 0.5:
        issues.append(f"⚠️ Только {full_nutrients / total * 100:.1f}% имеют полное КБЖУ.")

    if has_category < total * 0.5:
        issues.append(f"⚠️ Только {has_category / total * 100:.1f}% имеют категории.")

    if not issues:
        print("✅ Все отлично! Данные импортированы корректно.")
    else:
        for issue in issues:
            print(f"  {issue}")

    # 7. Проверяем структуру таблицы
    print("\n" + "=" * 70)
    print("📊 6. СТРУКТУРА ТАБЛИЦЫ")
    print("=" * 70)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'kitchen_ingredient'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()

        print("  Колонки с данными:")
        for col in columns[:15]:  # Показываем первые 15
            print(f"    • {col[0]}: {col[1]} (nullable: {col[2]})")

    print("\n" + "=" * 70)
    print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 70)


if __name__ == "__main__":
    main()