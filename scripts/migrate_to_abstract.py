#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для переноса данных из Ingredient в AbstractIngredient
Запуск: python scripts/migrate_to_abstract.py
"""

import os
import sys
from pathlib import Path
from django.db import transaction
from django.db.models import Count

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import Ingredient, AbstractIngredient, BrandedIngredient

# Поля, которые нужно скопировать из Ingredient в AbstractIngredient
FIELDS_TO_COPY = [
    'name', 'description', 'description_ru',
    'calories', 'protein', 'fat', 'carbohydrates',
    'fiber', 'sugar', 'water', 'ash', 'starch',
    'vitamin_a', 'beta_carotene', 'vitamin_b1', 'vitamin_b2',
    'vitamin_b3', 'vitamin_b4', 'vitamin_b5', 'vitamin_b6',
    'vitamin_b7', 'vitamin_b9_folate', 'vitamin_b12',
    'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k',
    'potassium', 'calcium', 'magnesium', 'sodium', 'phosphorus',
    'sulfur', 'silicon', 'chlorine',
    'iron', 'manganese', 'copper', 'selenium', 'zinc',
    'aluminum', 'boron', 'vanadium', 'iodine', 'cobalt',
    'lithium', 'molybdenum', 'nickel', 'rubidium', 'fluorine', 'chromium',
    'saturated_fat', 'trans_fat', 'cholesterol', 'omega_3', 'omega_6',
    'organic_acids',
    'data_source', 'fdc_id', 'image', 'created_at', 'updated_at', 'is_active'
]


@transaction.atomic
def migrate_to_abstract():
    """Переносит данные из Ingredient в AbstractIngredient"""
    print("=" * 70)
    print("🔄 МИГРАЦИЯ ДАННЫХ: Ingredient -> AbstractIngredient")
    print("=" * 70)

    total = Ingredient.objects.count()
    print(f"\n📊 Всего ингредиентов для переноса: {total}")

    stats = {
        'created': 0,
        'duplicates': 0,
        'errors': 0,
        'ingredients_updated': 0,
    }

    # Для отслеживания дубликатов
    seen_names = set()

    print("\n" + "=" * 70)
    print("🚀 НАЧИНАЕМ ПЕРЕНОС...")
    print("=" * 70)

    for i, old_ing in enumerate(Ingredient.objects.all(), 1):
        try:
            # Проверяем, существует ли уже AbstractIngredient с таким именем
            existing = AbstractIngredient.objects.filter(name=old_ing.name).first()

            if existing:
                # Если существует, просто связываем старый Ingredient с ним
                stats['duplicates'] += 1
                old_ing.abstract = existing
                old_ing.save()
                stats['ingredients_updated'] += 1

                if stats['duplicates'] <= 10:  # Показываем первые 10 дубликатов
                    print(f"🔄 Дубликат #{stats['duplicates']}: {old_ing.name[:50]} -> существующий ID:{existing.id}")
                continue

            # Создаем новый AbstractIngredient
            abstract_data = {}
            for field in FIELDS_TO_COPY:
                if hasattr(old_ing, field):
                    value = getattr(old_ing, field)
                    abstract_data[field] = value

            # Устанавливаем category из старого ингредиента
            if old_ing.category:
                abstract_data['category'] = old_ing.category

            # Создаем абстрактный ингредиент
            abstract = AbstractIngredient.objects.create(**abstract_data)

            # Связываем старый Ingredient с новым AbstractIngredient
            old_ing.abstract = abstract
            old_ing.save()

            stats['created'] += 1
            stats['ingredients_updated'] += 1

            # Показываем прогресс
            if stats['created'] % 100 == 0:
                print(f"📊 Прогресс: {i}/{total} | Создано: {stats['created']} | Дубликатов: {stats['duplicates']}")

        except Exception as e:
            stats['errors'] += 1
            print(f"❌ Ошибка при переносе {old_ing.name}: {e}")

    # Итог
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА МИГРАЦИИ")
    print("=" * 70)
    print(f"  Всего ингредиентов:     {total}")
    print(f"  Создано AbstractIngredient: {stats['created']}")
    print(f"  Использовано существующих:  {stats['duplicates']}")
    print(f"  Обновлено Ingredient:   {stats['ingredients_updated']}")
    print(f"  Ошибок:                 {stats['errors']}")

    # Проверяем результат
    abstract_count = AbstractIngredient.objects.count()
    ingredient_with_abstract = Ingredient.objects.filter(abstract__isnull=False).count()

    print("\n" + "=" * 70)
    print("📊 РЕЗУЛЬТАТ")
    print("=" * 70)
    print(f"  AbstractIngredient в БД: {abstract_count}")
    print(f"  Ingredient с abstract:    {ingredient_with_abstract}")

    if ingredient_with_abstract == total:
        print("\n🎉 МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    else:
        print(f"\n⚠️ ВНИМАНИЕ: {total - ingredient_with_abstract} ингредиентов остались без abstract!")


if __name__ == "__main__":
    migrate_to_abstract()