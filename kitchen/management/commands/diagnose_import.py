# kitchen/management/commands/diagnose_import.py

from django.core.management.base import BaseCommand
from kitchen.models import Ingredient
from django.db import connection


class Command(BaseCommand):
    help = 'Диагностирует проблему с импортом КБЖУ'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 ДИАГНОСТИКА ИМПОРТА КБЖУ'))
        self.stdout.write('=' * 60)

        # 1. Проверяем структуру таблицы
        self.check_table_structure()

        # 2. Проверяем данные
        self.check_data()

        # 3. Проверяем возможные причины
        self.check_possible_causes()

        # 4. Даем рекомендации
        self.give_recommendations()

    def check_table_structure(self):
        """Проверяет структуру таблицы Ingredient"""
        self.stdout.write('\n📋 СТРУКТУРА ТАБЛИЦЫ:')

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'kitchen_ingredient'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()

            for col in columns:
                self.stdout.write(f'  - {col[0]}: {col[1]}')

    def check_data(self):
        """Проверяет данные в таблице"""
        self.stdout.write('\n📊 АНАЛИЗ ДАННЫХ:')

        total = Ingredient.objects.count()
        has_calories = Ingredient.objects.filter(calories__isnull=False).count()
        has_protein = Ingredient.objects.filter(protein__isnull=False).count()
        has_fat = Ingredient.objects.filter(fat__isnull=False).count()
        has_carbs = Ingredient.objects.filter(carbohydrates__isnull=False).count()

        self.stdout.write(f'  Всего ингредиентов: {total}')
        self.stdout.write(f'  С калориями: {has_calories} ({has_calories / total * 100:.1f}%)')
        self.stdout.write(f'  С белками: {has_protein} ({has_protein / total * 100:.1f}%)')
        self.stdout.write(f'  С жирами: {has_fat} ({has_fat / total * 100:.1f}%)')
        self.stdout.write(f'  С углеводами: {has_carbs} ({has_carbs / total * 100:.1f}%)')

        # Проверяем значения
        zero_calories = Ingredient.objects.filter(calories=0).count()
        negative_calories = Ingredient.objects.filter(calories__lt=0).count()

        self.stdout.write(f'  С нулевыми калориями: {zero_calories}')
        self.stdout.write(f'  С отрицательными калориями: {negative_calories}')

    def check_possible_causes(self):
        """Проверяет возможные причины"""
        self.stdout.write('\n🔎 ВОЗМОЖНЫЕ ПРИЧИНЫ:')

        # Проверяем, есть ли поле data_source
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'kitchen_ingredient' 
                AND column_name = 'data_source'
            """)
            has_data_source = cursor.fetchone()

        if has_data_source:
            sources = Ingredient.objects.values('data_source').distinct()
            self.stdout.write('\n  Источники данных:')
            for source in sources:
                count = Ingredient.objects.filter(data_source=source['data_source']).count()
                self.stdout.write(f'    - {source["data_source"]}: {count} ингредиентов')

        # Проверяем ингредиенты с необычными названиями
        test_names = Ingredient.objects.filter(
            name__icontains='ккал'
        )[:5]

        if test_names.exists():
            self.stdout.write('\n  Найдены ингредиенты с "ккал" в названии:')
            for ing in test_names:
                self.stdout.write(f'    - {ing.name}')

    def give_recommendations(self):
        """Дает рекомендации"""
        self.stdout.write('\n💡 РЕКОМЕНДАЦИИ:')

        # Проверяем, может быть данные в другом поле
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'kitchen_ingredient' 
                AND column_name LIKE '%nutri%'
            """)
            nutri_columns = cursor.fetchall()

        if nutri_columns:
            self.stdout.write('\n  Найдены колонки с "nutri":')
            for col in nutri_columns:
                self.stdout.write(f'    - {col[0]}')

            self.stdout.write('\n  Попробуйте проверить данные в этих колонках')

        # Предлагаем варианты
        self.stdout.write('\n  Варианты решения:')
        self.stdout.write('  1. Проверить исходный файл импорта')
        self.stdout.write('  2. Запустить скрипт migrate_nutrients.py')
        self.stdout.write('  3. Импортировать данные заново из источника')