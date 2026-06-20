#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Исправление калорий из HTML файлов HealthDiet
Запуск: python scripts/fix_calories_from_html.py
"""

import os
import sys
import glob
import re
from pathlib import Path
from bs4 import BeautifulSoup
from django.db import transaction

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

# Импортируем модель ПОСЛЕ настройки Django
from kitchen.models import Ingredient


def extract_product_name(filename):
    """Извлекает имя продукта из имени файла."""
    base = os.path.basename(filename)
    base = base.replace('.html', '').replace('.htm', '')
    parts = base.split('_', 2)
    if len(parts) >= 3:
        name = parts[2].strip()
        # Декодируем URL-кодировку
        name = name.replace('%20', ' ').replace('%D0%B0', 'а').replace('%D0%B1', 'б')
        name = name.replace('%D0%B2', 'в').replace('%D0%B3', 'г').replace('%D0%B4', 'д')
        name = name.replace('%D0%B5', 'е').replace('%D0%B6', 'ж').replace('%D0%B7', 'з')
        name = name.replace('%D0%B8', 'и').replace('%D0%B9', 'й').replace('%D0%BA', 'к')
        name = name.replace('%D0%BB', 'л').replace('%D0%BC', 'м').replace('%D0%BD', 'н')
        name = name.replace('%D0%BE', 'о').replace('%D0%BF', 'п').replace('%D1%80', 'р')
        name = name.replace('%D1%81', 'с').replace('%D1%82', 'т').replace('%D1%83', 'у')
        name = name.replace('%D1%84', 'ф').replace('%D1%85', 'х').replace('%D1%86', 'ц')
        name = name.replace('%D1%87', 'ч').replace('%D1%88', 'ш').replace('%D1%89', 'щ')
        name = name.replace('%D1%8A', 'ъ').replace('%D1%8B', 'ы').replace('%D1%8C', 'ь')
        name = name.replace('%D1%8D', 'э').replace('%D1%8E', 'ю').replace('%D1%8F', 'я')
        return name
    return base


def parse_nutrients_from_html(html_content):
    """Парсит КБЖУ из HTML файла"""
    soup = BeautifulSoup(html_content, 'lxml')

    # Ищем таблицу
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

        name = cols[0].get_text(strip=True)

        # Ищем span с данными
        value_span = cols[1].find('span')
        if value_span:
            value_text = value_span.get_text(strip=True)
        else:
            value_text = cols[1].get_text(strip=True)

        # Парсим значение
        if 'Калорийность' in name or 'Энергетическая' in name:
            match = re.search(r'([\d.]+)', value_text)
            if match:
                try:
                    nutrients['calories'] = float(match.group(1))
                except:
                    pass

        if 'Белки' in name and not 'Витамин' in name:
            match = re.search(r'([\d.]+)', value_text)
            if match:
                try:
                    nutrients['protein'] = float(match.group(1))
                except:
                    pass

        if 'Жиры' in name and not 'Насыщенные' in name and not 'Трансжиры' in name:
            match = re.search(r'([\d.]+)', value_text)
            if match:
                try:
                    nutrients['fat'] = float(match.group(1))
                except:
                    pass

        if 'Углеводы' in name and not 'Моно' in name and not 'Крахмал' in name and not 'Углеводы (общие)' in name:
            match = re.search(r'([\d.]+)', value_text)
            if match:
                try:
                    nutrients['carbohydrates'] = float(match.group(1))
                except:
                    pass

    return nutrients


@transaction.atomic
def fix_calories():
    """Исправляет калории из HTML файлов"""
    print("=" * 70)
    print("🔥 ИСПРАВЛЕНИЕ КАЛОРИЙ ИЗ HTML")
    print("=" * 70)

    html_folder = '../../HealthDietParser/data/full_pages'

    if not os.path.exists(html_folder):
        print(f"❌ Папка {html_folder} не найдена!")
        return

    html_files = glob.glob(os.path.join(html_folder, 'food_*.html'))
    html_files += glob.glob(os.path.join(html_folder, 'food_*.htm'))

    if not html_files:
        print(f"❌ Файлы не найдены в папке {html_folder}")
        return

    print(f"📁 Найдено {len(html_files)} файлов")
    print("=" * 70)

    stats = {
        'total': len(html_files),
        'updated': 0,
        'skipped': 0,
        'errors': 0,
        'no_calories': 0,
        'not_found_in_db': 0,
    }

    # Обрабатываем все файлы
    for i, file_path in enumerate(html_files, 1):
        try:
            # Извлекаем имя продукта
            product_name = extract_product_name(file_path)

            # Ищем ингредиент в БД
            ingredient = Ingredient.objects.filter(name=product_name).first()
            if not ingredient:
                stats['not_found_in_db'] += 1
                if stats['not_found_in_db'] <= 10:  # Показываем первые 10
                    print(f"⚠️ Ингредиент не найден: {product_name[:50]}")
                continue

            # Читаем HTML
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Парсим КБЖУ
            nutrients = parse_nutrients_from_html(html_content)

            # Проверяем наличие калорий
            if not nutrients or 'calories' not in nutrients:
                stats['no_calories'] += 1
                continue

            # Обновляем поля (только если они пустые)
            updated = False
            for field in ['calories', 'protein', 'fat', 'carbohydrates']:
                if field in nutrients:
                    current = getattr(ingredient, field)
                    new_value = nutrients[field]
                    # Обновляем если:
                    # 1. Текущее значение None или 0
                    # 2. Новое значение есть и не 0
                    if (current is None or current == 0) and new_value is not None and new_value > 0:
                        setattr(ingredient, field, new_value)
                        updated = True

            if updated:
                ingredient.save()
                stats['updated'] += 1
                if stats['updated'] <= 50:  # Показываем первые 50 обновлений
                    print(f"✅ {i}. {product_name[:40]}: {nutrients.get('calories', '?')} ккал")

            # Прогресс
            if i % 100 == 0:
                print(f"📊 Прогресс: {i}/{len(html_files)} | Обновлено: {stats['updated']}")

        except Exception as e:
            stats['errors'] += 1
            if stats['errors'] <= 10:
                print(f"❌ Ошибка в файле {os.path.basename(file_path)}: {e}")

    # Итог
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    print(f"  Всего файлов:        {stats['total']}")
    print(f"  Обновлено:           {stats['updated']}")
    print(f"  Пропущено (нет калорий): {stats['no_calories']}")
    print(f"  Не найдено в БД:     {stats['not_found_in_db']}")
    print(f"  Ошибок:              {stats['errors']}")

    # Проверяем результат
    has_calories = Ingredient.objects.filter(calories__isnull=False).count()
    total = Ingredient.objects.count()
    print("\n" + "=" * 70)
    print("📊 РЕЗУЛЬТАТ ПОСЛЕ ИСПРАВЛЕНИЯ")
    print("=" * 70)
    print(f"  Ингредиентов с калориями: {has_calories}")
    print(f"  Процент: {has_calories / total * 100:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    fix_calories()