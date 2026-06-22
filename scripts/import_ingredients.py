#!/usr/bin/env python
import os
import sys
import csv
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
django.setup()

from kitchen.models import Ingredient, IngredientCategory


def import_ingredients():
    csv_file = '../Ingredients_categories/ingredients_export_20260611_212137.csv'

    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        created = 0
        updated = 0

        for row in reader:
            name_ru = row.get('name_ru', '').strip()
            if not name_ru:
                continue

            # Поиск категории
            category = None
            category_id = row.get('category_id')
            if category_id and category_id.isdigit():
                try:
                    category = IngredientCategory.objects.get(id=int(category_id))
                except IngredientCategory.DoesNotExist:
                    pass

            # Подготовка данных
            defaults = {
                'fdc_id': row.get('fdc_id') or None,
                'description': row.get('description', ''),
                'category': category,
                'is_common': row.get('is_common', 'False').lower() == 'true',
                'data_source': row.get('data_source', 'USDA'),
                'calories': float(row['calories']) if row.get('calories') else None,
                'protein': float(row['protein']) if row.get('protein') else None,
                'fat': float(row['fat']) if row.get('fat') else None,
                'carbohydrates': float(row['carbohydrates']) if row.get('carbohydrates') else None,
                'fiber': float(row['fiber']) if row.get('fiber') else None,
                'sugar': float(row['sugar']) if row.get('sugar') else None,
                'saturated_fat': float(row['saturated_fat']) if row.get('saturated_fat') else None,
                'trans_fat': float(row['trans_fat']) if row.get('trans_fat') else None,
                'cholesterol': float(row['cholesterol']) if row.get('cholesterol') else None,
                'vitamin_a': float(row['vitamin_a']) if row.get('vitamin_a') else None,
                'vitamin_b1': float(row['vitamin_b1']) if row.get('vitamin_b1') else None,
                'vitamin_b2': float(row['vitamin_b2']) if row.get('vitamin_b2') else None,
                'vitamin_b3': float(row['vitamin_b3']) if row.get('vitamin_b3') else None,
                'vitamin_b6': float(row['vitamin_b6']) if row.get('vitamin_b6') else None,
                'vitamin_b9': float(row['vitamin_b9']) if row.get('vitamin_b9') else None,
                'vitamin_b12': float(row['vitamin_b12']) if row.get('vitamin_b12') else None,
                'vitamin_c': float(row['vitamin_c']) if row.get('vitamin_c') else None,
                'vitamin_d': float(row['vitamin_d']) if row.get('vitamin_d') else None,
                'vitamin_e': float(row['vitamin_e']) if row.get('vitamin_e') else None,
                'vitamin_k': float(row['vitamin_k']) if row.get('vitamin_k') else None,
                'calcium': float(row['calcium']) if row.get('calcium') else None,
                'iron': float(row['iron']) if row.get('iron') else None,
                'magnesium': float(row['magnesium']) if row.get('magnesium') else None,
                'phosphorus': float(row['phosphorus']) if row.get('phosphorus') else None,
                'potassium': float(row['potassium']) if row.get('potassium') else None,
                'sodium': float(row['sodium']) if row.get('sodium') else None,
                'zinc': float(row['zinc']) if row.get('zinc') else None,
                'copper': float(row['copper']) if row.get('copper') else None,
                'manganese': float(row['manganese']) if row.get('manganese') else None,
                'selenium': float(row['selenium']) if row.get('selenium') else None,
                'water': float(row['water']) if row.get('water') else None,
                'ash': float(row['ash']) if row.get('ash') else None,
            }

            # Создаём или обновляем
            obj, is_created = Ingredient.objects.update_or_create(
                name=name_ru,
                defaults=defaults
            )

            if is_created:
                created += 1
            else:
                updated += 1

            if (created + updated) % 50 == 0:
                print(f"📊 Прогресс: {created + updated}...")

    print(f"\n✅ Импорт завершён!")
    print(f"   Создано: {created}")
    print(f"   Обновлено: {updated}")


if __name__ == '__main__':
    import_ingredients()