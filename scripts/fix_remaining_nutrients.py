# scripts/fix_remaining_nutrients.py
# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Исправление оставшихся 19 ингредиентов без КБЖУ
Запуск: python scripts/fix_remaining_nutrients.py
"""

import os
import sys
from pathlib import Path
from django.db import transaction

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import Ingredient

# Данные для 18 ингредиентов без КБЖУ
KNOWN_DATA = {
    'Омлет натуральный': {
        'calories': 221.9,
        'protein': 12.2,
        'fat': 18.4,
        'carbohydrates': 1.9,
    },
    'Боржоми': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Ессентуки №4': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Нарзан': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Газированный напиток низкокалорийный исключая кола': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Гвоздика': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Дижонская горчица': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Костяника': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Лимонная кислота': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Листья черники': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Молоко': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Молоко цельное': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Мука пшеничная': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Панировочные сухари': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Перец душистый': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Сливки': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Соль поваренная пищевая': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Сумах': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
    'Черемуха': {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
    },
}


@transaction.atomic
def fix_remaining():
    """Исправляет оставшиеся 19 ингредиентов"""
    print("=" * 70)
    print("🔧 ИСПРАВЛЕНИЕ ОСТАВШИХСЯ 19 ИНГРЕДИЕНТОВ")
    print("=" * 70)

    # Проверяем, сколько осталось
    missing = Ingredient.objects.filter(
        calories__isnull=True
    )

    print(f"\n📊 Осталось ингредиентов без калорий: {missing.count()}")

    if missing.count() == 0:
        print("✅ Все ингредиенты имеют калории!")
        return

    stats = {
        'updated': 0,
        'not_found': 0,
    }

    # Список не найденных
    not_found = []

    for ing in missing:
        # Ищем в KNOWN_DATA
        if ing.name in KNOWN_DATA:
            data = KNOWN_DATA[ing.name]

            # Обновляем поля
            for field, value in data.items():
                if hasattr(ing, field):
                    setattr(ing, field, value)

            ing.save()
            stats['updated'] += 1
            print(f"✅ {ing.name}: {data.get('calories')} ккал")
        else:
            stats['not_found'] += 1
            not_found.append(ing.name)

    # Итог
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    print(f"  Обновлено: {stats['updated']}")
    print(f"  Не найдено: {stats['not_found']}")

    if not_found:
        print("\n⚠️ Не найдены в справочнике:")
        for name in not_found:
            print(f"  - {name}")

        print("\n💡 Добавьте их в KNOWN_DATA и запустите снова")


if __name__ == "__main__":
    fix_remaining()