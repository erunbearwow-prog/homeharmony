# import_products.py
import os
import sys
import csv
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
django.setup()

from kitchen.models import Product


def import_products(csv_file, limit=100):
    print(f"🚀 Импорт из {csv_file}...")

    imported = 0
    skipped = 0

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            if i >= limit:
                break

            # Извлекаем название (теперь оно уже как строка)
            name = row.get('product_name', '').strip()
            if not name or len(name) < 3:
                skipped += 1
                continue

            # Ограничиваем длину
            name = name[:300]

            product, created = Product.objects.update_or_create(
                code=row.get('code', '')[:100],
                defaults={
                    'name': name,
                    'brand': row.get('brands', '')[:200],
                    'quantity': row.get('quantity', '')[:100],
                    'categories': row.get('categories', '')[:500],
                    'ingredients_text': row.get('ingredients_text', '')[:2000],
                    'nutriscore_grade': row.get('nutriscore_grade', '')[:1],
                    'data_source': 'Open Food Facts',
                }
            )

            if created:
                imported += 1
                print(f"✅ {imported}. {name[:60]}...")

    print(f"\n✅ Импортировано: {imported}, Пропущено: {skipped}")


if __name__ == '__main__':
    import_products('russian_products.csv', limit=100)