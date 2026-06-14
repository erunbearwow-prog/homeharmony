# quick_import_categories.py
import json
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
django.setup()

from kitchen.models import IngredientCategory

# Укажите путь к вашему файлу
json_file = 'Ingredients_categories/categories_export_20260611_212137.json'

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

created = 0
for item in data:
    parent = None
    if item.get('parent_id'):
        try:
            parent = IngredientCategory.objects.get(id=item['parent_id'])
        except IngredientCategory.DoesNotExist:
            pass

    obj, is_created = IngredientCategory.objects.update_or_create(
        id=item['id'],
        defaults={
            'name': item['name'],
            'parent': parent,
            'icon': item.get('icon', ''),
            'sort_order': item.get('sort_order', 0),
        }
    )
    if is_created:
        created += 1
        print(f"✅ {obj.name}")

print(f"\n✅ Импортировано {created} категорий")