# scripts/assign_categories_brands.py
# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Назначение категорий для брендовых продуктов
Запуск: python scripts/assign_categories_brands.py
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

from kitchen.models import Ingredient, IngredientCategory

# Дополнительный маппинг для брендов и специфических названий
BRAND_CATEGORY_MAP = {
    # === БРЕНДЫ ===
    'ашан': 'Ашан',
    'пятерочка': 'Пятерочка',
    'перекресток': 'Перекресток',
    'лента': 'Лента',
    'магнит': 'Магнит',
    'яшкино': 'Яшкино',
    'роллтон': 'Роллтон',
    'mars': 'Mars',
    'snickers': 'Mars',
    'bounty': 'Mars',
    'twix': 'Mars',
    'm&m': 'Mars',
    'nascafe': 'Nescafe',
    'nesquik': 'Nescafe',
    'mcdonalds': 'Макдоналдс',
    'kfc': 'KFC',
    'ростикc': 'Ростикc',
    'burger king': 'Burger King',
    'subway': 'Subway',
    'dominos': "Domino's",
    'dodo': 'Додо Пицца',
    'папа джонс': 'Папа Джонс',

    # === КОНКРЕТНЫЕ ПРОДУКТЫ ===
    'cannelloni': 'Макароны',
    'caramchoc': 'Шоколад',
    'celebrations': 'Конфеты',
    'choc brownie': 'Выпечка',
    'choco banana': 'Десерты',
    'choco crac': 'Шоколад',
    'cookies': 'Печенье',
    'crousty': 'Закуски',
    'dessert sauce': 'Соусы',
    'elle': 'Молочные продукты',
    'energy to go': 'Напитки',
    'fresh bitter lemon': 'Напитки',
    'fun banan': 'Конфеты',
    'galletas fondants': 'Печенье',
    'golden crack': 'Печенье',
    'gold': 'Закуски',
    'hi protein': 'Спортивное питание',
    'ice cream': 'Десерты',
    'salted caramel': 'Десерты',

    # === КАТЕГОРИИ ПРОДУКТОВ ===
    'arome framboise': 'Напитки',
    'cherry fresh': 'Напитки',
    'energy to go': 'Напитки',
    'fresh bitter lemon': 'Напитки',
    'banan': 'Фрукты',
    'cappuccino': 'Напитки',
    'latte': 'Напитки',
    'espresso': 'Напитки',
    'milkshake': 'Напитки',
    'smoothie': 'Напитки',
    'soda': 'Напитки',
    'cola': 'Напитки',
    'pepsi': 'Напитки',
    'sprite': 'Напитки',
    'fanta': 'Напитки',

    # === ДОПОЛНИТЕЛЬНЫЕ КЛЮЧЕВЫЕ СЛОВА ===
    'sauce': 'Соусы',
    'dressing': 'Соусы',
    'syrup': 'Сиропы',
    'spread': 'Пасты',
    'paste': 'Пасты',
    'pate': 'Паштеты',
    'mousse': 'Десерты',
    'pudding': 'Десерты',
    'parfait': 'Десерты',
    'terrine': 'Закуски',
    'crostini': 'Закуски',
    'bruschetta': 'Закуски',
    'focaccia': 'Хлеб',
    'ciabatta': 'Хлеб',
    'baguette': 'Хлеб',
    'brioche': 'Выпечка',
    'croissant': 'Выпечка',
    'pain au chocolat': 'Выпечка',
    'muffin': 'Выпечка',
    'cupcake': 'Выпечка',
    'brownie': 'Выпечка',
    'blondie': 'Выпечка',
    'cookie': 'Печенье',
    'biscuit': 'Печенье',
    'cracker': 'Печенье',
    'wafer': 'Печенье',
    'scone': 'Выпечка',
    'pancake': 'Выпечка',
    'waffle': 'Вафли',
    'crepe': 'Блины',
    'blintz': 'Блины',
    'quesadilla': 'Закуски',
    'tortilla': 'Закуски',
    'wrap': 'Закуски',
    'burrito': 'Закуски',
    'taco': 'Закуски',
    'fajita': 'Закуски',
    'enchilada': 'Закуски',
    'chili': 'Супы',
    'gumbo': 'Супы',
    'bisque': 'Супы',
    'chowder': 'Супы',
    'consomme': 'Супы',
    'bouillabaisse': 'Супы',
    'ramen': 'Лапша',
    'pho': 'Супы',
    'miso': 'Супы',
    'noodle': 'Лапша',
    'udon': 'Лапша',
    'soba': 'Лапша',
    'rice': 'Рис',
    'quinoa': 'Киноа',
    'couscous': 'Кускус',
    'bulgur': 'Булгур',
    'polenta': 'Полента',
    'risotto': 'Рис',
    'paella': 'Рис',
    'pilaf': 'Рис',
}


@transaction.atomic
def assign_brand_categories():
    """Назначает категории для брендовых продуктов"""
    print("=" * 70)
    print("📂 НАЗНАЧЕНИЕ КАТЕГОРИЙ ДЛЯ БРЕНДОВ")
    print("=" * 70)

    without_cat = Ingredient.objects.filter(category__isnull=True)
    total = without_cat.count()

    if total == 0:
        print("✅ Все ингредиенты имеют категории!")
        return

    print(f"Осталось ингредиентов без категории: {total}")
    print("=" * 70)

    stats = {
        'assigned': 0,
        'not_found': 0,
    }

    # Создаем все категории из маппинга
    categories_to_create = set(BRAND_CATEGORY_MAP.values())
    for category_name in categories_to_create:
        IngredientCategory.objects.get_or_create(name=category_name)

    for ing in without_cat:
        ing_lower = ing.name.lower()
        assigned = False

        # Ищем по ключевым словам
        for keyword, category_name in BRAND_CATEGORY_MAP.items():
            if keyword in ing_lower:
                try:
                    category = IngredientCategory.objects.get(name=category_name)
                    ing.category = category
                    ing.save()
                    stats['assigned'] += 1
                    assigned = True
                    break
                except IngredientCategory.DoesNotExist:
                    # Создаем категорию если не существует
                    category = IngredientCategory.objects.create(name=category_name)
                    ing.category = category
                    ing.save()
                    stats['assigned'] += 1
                    assigned = True
                    break

        if not assigned:
            stats['not_found'] += 1

    # Итог
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    print(f"  Всего оставалось: {total}")
    print(f"  Назначено категорий: {stats['assigned']}")
    print(f"  Осталось без категории: {stats['not_found']}")
    print("=" * 70)

    if stats['not_found'] > 0:
        print("\n⚠️ Ингредиенты без категории (первые 20):")
        for ing in Ingredient.objects.filter(category__isnull=True)[:20]:
            print(f"  - {ing.name}")

        # Показываем статистику по брендам
        print("\n📊 Статистика по брендам:")
        brands = {}
        for ing in Ingredient.objects.filter(category__isnull=True):
            found = False
            for brand in ['ашан', 'пятерочка', 'mars', 'яшкино', 'роллтон', 'перекресток', 'лента', 'магнит']:
                if brand in ing.name.lower():
                    brands[brand] = brands.get(brand, 0) + 1
                    found = True
                    break
            if not found:
                brands['other'] = brands.get('other', 0) + 1

        for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True):
            print(f"  {brand}: {count}")

        print(f"\n💡 Для добавления новых категорий обновите BRAND_CATEGORY_MAP")


if __name__ == "__main__":
    assign_brand_categories()