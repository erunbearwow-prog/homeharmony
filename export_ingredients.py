#!/usr/bin/env python
import os
import sys
import json
import csv
from datetime import datetime

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')

import django

django.setup()

from kitchen.models import Ingredient, IngredientCategory


def export_to_json():
    """Экспорт ингредиентов в JSON"""
    ingredients = Ingredient.objects.all().select_related('category')

    data = []
    for ing in ingredients:
        item = {
            # Основная информация
            'name': ing.name,
            'name_ru': ing.name_ru,
            'fdc_id': ing.fdc_id,
            'description': ing.description,
            'description_ru': ing.description_ru,
            'category': ing.category.name if ing.category else None,
            'category_id': ing.category_id,
            'is_common': ing.is_common,
            'data_source': ing.data_source,

            # Макронутриенты (на 100г)
            'calories': ing.calories,
            'protein': ing.protein,
            'fat': ing.fat,
            'carbohydrates': ing.carbohydrates,
            'fiber': ing.fiber,
            'sugar': ing.sugar,

            # Жиры и холестерин
            'saturated_fat': ing.saturated_fat,
            'trans_fat': ing.trans_fat,
            'cholesterol': ing.cholesterol,

            # Витамины
            'vitamin_a': ing.vitamin_a,
            'vitamin_b1': ing.vitamin_b1,
            'vitamin_b2': ing.vitamin_b2,
            'vitamin_b3': ing.vitamin_b3,
            'vitamin_b6': ing.vitamin_b6,
            'vitamin_b9': ing.vitamin_b9,
            'vitamin_b12': ing.vitamin_b12,
            'vitamin_c': ing.vitamin_c,
            'vitamin_d': ing.vitamin_d,
            'vitamin_e': ing.vitamin_e,
            'vitamin_k': ing.vitamin_k,

            # Минералы
            'calcium': ing.calcium,
            'iron': ing.iron,
            'magnesium': ing.magnesium,
            'phosphorus': ing.phosphorus,
            'potassium': ing.potassium,
            'sodium': ing.sodium,
            'zinc': ing.zinc,
            'copper': ing.copper,
            'manganese': ing.manganese,
            'selenium': ing.selenium,

            # Дополнительно
            'water': ing.water,
            'ash': ing.ash,
            'image_url': ing.image.url if ing.image else None,

            # Служебные поля
            'last_update': ing.last_update.isoformat() if ing.last_update else None,
            'created_at': ing.created_at.isoformat() if ing.created_at else None,
        }
        data.append(item)

    # Сохраняем JSON
    output_file = f'ingredients_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Экспортировано {len(data)} ингредиентов в {output_file}")
    return output_file


def export_to_csv():
    """Экспорт ингредиентов в CSV"""
    ingredients = Ingredient.objects.all().select_related('category')

    # Поля для экспорта
    fields = [
        'name', 'name_ru', 'fdc_id', 'category', 'is_common', 'data_source',
        'calories', 'protein', 'fat', 'carbohydrates', 'fiber', 'sugar',
        'saturated_fat', 'trans_fat', 'cholesterol',
        'vitamin_a', 'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b6',
        'vitamin_b9', 'vitamin_b12', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k',
        'calcium', 'iron', 'magnesium', 'phosphorus', 'potassium', 'sodium',
        'zinc', 'copper', 'manganese', 'selenium',
        'water', 'ash', 'last_update', 'created_at'
    ]

    output_file = f'ingredients_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()

        for ing in ingredients:
            row = {
                'name': ing.name,
                'name_ru': ing.name_ru,
                'fdc_id': ing.fdc_id,
                'category': ing.category.name if ing.category else '',
                'is_common': ing.is_common,
                'data_source': ing.data_source,
                'calories': ing.calories,
                'protein': ing.protein,
                'fat': ing.fat,
                'carbohydrates': ing.carbohydrates,
                'fiber': ing.fiber,
                'sugar': ing.sugar,
                'saturated_fat': ing.saturated_fat,
                'trans_fat': ing.trans_fat,
                'cholesterol': ing.cholesterol,
                'vitamin_a': ing.vitamin_a,
                'vitamin_b1': ing.vitamin_b1,
                'vitamin_b2': ing.vitamin_b2,
                'vitamin_b3': ing.vitamin_b3,
                'vitamin_b6': ing.vitamin_b6,
                'vitamin_b9': ing.vitamin_b9,
                'vitamin_b12': ing.vitamin_b12,
                'vitamin_c': ing.vitamin_c,
                'vitamin_d': ing.vitamin_d,
                'vitamin_e': ing.vitamin_e,
                'vitamin_k': ing.vitamin_k,
                'calcium': ing.calcium,
                'iron': ing.iron,
                'magnesium': ing.magnesium,
                'phosphorus': ing.phosphorus,
                'potassium': ing.potassium,
                'sodium': ing.sodium,
                'zinc': ing.zinc,
                'copper': ing.copper,
                'manganese': ing.manganese,
                'selenium': ing.selenium,
                'water': ing.water,
                'ash': ing.ash,
                'last_update': ing.last_update.isoformat() if ing.last_update else '',
                'created_at': ing.created_at.isoformat() if ing.created_at else '',
            }
            writer.writerow(row)

    print(f"✅ Экспортировано {len(ingredients)} ингредиентов в {output_file}")
    return output_file


def export_categories():
    """Экспорт категорий ингредиентов"""
    categories = IngredientCategory.objects.all()

    data = []
    for cat in categories:
        data.append({
            'id': cat.id,
            'name': cat.name,
            'parent': cat.parent.name if cat.parent else None,
            'parent_id': cat.parent_id,
            'icon': cat.icon,
            'sort_order': cat.sort_order,
        })

    output_file = f'categories_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Экспортировано {len(data)} категорий в {output_file}")
    return output_file


if __name__ == '__main__':
    print("🚀 Начинаем экспорт базы ингредиентов...")
    print("=" * 50)

    # Экспорт в JSON
    json_file = export_to_json()
    print(f"   JSON: {json_file}")

    # Экспорт в CSV
    csv_file = export_to_csv()
    print(f"   CSV: {csv_file}")

    # Экспорт категорий
    cat_file = export_categories()
    print(f"   Категории: {cat_file}")

    print("=" * 50)
    print("✅ Экспорт завершён!")