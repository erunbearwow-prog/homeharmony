#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для импорта данных из HTML-файлов HealthDiet в AbstractIngredient
Импортирует: название, КБЖУ и все нутриенты (витамины, минералы, жирные кислоты)
Запуск:
    python import_to_abstract.py [путь_к_html_файлу]

Режимы:
    - Если файл не указан: импорт всех файлов из папки
    - Если указан файл: импорт только этого файла

Параметры:
    --force  - полная перезапись всех полей (по умолчанию обновляются только пустые)
"""

import os
import sys
import glob
import re
from bs4 import BeautifulSoup
import django

print("🚀 СКРИПТ ЗАПУЩЕН!")
print(f"Аргументы: {sys.argv}")

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
    'Калорийность (ккал)': 'calories',
    'Калорийность, ккал': 'calories',
    'Калорийность': 'calories',
    'Калорийность (ккал) ': 'calories',
    'Калорийность, ккал ': 'calories',
    'Энергетическая ценность': 'calories',
    'Энергетическая ценность (ккал)': 'calories',
    'Энерг. ценность, ккал': 'calories',
    'калорийность': 'calories',
    'энергетическая ценность': 'calories',
    'Белки': 'protein',
    'белки': 'protein',
    'Белки (г)': 'protein',
    'Жиры': 'fat',
    'жиры': 'fat',
    'Жиры (г)': 'fat',
    'Углеводы': 'carbohydrates',
    'углеводы': 'carbohydrates',
    'Углеводы (г)': 'carbohydrates',
    'Углеводы (общие)': 'carbohydrates',
    'Пищевые волокна': 'fiber',
    'пищевые волокна': 'fiber',
    'Пищевые волокна (г)': 'fiber',
    'Моно- и дисахариды (сахара)': 'sugar',
    'Вода': 'water',
    'Вода (г)': 'water',
    'Зола': 'ash',
    'Крахмал и декстрины': 'starch',
    'Крахмал': 'starch',

    # ===== ВИТАМИНЫ =====
    'Витамин А, РЭ': 'vitamin_a',
    'Витамин A, РЭ': 'vitamin_a',
    'Витамин А, РЭ (мкг)': 'vitamin_a',
    'альфа Каротин': 'vitamin_a',
    'бета Каротин': 'beta_carotene',
    'Бета-каротин': 'beta_carotene',
    'бета Каротин (мг)': 'beta_carotene',
    'бета Криптоксантин': 'beta_carotene',
    'Витамин В1, тиамин': 'vitamin_b1',
    'Витамин B1, тиамин': 'vitamin_b1',
    'Витамин В1, тиамин (мг)': 'vitamin_b1',
    'Витамин В2, рибофлавин': 'vitamin_b2',
    'Витамин B2, рибофлавин': 'vitamin_b2',
    'Витамин В2, рибофлавин (мг)': 'vitamin_b2',
    'Витамин В3, ниацин': 'vitamin_b3',
    'Витамин B3, ниацин': 'vitamin_b3',
    'Витамин В4, холин': 'vitamin_b4',
    'Витамин B4, холин': 'vitamin_b4',
    'Витамин В4, холин (мг)': 'vitamin_b4',
    'Витамин В5, пантотеновая': 'vitamin_b5',
    'Витамин B5, пантотеновая': 'vitamin_b5',
    'Витамин В5, пантотеновая (мг)': 'vitamin_b5',
    'Витамин В6, пиридоксин': 'vitamin_b6',
    'Витамин B6, пиридоксин': 'vitamin_b6',
    'Витамин В6, пиридоксин (мг)': 'vitamin_b6',
    'Витамин В7, биотин': 'vitamin_b7',
    'Витамин B7, биотин': 'vitamin_b7',
    'Витамин Н, биотин': 'vitamin_b7',
    'Витамин H, биотин': 'vitamin_b7',
    'Витамин Н, биотин (мкг)': 'vitamin_b7',
    'Витамин В9, фолаты': 'vitamin_b9_folate',
    'Витамин B9, фолаты': 'vitamin_b9_folate',
    'Витамин B9, фолиевая кислота': 'vitamin_b9_folate',
    'Витамин В9, фолаты (мкг)': 'vitamin_b9_folate',
    'Витамин В12': 'vitamin_b12',
    'Витамин B12': 'vitamin_b12',
    'Витамин В12, кобаламин (мкг)': 'vitamin_b12',
    'Витамин C, аскорбиновая': 'vitamin_c',
    'Витамин C': 'vitamin_c',
    'Витамин C, аскорбиновая (мг)': 'vitamin_c',
    'Витамин D': 'vitamin_d',
    'Витамин D, кальциферол (мкг)': 'vitamin_d',
    'Витамин Е, альфа токоферол, ТЭ': 'vitamin_e',
    'Витамин E': 'vitamin_e',
    'Витамин Е, альфа токоферол, ТЭ (мг)': 'vitamin_e',
    'гамма Токоферол': 'vitamin_e',
    'Витамин К, филлохинон': 'vitamin_k',
    'Витамин K': 'vitamin_k',
    'Витамин К, филлохинон (мкг)': 'vitamin_k',
    'Витамин РР, НЭ': 'vitamin_b3',
    'Витамин PP, НЭ': 'vitamin_b3',
    'Витамин РР, НЭ (мг)': 'vitamin_b3',
    'Ниацин': 'vitamin_b3',
    'Бетаин': 'vitamin_b4',

    # ===== ДОПОЛНИТЕЛЬНЫЕ ВИТАМИНЫ =====
    'Ретиноловый эквивалент': 'retinol_equivalent',
    'РЭ': 'retinol_equivalent',
    'РЭ (мкг)': 'retinol_equivalent',
    'Ниациновый эквивалент': 'niacin_equivalent',
    'НЭ': 'niacin_equivalent',
    'НЭ (мг)': 'niacin_equivalent',
    'Ниациновый эквивалент (НЭ)': 'niacin_equivalent',

    # ===== МАКРОЭЛЕМЕНТЫ =====
    'Калий, K': 'potassium',
    'Калий': 'potassium',
    'Калий, K (мг)': 'potassium',
    'Кальций, Ca': 'calcium',
    'Кальций': 'calcium',
    'Кальций, Ca (мг)': 'calcium',
    'Магний, Mg': 'magnesium',
    'Магний': 'magnesium',
    'Магний, Mg (мг)': 'magnesium',
    'Натрий, Na': 'sodium',
    'Натрий': 'sodium',
    'Натрий, Na (мг)': 'sodium',
    'Фосфор, P': 'phosphorus',
    'Фосфор': 'phosphorus',
    'Фосфор, P (мг)': 'phosphorus',
    'Сера, S': 'sulfur',
    'Сера': 'sulfur',
    'Сера, S (мг)': 'sulfur',
    'Кремний, Si': 'silicon',
    'Кремний': 'silicon',
    'Кремний, Si (мг)': 'silicon',
    'Хлор, Cl': 'chlorine',
    'Хлор': 'chlorine',
    'Хлор, Cl (мг)': 'chlorine',

    # ===== МИКРОЭЛЕМЕНТЫ =====
    'Железо, Fe': 'iron',
    'Железо': 'iron',
    'Железо, Fe (мг)': 'iron',
    'Марганец, Mn': 'manganese',
    'Марганец': 'manganese',
    'Марганец, Mn (мг)': 'manganese',
    'Медь, Cu': 'copper',
    'Медь': 'copper',
    'Медь, Cu (мкг)': 'copper',
    'Селен, Se': 'selenium',
    'Селен': 'selenium',
    'Селен, Se (мкг)': 'selenium',
    'Цинк, Zn': 'zinc',
    'Цинк': 'zinc',
    'Цинк, Zn (мг)': 'zinc',
    'Алюминий, Al': 'aluminum',
    'Алюминий': 'aluminum',
    'Алюминий, Al (мкг)': 'aluminum',
    'Йод, I': 'iodine',
    'Йод': 'iodine',
    'Йод, I (мкг)': 'iodine',
    'Кобальт, Co': 'cobalt',
    'Кобальт': 'cobalt',
    'Кобальт, Co (мкг)': 'cobalt',
    'Литий, Li': 'lithium',
    'Литий': 'lithium',
    'Литий, Li (мкг)': 'lithium',
    'Молибден, Mo': 'molybdenum',
    'Молибден': 'molybdenum',
    'Молибден, Mo (мкг)': 'molybdenum',
    'Никель, Ni': 'nickel',
    'Никель': 'nickel',
    'Никель, Ni (мкг)': 'nickel',
    'Рубидий, Rb': 'rubidium',
    'Рубидий': 'rubidium',
    'Рубидий, Rb (мкг)': 'rubidium',
    'Фтор, F': 'fluorine',
    'Фтор': 'fluorine',
    'Фтор, F (мкг)': 'fluorine',
    'Хром, Cr': 'chromium',
    'Хром': 'chromium',
    'Хром, Cr (мкг)': 'chromium',

    # ===== ОРГАНИЧЕСКИЕ КИСЛОТЫ =====
    'Органические кислоты': 'organic_acids',

    # ===== ЖИРНЫЕ КИСЛОТЫ =====
    'Насыщенные жирные кислоты': 'saturated_fat',
    'Насыщенные жирные кислоты (г)': 'saturated_fat',
    'Трансжиры': 'trans_fat',
    'Трансжиры (г)': 'trans_fat',
    'Холестерин': 'cholesterol',
    'Холестерин (мг)': 'cholesterol',
    'Омега-3 жирные кислоты': 'omega_3',
    'Омега-3': 'omega_3',
    'Омега-3 жирные кислоты (г)': 'omega_3',
    'Омега-6 жирные кислоты': 'omega_6',
    'Омега-6': 'omega_6',
    'Омега-6 жирные кислоты (г)': 'omega_6',
}

# Поля модели AbstractIngredient (полный список)
MODEL_FIELDS = {
    'calories', 'protein', 'fat', 'carbohydrates',
    'fiber', 'sugar', 'water', 'ash', 'starch',
    'vitamin_a', 'beta_carotene',
    'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b4',
    'vitamin_b5', 'vitamin_b6', 'vitamin_b7', 'vitamin_b9_folate', 'vitamin_b12',
    'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k',
    'retinol_equivalent',
    'niacin_equivalent',
    'potassium', 'calcium', 'magnesium', 'sodium', 'phosphorus',
    'sulfur', 'silicon', 'chlorine',
    'iron', 'manganese', 'copper', 'selenium', 'zinc',
    'aluminum', 'boron', 'vanadium', 'iodine', 'cobalt',
    'lithium', 'molybdenum', 'nickel', 'rubidium', 'fluorine', 'chromium',
    'organic_acids',
    'saturated_fat', 'trans_fat', 'cholesterol', 'omega_3', 'omega_6',
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

    # Убираем всё после "±" если есть
    if '±' in text:
        text = text.split('±')[0].strip()

    # Убираем всё после "(" если есть
    if '(' in text:
        text = text.split('(')[0].strip()

    # Убираем всё после "—" если есть
    if '—' in text:
        text = text.split('—')[0].strip()

    # Ищем число
    match = re.search(r'([\d.]+)', text)
    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def get_field_name(nutrient_name):
    """
    Возвращает имя поля модели для нутриента.
    """
    if not nutrient_name:
        return None

    # Очищаем от лишних пробелов
    nutrient_name = nutrient_name.strip()

    # 1. Прямое совпадение
    if nutrient_name in NUTRIENT_MAPPING:
        return NUTRIENT_MAPPING[nutrient_name]

    # 2. Частичное совпадение (игнорируем регистр)
    nutrient_lower = nutrient_name.lower()
    for key, field in NUTRIENT_MAPPING.items():
        if key.lower() in nutrient_lower or nutrient_lower in key.lower():
            return field

    # 3. Специальная обработка для калорийности
    if 'калорийн' in nutrient_lower or 'энергетич' in nutrient_lower:
        return 'calories'

    # 4. Специальная обработка для белков
    if 'белк' in nutrient_lower:
        return 'protein'

    # 5. Специальная обработка для жиров
    if 'жир' in nutrient_lower:
        return 'fat'

    # 6. Специальная обработка для углеводов
    if 'углевод' in nutrient_lower:
        return 'carbohydrates'

    return None


def parse_nutrients_from_table(html_content):
    """Парсит таблицу с нутриентами."""
    soup = BeautifulSoup(html_content, 'lxml')

    # Ищем все строки с нутриентами
    rows = soup.find_all('tr')

    nutrients = {}
    print(f"  🔍 Найдено строк в таблице: {len(rows)}")

    for row in rows:
        # Проверяем, что строка содержит ячейки
        tds = row.find_all('td')
        if len(tds) < 3:
            continue

        # Проверяем, что первая ячейка содержит текст (не пустая)
        name_cell = tds[0]
        name = name_cell.get_text(strip=True)

        # Пропускаем заголовки
        if not name or name == 'Нутриент' or name == 'Пищевая ценность' or name == 'Нутриенты':
            continue

        # Проверяем, что вторая ячейка содержит число
        value_cell = tds[1]
        value_text = value_cell.get_text(strip=True)

        if not value_text or value_text == '' or value_text == '~':
            continue

        # Парсим значение
        value = parse_nutrient_value(value_text)
        if value is not None:
            # Специальная обработка для основных нутриентов
            name_lower = name.lower()
            if 'калорийн' in name_lower or 'энергетич' in name_lower:
                # Если калорийность уже есть, не перезаписываем (берём первое значение)
                if 'calories' not in nutrients:
                    nutrients['calories'] = value
                    print(f"  ✅ Найдена калорийность: {value}")
            elif 'белк' in name_lower:
                nutrients['protein'] = value
            elif 'жир' in name_lower and 'насыщ' not in name_lower and 'транс' not in name_lower:
                nutrients['fat'] = value
            elif 'углевод' in name_lower:
                nutrients['carbohydrates'] = value
            else:
                # Для остальных используем мэппинг
                field_name = get_field_name(name)
                if field_name and field_name in MODEL_FIELDS:
                    # Если поле уже есть, не перезаписываем
                    if field_name not in nutrients:
                        nutrients[field_name] = value

    print(f"  📊 Всего найдено нутриентов: {len(nutrients)}")

    # Проверяем основные нутриенты
    main = []
    for n in ['calories', 'protein', 'fat', 'carbohydrates']:
        if n in nutrients:
            main.append(f"{n}={nutrients[n]}")
    if main:
        print(f"  📊 Основные нутриенты: {', '.join(main)}")
    else:
        print("  ⚠️ Основные нутриенты (КБЖУ) не найдены!")

    return nutrients


def import_from_html(file_path, update_empty_only=True):
    """
    Импортирует данные из одного HTML-файла в AbstractIngredient.

    Args:
        file_path: путь к HTML-файлу
        update_empty_only: если True, обновляет только пустые поля
                           если False, перезаписывает все поля
    """
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return None

    product_name = extract_product_name(file_path)
    print(f"\n📄 Обработка: {product_name}")

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

    # Проверяем существование
    existing = AbstractIngredient.objects.filter(name=product_name).first()

    if existing:
        # ===== ОБНОВЛЕНИЕ СУЩЕСТВУЮЩЕЙ ЗАПИСИ =====
        print(f"  🔄 Обновление существующей записи (ID: {existing.id})")
        abstract = existing

        fields_updated = []
        fields_skipped = []

        for nutrient_name, value in nutrients.items():
            # Определяем поле для этого нутриента
            field_name = None

            # Специальная обработка для случаев, когда ключ уже является именем поля
            if nutrient_name in MODEL_FIELDS:
                field_name = nutrient_name
            else:
                field_name = get_field_name(nutrient_name)

            if not field_name or field_name not in MODEL_FIELDS:
                continue

            current_value = getattr(abstract, field_name, None)

            if update_empty_only:
                # Обновляем только если поле пустое
                if current_value is None or current_value == 0:
                    setattr(abstract, field_name, value)
                    fields_updated.append(f"{field_name}={value}")
                else:
                    fields_skipped.append(f"{field_name}={current_value}")
            else:
                # Перезаписываем все поля
                setattr(abstract, field_name, value)
                fields_updated.append(f"{field_name}={value}")

        # Проверяем, что калорийность попала в обновления
        if 'calories' not in str(fields_updated) and 'calories' in nutrients:
            # Если калорийность не обновилась, добавляем принудительно
            setattr(abstract, 'calories', nutrients['calories'])
            fields_updated.append(f"calories={nutrients['calories']} (принудительно)")

        try:
            abstract.save()
            print(f"  ✅ Обновлён (ID: {abstract.id})")

            if fields_updated:
                print(f"  📊 Обновлено полей: {len(fields_updated)}")
                if len(fields_updated) <= 10:
                    print(f"     {', '.join(fields_updated)}")
                else:
                    print(f"     {', '.join(fields_updated[:10])}... (+{len(fields_updated) - 10} ещё)")

            if fields_skipped and update_empty_only:
                print(f"  ⏭️ Пропущено (уже заполнено): {len(fields_skipped)}")
                if len(fields_skipped) <= 5:
                    print(f"     {', '.join(fields_skipped)}")

            # Показываем КБЖУ (включая calories, даже если = 0)
            main = []
            for name in ['calories', 'protein', 'fat', 'carbohydrates']:
                val = getattr(abstract, name, None)
                if val is not None:
                    main.append(f"{name}={val}")
            if main:
                print(f"  📊 КБЖУ (все значения): {', '.join(main)}")
            else:
                print(f"  ⚠️ КБЖУ не заполнено!")

            return abstract

        except Exception as e:
            print(f"  ❌ Ошибка обновления: {e}")
            return None

    else:
        # ===== СОЗДАНИЕ НОВОЙ ЗАПИСИ =====
        abstract = AbstractIngredient(
            name=product_name,
            data_source='health-diet.ru',
            description=f'Химический состав продукта "{product_name}"',
            is_active=True
        )

        fields_updated = []

        for nutrient_name, value in nutrients.items():
            field_name = get_field_name(nutrient_name)
            if field_name and field_name in MODEL_FIELDS:
                setattr(abstract, field_name, value)
                fields_updated.append(field_name)

        try:
            abstract.save()
            print(f"  ✅ Создан (ID: {abstract.id})")
            print(f"  📊 Нутриентов: {len(nutrients)}, обновлено полей: {len(fields_updated)}")

            # Показываем КБЖУ (включая calories, даже если = 0)
            main = []
            for name in ['calories', 'protein', 'fat', 'carbohydrates']:
                val = getattr(abstract, name, None)
                if val is not None:
                    main.append(f"{name}={val}")
            if main:
                print(f"  📊 КБЖУ (все значения): {', '.join(main)}")
            else:
                print(f"  ⚠️ КБЖУ не заполнено!")

            return abstract

        except Exception as e:
            print(f"  ❌ Ошибка сохранения: {e}")
            return None


def import_all_from_folder(update_empty_only=True):
    """
    Импортирует все HTML-файлы из папки.

    Args:
        update_empty_only: если True, обновляет только пустые поля
    """
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
    if update_empty_only:
        print("📝 Режим: обновление только пустых полей")
    else:
        print("📝 Режим: полная перезапись всех полей")
    print("=" * 70)
    print(f"📁 Найдено {len(html_files)} файлов")
    print("=" * 70)

    stats = {
        'total': len(html_files),
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0,
        'no_data': 0,
    }

    for file_path in html_files:
        product_name = extract_product_name(file_path)

        # Проверяем, существует ли уже запись
        existing = AbstractIngredient.objects.filter(name=product_name).first()

        result = import_from_html(file_path, update_empty_only)

        if result:
            if existing:
                stats['updated'] += 1
            else:
                stats['created'] += 1
        else:
            # Проверяем, почему не удалось импортировать
            if AbstractIngredient.objects.filter(name=product_name).exists():
                stats['skipped'] += 1
            else:
                stats['errors'] += 1

    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА ИМПОРТА")
    print("=" * 70)
    print(f"  Всего файлов:    {stats['total']}")
    print(f"  Создано:         {stats['created']}")
    print(f"  Обновлено:       {stats['updated']}")
    print(f"  Пропущено:       {stats['skipped']}")
    print(f"  Ошибок:          {stats['errors']}")
    print("=" * 70)


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    # Парсим аргументы командной строки
    update_empty_only = True
    if '--force' in sys.argv:
        update_empty_only = False
        sys.argv.remove('--force')

    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        # Импорт одного файла
        import_from_html(sys.argv[1], update_empty_only)
    else:
        # Импорт всех файлов из папки
        import_all_from_folder(update_empty_only)

    print("\n" + "=" * 70)
    print("🏁 ИМПОРТ ЗАВЕРШЁН")
    print("=" * 70)