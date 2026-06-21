#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Создание брендированных продуктов
Запуск: python scripts/create_branded_products.py
"""

import os
import sys
from pathlib import Path
from decimal import Decimal

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import AbstractIngredient, BrandedIngredient

# Данные для брендированных продуктов
# Формат: (название_абстрактного, бренд, название_продукта, цена, вес_г, магазин, калории, белки, жиры, углеводы)
BRANDED_PRODUCTS = [
    # === МОЛОЧНЫЕ ПРОДУКТЫ ===
    {
        'abstract_name': 'Молоко пастеризованное, 2,5% жирности',
        'brand': 'Простоквашино',
        'product_name': 'Молоко пастеризованное 2.5%',
        'price': 89.90,
        'weight': 1000,
        'store': 'Пятерочка',
        'calories': 52,
        'protein': 2.8,
        'fat': 2.5,
        'carbohydrates': 4.7,
    },
    {
        'abstract_name': 'Молоко 3.2%',
        'brand': 'Простоквашино',
        'product_name': 'Молоко пастеризованное 3.2%',
        'price': 99.90,
        'weight': 1000,
        'store': 'Пятерочка',
        'calories': 58,
        'protein': 2.8,
        'fat': 3.2,
        'carbohydrates': 4.7,
    },
    {
        'abstract_name': 'Творог 5%',
        'brand': 'Домик в деревне',
        'product_name': 'Творог 5% 200г',
        'price': 89.90,
        'weight': 200,
        'store': 'Пятерочка',
        'calories': 121,
        'protein': 16.0,
        'fat': 5.0,
        'carbohydrates': 2.0,
    },
    {
        'abstract_name': 'Сметана 15%',
        'brand': 'Простоквашино',
        'product_name': 'Сметана 15% 200г',
        'price': 79.90,
        'weight': 200,
        'store': 'Пятерочка',
        'calories': 158,
        'protein': 2.6,
        'fat': 15.0,
        'carbohydrates': 3.6,
    },

    # === МЯСО ===
    {
        'abstract_name': 'Куриная грудка',
        'brand': 'Петелинка',
        'product_name': 'Филе куриное охлажденное',
        'price': 249.90,
        'weight': 500,
        'store': 'Пятерочка',
        'calories': 110,
        'protein': 23.0,
        'fat': 1.5,
        'carbohydrates': 0,
    },
    {
        'abstract_name': 'Куриная грудка',
        'brand': 'Пава-Пава',
        'product_name': 'Филе куриное охлажденное',
        'price': 229.90,
        'weight': 500,
        'store': 'Перекресток',
        'calories': 110,
        'protein': 23.0,
        'fat': 1.5,
        'carbohydrates': 0,
    },
    {
        'abstract_name': 'Говядина',
        'brand': 'Мираторг',
        'product_name': 'Говядина охлажденная (лопатка)',
        'price': 399.90,
        'weight': 500,
        'store': 'Пятерочка',
        'calories': 187,
        'protein': 18.0,
        'fat': 12.4,
        'carbohydrates': 0,
    },
    {
        'abstract_name': 'Фарш куриный',
        'brand': 'Петелинка',
        'product_name': 'Фарш куриный охлажденный',
        'price': 179.90,
        'weight': 400,
        'store': 'Пятерочка',
        'calories': 143,
        'protein': 17.0,
        'fat': 8.0,
        'carbohydrates': 0,
    },

    # === РЫБА ===
    {
        'abstract_name': 'Лосось',
        'brand': 'Меридиан',
        'product_name': 'Филе лосося охлажденное',
        'price': 699.90,
        'weight': 300,
        'store': 'Перекресток',
        'calories': 208,
        'protein': 20.0,
        'fat': 13.0,
        'carbohydrates': 0,
    },
    {
        'abstract_name': 'Треска',
        'brand': 'Русское море',
        'product_name': 'Филе трески мороженое',
        'price': 299.90,
        'weight': 500,
        'store': 'Пятерочка',
        'calories': 82,
        'protein': 18.0,
        'fat': 0.7,
        'carbohydrates': 0,
    },

    # === ОВОЩИ ===
    {
        'abstract_name': 'Картофель',
        'brand': 'Ашан',
        'product_name': 'Картофель молодой 1кг',
        'price': 89.90,
        'weight': 1000,
        'store': 'Ашан',
        'calories': 77,
        'protein': 2.0,
        'fat': 0.1,
        'carbohydrates': 16.3,
    },
    {
        'abstract_name': 'Морковь',
        'brand': 'Ашан',
        'product_name': 'Морковь 1кг',
        'price': 49.90,
        'weight': 1000,
        'store': 'Ашан',
        'calories': 35,
        'protein': 1.3,
        'fat': 0.1,
        'carbohydrates': 6.9,
    },
    {
        'abstract_name': 'Лук репчатый',
        'brand': 'Ашан',
        'product_name': 'Лук репчатый 1кг',
        'price': 39.90,
        'weight': 1000,
        'store': 'Ашан',
        'calories': 41,
        'protein': 1.4,
        'fat': 0.2,
        'carbohydrates': 8.2,
    },
    {
        'abstract_name': 'Капуста белокочанная',
        'brand': 'Ашан',
        'product_name': 'Капуста белокочанная 1кг',
        'price': 49.90,
        'weight': 1000,
        'store': 'Ашан',
        'calories': 25,
        'protein': 1.3,
        'fat': 0.1,
        'carbohydrates': 4.8,
    },

    # === КРУПЫ ===
    {
        'abstract_name': 'Рис',
        'brand': 'Мистраль',
        'product_name': 'Рис круглозерный 800г',
        'price': 89.90,
        'weight': 800,
        'store': 'Пятерочка',
        'calories': 130,
        'protein': 2.7,
        'fat': 0.3,
        'carbohydrates': 28.2,
    },
    {
        'abstract_name': 'Гречка',
        'brand': 'Мистраль',
        'product_name': 'Гречка ядрица 800г',
        'price': 99.90,
        'weight': 800,
        'store': 'Пятерочка',
        'calories': 132,
        'protein': 4.5,
        'fat': 1.3,
        'carbohydrates': 25.4,
    },
    {
        'abstract_name': 'Овсянка',
        'brand': 'Ясно Солнышко',
        'product_name': 'Овсяные хлопья 400г',
        'price': 59.90,
        'weight': 400,
        'store': 'Пятерочка',
        'calories': 88,
        'protein': 3.3,
        'fat': 1.8,
        'carbohydrates': 14.2,
    },

    # === МАКАРОНЫ ===
    {
        'abstract_name': 'Макароны',
        'brand': 'Makfa',
        'product_name': 'Спагетти 450г',
        'price': 69.90,
        'weight': 450,
        'store': 'Пятерочка',
        'calories': 334,
        'protein': 10.3,
        'fat': 1.1,
        'carbohydrates': 68.9,
    },

    # === МАСЛА ===
    {
        'abstract_name': 'Масло подсолнечное',
        'brand': 'Золотая семечка',
        'product_name': 'Масло подсолнечное 1л',
        'price': 119.90,
        'weight': 920,
        'store': 'Пятерочка',
        'calories': 899,
        'protein': 0,
        'fat': 99.9,
        'carbohydrates': 0,
    },
    {
        'abstract_name': 'Масло сливочное',
        'brand': 'Крестьянское',
        'product_name': 'Масло сливочное 82.5% 180г',
        'price': 129.90,
        'weight': 180,
        'store': 'Пятерочка',
        'calories': 748,
        'protein': 0.5,
        'fat': 82.5,
        'carbohydrates': 0.8,
    },

    # === ЯЙЦА ===
    {
        'abstract_name': 'Яйцо куриное',
        'brand': 'Окское',
        'product_name': 'Яйца куриные С0 10шт',
        'price': 89.90,
        'weight': 600,
        'store': 'Пятерочка',
        'calories': 157,
        'protein': 12.7,
        'fat': 11.5,
        'carbohydrates': 0.7,
    },
    {
        'abstract_name': 'Яйцо куриное',
        'brand': 'Вараксино',
        'product_name': 'Яйца куриные С1 10шт',
        'price': 79.90,
        'weight': 550,
        'store': 'Перекресток',
        'calories': 157,
        'protein': 12.7,
        'fat': 11.5,
        'carbohydrates': 0.7,
    },

    # === МУКА ===
    {
        'abstract_name': 'Мука пшеничная',
        'brand': 'Makfa',
        'product_name': 'Мука пшеничная 1кг',
        'price': 69.90,
        'weight': 1000,
        'store': 'Пятерочка',
        'calories': 334,
        'protein': 10.3,
        'fat': 1.1,
        'carbohydrates': 68.9,
    },

    # === СЫР ===
    {
        'abstract_name': 'Сыр',
        'brand': 'Российский',
        'product_name': 'Сыр Российский 200г',
        'price': 159.90,
        'weight': 200,
        'store': 'Пятерочка',
        'calories': 350,
        'protein': 25.0,
        'fat': 27.0,
        'carbohydrates': 1.0,
    },
]


def create_branded_products():
    """Создает брендированные продукты"""
    print("=" * 70)
    print("🏷️  СОЗДАНИЕ БРЕНДИРОВАННЫХ ПРОДУКТОВ")
    print("=" * 70)

    stats = {
        'created': 0,
        'updated': 0,
        'not_found': 0,
        'errors': 0,
    }

    for data in BRANDED_PRODUCTS:
        try:
            # Ищем AbstractIngredient по имени
            abstract = AbstractIngredient.objects.filter(
                name__iexact=data['abstract_name']
            ).first()

            if not abstract:
                print(f"❌ AbstractIngredient не найден: {data['abstract_name']}")
                stats['not_found'] += 1
                continue

            # Проверяем, существует ли уже такой бренд
            branded, created = BrandedIngredient.objects.get_or_create(
                abstract=abstract,
                brand=data['brand'],
                product_name=data['product_name'],
                defaults={
                    'price': Decimal(str(data['price'])),
                    'weight': Decimal(str(data['weight'])),
                    'store': data['store'],
                    'calories': data.get('calories'),
                    'protein': data.get('protein'),
                    'fat': data.get('fat'),
                    'carbohydrates': data.get('carbohydrates'),
                    'is_available': True,
                }
            )

            if created:
                stats['created'] += 1
                print(f"✅ Создан: {data['brand']} {data['product_name']}")
            else:
                # Обновляем существующий
                branded.price = Decimal(str(data['price']))
                branded.weight = Decimal(str(data['weight']))
                branded.store = data['store']
                if data.get('calories'):
                    branded.calories = data['calories']
                if data.get('protein'):
                    branded.protein = data['protein']
                if data.get('fat'):
                    branded.fat = data['fat']
                if data.get('carbohydrates'):
                    branded.carbohydrates = data['carbohydrates']
                branded.is_available = True
                branded.save()
                stats['updated'] += 1
                print(f"🔄 Обновлен: {data['brand']} {data['product_name']}")

        except Exception as e:
            stats['errors'] += 1
            print(f"❌ Ошибка для {data.get('abstract_name')}: {e}")

    # Итог
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    print(f"  Создано: {stats['created']}")
    print(f"  Обновлено: {stats['updated']}")
    print(f"  Не найдено: {stats['not_found']}")
    print(f"  Ошибок: {stats['errors']}")
    print("=" * 70)

    # Проверяем результат
    total = BrandedIngredient.objects.count()
    print(f"\n📊 Всего брендированных продуктов в БД: {total}")


if __name__ == "__main__":
    create_branded_products()