# management/commands/import_off_products.py
import csv
import duckdb
from django.core.management.base import BaseCommand
from kitchen.models import Product


class Command(BaseCommand):
    help = 'Импорт продуктов из Open Food Facts'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='russian_products.csv', help='Путь к CSV файлу')
        parser.add_argument('--limit', type=int, default=5000, help='Лимит продуктов для импорта')

    def handle(self, *args, **options):
        file_path = options['file']
        limit = options['limit']

        self.stdout.write(f"🚀 Импорт продуктов из {file_path}...")

        imported = 0
        skipped = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader):
                if i >= limit:
                    break

                name = row.get('product_name', '')
                if not name or len(name) < 3:
                    skipped += 1
                    continue

                # Извлекаем название из структуры, если нужно
                if isinstance(name, dict):
                    name = name.get('text', '') or str(name)

                product, created = Product.objects.update_or_create(
                    name=name[:300],
                    defaults={
                        'code': row.get('code', '')[:100],
                        'name_ru': '',  # позже можно перевести
                        'brand': row.get('brands', '')[:200],
                        'quantity': row.get('quantity', '')[:100],
                        'categories': row.get('categories', '')[:500],
                        'ingredients_text': row.get('ingredients_text', ''),
                        'nutriscore_grade': row.get('nutriscore_grade', '')[:1],
                        'data_source': 'Open Food Facts',
                    }
                )

                if created:
                    imported += 1
                    if imported % 100 == 0:
                        self.stdout.write(f"📊 Импортировано: {imported}")

        self.stdout.write(self.style.SUCCESS(
            f"✅ Импорт завершён! Добавлено: {imported}, Пропущено: {skipped}"
        ))