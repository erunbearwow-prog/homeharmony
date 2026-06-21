#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Создание недостающих категорий для семантической сети
Запуск: python scripts/create_missing_categories.py
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import IngredientCategory

MISSING_CATEGORIES = {
    # Основные корневые категории
    'Овощи': None,
    'Фрукты': None,
    'Ягоды': None,
    'Мясо': None,
    'Птица': None,
    'Рыба': None,
    'Морепродукты': None,
    'Молочные продукты': None,
    'Крупы': None,
    'Макароны': None,
    'Хлеб': None,
    'Сладости': None,
    'Напитки': None,
    'Соусы': None,
    'Специи': None,
    'Грибы': None,
    'Бобовые': None,
    'Яйца': None,
    'Масла': None,
    'Консервы': None,
    'Полуфабрикаты': None,

    # Подкатегории
    'Салаты': 'Овощи',
    'Супы': 'Овощи',
    'Соусы': 'Соусы',
    'Гарниры': 'Овощи',
    'Основные блюда': 'Мясо',
    'Бульоны': 'Мясо',
    'Завтраки': 'Молочные продукты',
    'Десерты': 'Сладости',
    'Выпечка': 'Хлеб',
    'Паста': 'Макароны',
    'Запеканки': 'Молочные продукты',
    'Маринады': 'Соусы',

    # Ингредиенты
    'Лук репчатый': 'Овощи',
    'Сливки': 'Молочные продукты',
    'Сыр': 'Молочные продукты',
    'Масло сливочное': 'Молочные продукты',
    'Мука пшеничная': 'Крупы',
    'Сок абрикосовый': 'Напитки',
    'Сок яблочный': 'Напитки',
    'Сок апельсиновый': 'Напитки',
    'Оливковое масло': 'Масла',
    'Подсолнечное масло': 'Масла',
    'Йогурт': 'Молочные продукты',
    'Рикотта': 'Молочные продукты',
    'Кефир': 'Молочные продукты',
    'Тофу': 'Бобовые',
    'Соевое молоко': 'Напитки',
    'Овсяное молоко': 'Напитки',
    'Миндальное молоко': 'Напитки',
    'Куриная грудка': 'Мясо',
    'Бекон': 'Мясо',
    'Вегетарианский фарш': 'Полуфабрикаты',

    # Кулинарные техники (как категории для связей)
    'Жарка': None,
    'Варка': None,
    'Запекание': None,
    'Тушение': None,
    'Гриль': None,
    'Фритюр': None,
    'Взбивание белков': None,
    'Взбивание сливок': None,
    'Замешивание': None,

    # Для диетических связей
    'Безглютеновая диета': None,
    'Низкокалорийная диета': None,
    'Диабетическая диета': None,
    'Вегетарианская диета': None,

    # Нутриенты (как категории)
    'Белок': None,
    'Омега-3': None,
    'Жиры': None,
    'Клетчатка': None,
    'Кальций': None,
    'Железо': None,
    'Калий': None,
    'Витамин C': None,

    # Вкусовые категории
    'Вкус': None,
    'Лимон': 'Фрукты',
    'Перец': 'Специи',
}


def create_missing():
    """Создает недостающие категории"""
    print("=" * 70)
    print("📂 СОЗДАНИЕ НЕДОСТАЮЩИХ КАТЕГОРИЙ")
    print("=" * 70)

    stats = {'created': 0, 'exists': 0, 'errors': 0}

    # Сначала создаем корневые категории (где parent=None)
    for name, parent_name in MISSING_CATEGORIES.items():
        if parent_name is None:
            # Корневая категория
            cat, created = IngredientCategory.objects.get_or_create(
                name=name,
                defaults={'parent': None}
            )
            if created:
                stats['created'] += 1
                print(f"✅ Создана корневая: {name}")
            else:
                stats['exists'] += 1

    # Затем создаем дочерние категории
    for name, parent_name in MISSING_CATEGORIES.items():
        if parent_name is not None:
            try:
                parent = IngredientCategory.objects.get(name=parent_name)
                cat, created = IngredientCategory.objects.get_or_create(
                    name=name,
                    defaults={'parent': parent}
                )
                if created:
                    stats['created'] += 1
                    print(f"✅ Создана: {name} → {parent_name}")
                else:
                    stats['exists'] += 1
            except IngredientCategory.DoesNotExist:
                stats['errors'] += 1
                print(f"❌ Родитель не найден: {parent_name} для {name}")

    # Итог
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    print(f"  Создано: {stats['created']}")
    print(f"  Уже существовало: {stats['exists']}")
    print(f"  Ошибок: {stats['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    create_missing()