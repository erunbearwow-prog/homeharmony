# kitchen/management/commands/update_ingredients.py
import os
import urllib.request
import zipfile
import csv
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from kitchen.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает и обновляет базу ингредиентов из официального датасета USDA (Foundation Foods)'

    # Исправленная ссылка на Foundation Foods
    DOWNLOAD_URL = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_2026-04-30.zip"
    DATA_DIR = os.path.join(settings.BASE_DIR, 'data', 'usda')

    NUTRIENT_MAPPING = {
        '1008': 'calories',
        '1003': 'protein',
        '1004': 'fat',
        '1005': 'carbohydrates',
        '1079': 'fiber',
        '2000': 'sugar',
        '1258': 'saturated_fat',
        '1257': 'trans_fat',
        '1253': 'cholesterol',
        '1104': 'vitamin_a',
        '1165': 'vitamin_b1',
        '1166': 'vitamin_b2',
        '1167': 'vitamin_b3',
        '1170': 'vitamin_b6',
        '1177': 'vitamin_b9',
        '1178': 'vitamin_b12',
        '1162': 'vitamin_c',
        '1114': 'vitamin_d',
        '1109': 'vitamin_e',
        '1185': 'vitamin_k',
        '1087': 'calcium',
        '1089': 'iron',
        '1090': 'magnesium',
        '1091': 'phosphorus',
        '1092': 'potassium',
        '1093': 'sodium',
        '1095': 'zinc',
        '1098': 'copper',
        '1101': 'manganese',
        '1103': 'selenium',
        '1051': 'water',
        '1057': 'ash',
    }

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Принудительная загрузка')

    def handle(self, *args, **options):
        force = options['force']
        self.stdout.write(self.style.SUCCESS('🚀 Начинаем импорт ингредиентов...'))

        zip_path = self.download_data(force)
        if not zip_path:
            return

        # Важно: получаем путь к распакованной папке!
        extract_dir = self.extract_archive(zip_path)
        if not extract_dir:
            return

        food_data, nutrient_data = self.parse_files(extract_dir)

        self.import_to_db(food_data, nutrient_data)

        self.stdout.write(self.style.SUCCESS('✅ Импорт завершён!'))

    def download_data(self, force):
        os.makedirs(self.DATA_DIR, exist_ok=True)
        zip_path = os.path.join(self.DATA_DIR, 'foundation_foods.zip')
        if os.path.exists(zip_path) and not force:
            self.stdout.write('📁 Файл уже существует. Использую существующий.')
            return zip_path

        self.stdout.write(f'📥 Скачиваю {self.DOWNLOAD_URL}...')
        try:
            urllib.request.urlretrieve(self.DOWNLOAD_URL, zip_path)
            self.stdout.write(self.style.SUCCESS('✅ Скачано'))
            return zip_path
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка скачивания: {e}'))
            return None

    def extract_archive(self, zip_path):
        """Распаковывает архив и возвращает путь к папке с CSV-файлами."""
        self.stdout.write('📂 Распаковываю архив...')
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(self.DATA_DIR)
            self.stdout.write(self.style.SUCCESS('✅ Распаковано'))

            # Ищем распакованную папку (она может называться по-разному)
            for item in os.listdir(self.DATA_DIR):
                item_path = os.path.join(self.DATA_DIR, item)
                # Проверяем, является ли элемент папкой и содержит ли CSV-файлы
                if os.path.isdir(item_path) and any(f.endswith('.csv') for f in os.listdir(item_path)):
                    self.stdout.write(f'📁 Найдена папка с данными: {item}')
                    return item_path

            # Если папка не найдена, возможно, файлы лежат прямо в data/usda
            if any(f.endswith('.csv') for f in os.listdir(self.DATA_DIR)):
                self.stdout.write('📁 CSV-файлы найдены в корне data/usda')
                return self.DATA_DIR

            self.stdout.write(self.style.ERROR('❌ Не удалось найти папку с CSV-файлами после распаковки.'))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка распаковки: {e}'))
            return None

    def parse_files(self, base_dir):
        """Парсит CSV-файлы из указанной директории."""
        food_path = os.path.join(base_dir, 'food.csv')
        nutrient_path = os.path.join(base_dir, 'food_nutrient.csv')

        if not os.path.exists(food_path) or not os.path.exists(nutrient_path):
            self.stdout.write(self.style.ERROR(f'❌ Не найдены файлы food.csv или food_nutrient.csv в {base_dir}'))
            return {}, {}

        food_data = {}
        with open(food_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                food_data[row['fdc_id']] = row['description']

        nutrient_data = {}
        with open(nutrient_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fdc_id = row['fdc_id']
                nutrient_id = row['nutrient_id']
                amount = row['amount']

                if nutrient_id in self.NUTRIENT_MAPPING:
                    if fdc_id not in nutrient_data:
                        nutrient_data[fdc_id] = {}
                    try:
                        nutrient_data[fdc_id][self.NUTRIENT_MAPPING[nutrient_id]] = float(amount)
                    except (ValueError, TypeError):
                        pass

        return food_data, nutrient_data

    @transaction.atomic
    def import_to_db(self, food_data, nutrient_data):
        created = 0
        updated = 0
        skipped = 0

        for fdc_id, name in food_data.items():
            nutrients = nutrient_data.get(fdc_id, {})

            # Пропускаем ингредиенты, у которых нет основных нутриентов
            if not nutrients.get('calories') or not nutrients.get('protein'):
                skipped += 1
                continue

            defaults = {
                'name': name,
                'fdc_id': fdc_id,
                'calories': nutrients.get('calories'),
                'protein': nutrients.get('protein'),
                'fat': nutrients.get('fat'),
                'carbohydrates': nutrients.get('carbohydrates'),
                'fiber': nutrients.get('fiber'),
                'sugar': nutrients.get('sugar'),
                'saturated_fat': nutrients.get('saturated_fat'),
                'trans_fat': nutrients.get('trans_fat'),
                'cholesterol': nutrients.get('cholesterol'),
                'vitamin_a': nutrients.get('vitamin_a'),
                'vitamin_b1': nutrients.get('vitamin_b1'),
                'vitamin_b2': nutrients.get('vitamin_b2'),
                'vitamin_b3': nutrients.get('vitamin_b3'),
                'vitamin_b6': nutrients.get('vitamin_b6'),
                'vitamin_b9': nutrients.get('vitamin_b9'),
                'vitamin_b12': nutrients.get('vitamin_b12'),
                'vitamin_c': nutrients.get('vitamin_c'),
                'vitamin_d': nutrients.get('vitamin_d'),
                'vitamin_e': nutrients.get('vitamin_e'),
                'vitamin_k': nutrients.get('vitamin_k'),
                'calcium': nutrients.get('calcium'),
                'iron': nutrients.get('iron'),
                'magnesium': nutrients.get('magnesium'),
                'phosphorus': nutrients.get('phosphorus'),
                'potassium': nutrients.get('potassium'),
                'sodium': nutrients.get('sodium'),
                'zinc': nutrients.get('zinc'),
                'copper': nutrients.get('copper'),
                'manganese': nutrients.get('manganese'),
                'selenium': nutrients.get('selenium'),
                'water': nutrients.get('water'),
                'ash': nutrients.get('ash'),
                'data_source': 'USDA Foundation',
            }

            obj, is_created = Ingredient.objects.update_or_create(
                fdc_id=fdc_id,
                defaults=defaults
            )

            if is_created:
                created += 1
            else:
                updated += 1

            if (created + updated) % 1000 == 0:
                self.stdout.write(f'📊 Прогресс: обработано {created + updated} ингредиентов...')

        self.stdout.write(self.style.SUCCESS(f'📊 Результат: Создано {created}, Обновлено {updated}, Пропущено (без КБЖУ) {skipped}'))