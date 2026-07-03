#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для импорта данных из HTML-файлов HealthDiet в AbstractIngredient
Импортирует: название, КБЖУ и все нутриенты (витамины, минералы, жирные кислоты)
Запуск:
 [путь_к_html_файлу]
"""

import os
import sys
import glob
import re
from bs4 import BeautifulSoup
import django

# ==================== НАСТРОЙКА DJANGO ====================
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
django.setup()

# ==================== ИМПОРТ МОДЕЛЕЙ ====================
from kitchen.models import AbstractIngredient

# ==================== НАСТРОЙКИ ====================
HTML_FOLDER = '../HealthDietParser/data/full_pages'

# ==================== МЭППИНГ НУТРИЕНТОВ ====================
NUTRIENT_MAPPING = {
    # ===== МАКРОНУТРИЕНТЫ =====
    'Калорийность': 'calories',
    'Энергетическая ценность': 'calories',
    'Белки': 'protein',
    'Жиры': 'fat',
    'Углеводы': 'carbohydrates',
    'Углеводы (общие)': 'carbohydrates',
    'Пищевые волокна': 'fiber',
    'Моно- и дисахариды (сахара)': 'sugar',
    'Вода': 'water',
    'Зола': 'ash',
    'Крахмал и декстрины': 'starch',
    'Крахмал': 'starch',

    # ===== ВИТАМИНЫ =====
    'Витамин А, РЭ': 'vitamin_a',
    'Витамин A, РЭ': 'vitamin_a',
    'альфа Каротин': 'vitamin_a',
    'бета Каротин': 'beta_carotene',
    'Бета-каротин': 'beta_carotene',
    'бета Криптоксантин': 'beta_carotene',
    'Витамин В1, тиамин': 'vitamin_b1',
    'Витамин B1, тиамин': 'vitamin_b1',
    'Витамин В2, рибофлавин': 'vitamin_b2',
    'Витамин B2, рибофлавин': 'vitamin_b2',
    'Витамин В3, ниацин': 'vitamin_b3',
    'Витамин B3, ниацин': 'vitamin_b3',
    'Витамин В4, холин': 'vitamin_b4',
    'Витамин B4, холин': 'vitamin_b4',
    'Витамин В5, пантотеновая': 'vitamin_b5',
    'Витамин B5, пантотеновая': 'vitamin_b5',
    'Витамин В6, пиридоксин': 'vitamin_b6',
    'Витамин B6, пиридоксин': 'vitamin_b6',
    'Витамин В7, биотин': 'vitamin_b7',
    'Витамин B7, биотин': 'vitamin_b7',
    'Витамин Н, биотин': 'vitamin_b7',
    'Витамин H, биотин': 'vitamin_b7',
    'Витамин В9, фолаты': 'vitamin_b9_folate',
    'Витамин B9, фолаты': 'vitamin_b9_folate',
    'Витамин B9, фолиевая кислота': 'vitamin_b9_folate',
    'Витамин В12': 'vitamin_b12',
    'Витамин B12': 'vitamin_b12',
    'Витамин C, аскорбиновая': 'vitamin_c',
    'Витамин C': 'vitamin_c',
    'Витамин D': 'vitamin_d',
    'Витамин Е, альфа токоферол, ТЭ': 'vitamin_e',
    'Витамин E': 'vitamin_e',
    'гамма Токоферол': 'vitamin_e',
    'Витамин К, филлохинон': 'vitamin_k',
    'Витамин K': 'vitamin_k',
    'Витамин РР, НЭ': 'vitamin_b3',
    'Витамин PP, НЭ': 'vitamin_b3',
    'Ниацин': 'vitamin_b3',
    'Бетаин': 'vitamin_b4',

    # ===== МАКРОЭЛЕМЕНТЫ =====
    'Калий, K': 'potassium',
    'Калий': 'potassium',
    'Кальций, Ca': 'calcium',
    'Кальций': 'calcium',
    'Магний, Mg': 'magnesium',
    'Магний': 'magnesium',
    'Натрий, Na': 'sodium',
    'Натрий': 'sodium',
    'Фосфор, P': 'phosphorus',
    'Фосфор': 'phosphorus',
    'Сера, S': 'sulfur',
    'Сера': 'sulfur',
    'Кремний, Si': 'silicon',
    'Кремний': 'silicon',
    'Хлор, Cl': 'chlorine',
    'Хлор': 'chlorine',

    # ===== МИКРОЭЛЕМЕНТЫ =====
    'Железо, Fe': 'iron',
    'Железо': 'iron',
    'Марганец, Mn': 'manganese',
    'Марганец': 'manganese',
    'Медь, Cu': 'copper',
    'Медь': 'copper',
    'Селен, Se': 'selenium',
    'Селен': 'selenium',
    'Цинк, Zn': 'zinc',
    'Цинк': 'zinc',
    'Алюминий, Al': 'aluminum',
    'Алюминий': 'aluminum',
    'Йод, I': 'iodine',
    'Йод': 'iodine',
    'Кобальт, Co': 'cobalt',
    'Кобальт': 'cobalt',
    'Литий, Li': 'lithium',
    'Литий': 'lithium',
    'Молибден, Mo': 'molybdenum',
    'Молибден': 'molybdenum',
    'Никель, Ni': 'nickel',
    'Никель': 'nickel',
    'Рубидий, Rb': 'rubidium',
    'Рубидий': 'rubidium',
    'Фтор, F': 'fluorine',
    'Фтор': 'fluorine',
    'Хром, Cr': 'chromium',
    'Хром': 'chromium',

    # ===== ОРГАНИЧЕСКИЕ КИСЛОТЫ =====
    'Органические кислоты': 'organic_acids',

    # ===== ЖИРНЫЕ КИСЛОТЫ =====
    'Насыщенные жирные кислоты': 'saturated_fat',
    'Трансжиры': 'trans_fat',
    'Холестерин': 'cholesterol',
    'Омега-3 жирные кислоты': 'omega_3',
    'Омега-3': 'omega_3',
    'Омега-6 жирные кислоты': 'omega_6',
    'Омега-6': 'omega_6',

    # ===== АМИНОКИСЛОТЫ (добавляем для полноты) =====
    'Аргинин*': 'arginine',
    'Аргинин': 'arginine',
    'Валин': 'valine',
    'Гистидин*': 'histidine',
    'Гистидин': 'histidine',
    'Изолейцин': 'isoleucine',
    'Лейцин': 'leucine',
    'Лизин': 'lysine',
    'Метионин': 'methionine',
    'Треонин': 'threonine',
    'Триптофан': 'tryptophan',
    'Фенилаланин': 'phenylalanine',
    'Аланин': 'alanine',
    'Аспарагиновая кислота': 'aspartic_acid',
    'Глицин': 'glycine',
    'Глутаминовая кислота': 'glutamic_acid',
    'Пролин': 'proline',
    'Серин': 'serine',
    'Тирозин': 'tyrosine',
    'Цистеин': 'cysteine',
}

# Поля модели AbstractIngredient (полный список)
MODEL_FIELDS = {
    'calories', 'protein', 'fat', 'carbohydrates',
    'fiber', 'sugar', 'water', 'ash', 'starch',
    'vitamin_a', 'beta_carotene',
    'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b4',
    'vitamin_b5', 'vitamin_b6', 'vitamin_b7', 'vitamin_b9_folate', 'vitamin_b12',
    'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k',
    'potassium', 'calcium', 'magnesium', 'sodium', 'phosphorus',
    'sulfur', 'silicon', 'chlorine',
    'iron', 'manganese', 'copper', 'selenium', 'zinc',
    'aluminum', 'boron', 'vanadium', 'iodine', 'cobalt',
    'lithium', 'molybdenum', 'nickel', 'rubidium', 'fluorine', 'chromium',
    'organic_acids',
    'saturated_fat', 'trans_fat', 'cholesterol', 'omega_3', 'omega_6',
}

# Поля, которые НЕ нужно обновлять (только для новых записей)
SKIP_FIELDS = {
    'id', 'created_at', 'updated_at', 'category',
    'description', 'description_ru', 'image',
    'data_source', 'fdc_id', 'is_active', 'name_normalized'
}


# ==================== ФУНКЦИИ ====================

def extract_product_name(filename):
    """Извлекает имя продукта из имени файла."""
    base = os.path.basename(filename)
    base = base.replace('.html', '').replace('.htm', '')
    parts = base.split('_', 2)
    if len(parts) >= 3:
        name = parts[2].strip()
        name = name.replace('%20', ' ').replace('%D0%B0', 'а')
        name = re.sub(r'[^\w\s\-.,()]', '', name)
        return name
    return base


def parse_nutrient_value(text):
    """Парсит значение из текста."""
    if not text or text.strip() == '' or text.strip() == '~':
        return None

    text = text.strip().replace(',', '.')

    # Убираем всё после "<" если есть
    if '<' in text:
        text = text.split('<')[0].strip()

    # Ищем число
    match = re.search(r'([\d.]+)', text)
    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def parse_nutrients_from_table(html_content):
    """Парсит таблицу с нутриентами."""
    soup = BeautifulSoup(html_content, 'lxml')
    table = soup.select_one('table.mzr-table.mzr-table-border.mzr-tc-chemical-table')

    if not table:
        table = soup.select_one('table.mzr-table')

    if not table:
        return {}

    nutrients = {}
    rows = table.find_all('tr')

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 2:
            continue

        first_col = cols[0].get_text(strip=True)
        if first_col == 'Нутриент':
            continue

        td = cols[0]
        if 'mzr-tc-chemical-group' in td.get('class', []):
            continue

        value_text = cols[1].get_text(strip=True)
        if not value_text or value_text == '' or value_text == '~':
            continue

        value = parse_nutrient_value(value_text)
        if value is not None:
            nutrients[first_col] = value

    return nutrients


def import_from_html(file_path):
    """
    Импортирует данные из одного HTML-файла в AbstractIngredient.
    """
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return None

    product_name = extract_product_name(file_path)
    print(f"\n📄 Обработка: {product_name}")

    # Проверяем существование
    existing = AbstractIngredient.objects.filter(name=product_name).first()
    if existing:
        print(f"  ⚠️ Уже существует (ID: {existing.id})")
        return existing

    # Читаем HTML
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"  ❌ Ошибка чтения файла: {e}")
        return None

    # Парсим нутриенты
    nutrients = parse_nutrients_from_table(html_content)
    if not nutrients:
        print(f"  ⚠️ Нет данных")
        return None

    # Создаем объект
    abstract = AbstractIngredient(
        name=product_name,
        data_source='health-diet.ru',
        description=f'Химический состав продукта "{product_name}"',
        is_active=True
    )

    # Заполняем поля
    fields_updated = []

    for nutrient_name, value in nutrients.items():
        field_name = None

        # Прямое совпадение
        if nutrient_name in NUTRIENT_MAPPING:
            field_name = NUTRIENT_MAPPING[nutrient_name]

        # Частичное совпадение
        if not field_name:
            for key, field in NUTRIENT_MAPPING.items():
                if key.lower() in nutrient_name.lower() or nutrient_name.lower() in key.lower():
                    field_name = field
                    break

        # Проверяем, что поле существует
        if field_name and field_name in MODEL_FIELDS:
            setattr(abstract, field_name, value)
            fields_updated.append(field_name)

    # Сохраняем
    try:
        abstract.save()
        print(f"  ✅ Создан (ID: {abstract.id})")
        print(f"  📊 Нутриентов: {len(nutrients)}, обновлено полей: {len(fields_updated)}")

        # Показываем КБЖУ
        main = []
        for name in ['calories', 'protein', 'fat', 'carbohydrates']:
            val = getattr(abstract, name, None)
            if val is not None:
                main.append(f"{name}={val}")
        if main:
            print(f"  📊 КБЖУ: {', '.join(main)}")

        return abstract

    except Exception as e:
        print(f"  ❌ Ошибка сохранения: {e}")
        return None


def import_all_from_folder():
    """Импортирует все HTML-файлы из папки."""
    if not os.path.exists(HTML_FOLDER):
        print(f"❌ Папка {HTML_FOLDER} не найдена!")
        return

    html_files = glob.glob(os.path.join(HTML_FOLDER, 'food_*.html'))
    html_files += glob.glob(os.path.join(HTML_FOLDER, 'food_*.htm'))

    if not html_files:
        print(f"❌ Файлы не найдены в папке {HTML_FOLDER}")
        return

    print("=" * 70)
    print("🍽️  ИМПОРТ В ABSTRACTINGREDIENT")
    print("=" * 70)
    print(f"📁 Найдено {len(html_files)} файлов")
    print("=" * 70)

    stats = {
        'total': len(html_files),
        'created': 0,
        'skipped': 0,
        'errors': 0,
    }

    for file_path in html_files:
        result = import_from_html(file_path)
        if result:
            stats['created'] += 1
        else:
            name = extract_product_name(file_path)
            if AbstractIngredient.objects.filter(name=name).exists():
                stats['skipped'] += 1
            else:
                stats['errors'] += 1

    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА ИМПОРТА")
    print("=" * 70)
    print(f"  Всего файлов:    {stats['total']}")
    print(f"  Создано:         {stats['created']}")
    print(f"  Пропущено:       {stats['skipped']}")
    print(f"  Ошибок:          {stats['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_from_html(sys.argv[1])
    else:
        import_all_from_folder()