#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Исправление калорий и макронутриентов из HTML (только в AbstractIngredient)
Запуск: python scripts/fix_calories_from_html.py
"""

import os
import sys
import glob
import re
from pathlib import Path
from bs4 import BeautifulSoup

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import Ingredient, AbstractIngredient


def extract_product_name(filename):
    """Извлекает имя продукта из имени файла."""
    base = os.path.basename(filename)
    base = base.replace('.html', '').replace('.htm', '')
    parts = base.split('_', 2)
    if len(parts) >= 3:
        name = parts[2].strip()
        name = name.replace('%20', ' ').replace('%D0%B0', 'а')
        return name
    return base


def parse_main_nutrients(html_content):
    """Парсит только калории, белки, жиры, углеводы"""
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

        name = cols[0].get_text(strip=True)
        value_span = cols[1].find('span')
        value_text = value_span.get_text(strip=True) if value_span else cols[1].get_text(strip=True)

        match = re.search(r'([\d.]+)', value_text)
        if not match:
            continue

        value = float(match.group(1))

        if 'Калорийность' in name or 'Энергетическая' in name:
            nutrients['calories'] = value
        elif 'Белки' in name and not 'Витамин' in name:
            nutrients['protein'] = value
        elif 'Жиры' in name and not 'Насыщенные' in name and not 'Трансжиры' in name:
            nutrients['fat'] = value
        elif 'Углеводы' in name and not 'Моно' in name and not 'Крахмал' in name:
            nutrients['carbohydrates'] = value

    return nutrients


def fix_calories():
    """Исправляет калории и макронутриенты (только в AbstractIngredient)"""
    print("=" * 70)
    print("🔥 ИСПРАВЛЕНИЕ КАЛОРИЙ ИЗ HTML (ТОЛЬКО ABSTRACT)")
    print("=" * 70)

    html_folder = '../../HealthDietParser/data/full_pages'

    if not os.path.exists(html_folder):
        print(f"❌ Папка {html_folder} не найдена!")
        return

    html_files = glob.glob(os.path.join(html_folder, 'food_*.html'))
    html_files += glob.glob(os.path.join(html_folder, 'food_*.htm'))

    print(f"📁 Найдено {len(html_files)} файлов")
    print("=" * 70)

    stats = {
        'total': len(html_files),
        'updated': 0,
        'not_found': 0,
        'no_data': 0,
        'errors': 0,
    }

    for i, file_path in enumerate(html_files, 1):
        try:
            product_name = extract_product_name(file_path)

            # Ищем AbstractIngredient
            abstract = AbstractIngredient.objects.filter(name=product_name).first()
            if not abstract:
                stats['not_found'] += 1
                # Показываем первые 10 не найденных
                if stats['not_found'] <= 10:
                    print(f"⚠️ Ингредиент не найден: {product_name[:50]}")
                continue

            # Читаем HTML
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            nutrients = parse_main_nutrients(html_content)

            if not nutrients:
                stats['no_data'] += 1
                continue

            # Обновляем только AbstractIngredient
            updated = False
            for field, value in nutrients.items():
                if hasattr(abstract, field):
                    current = getattr(abstract, field)
                    if current is None or current == 0:
                        setattr(abstract, field, value)
                        updated = True

            if updated:
                abstract.save()
                stats['updated'] += 1

                if stats['updated'] % 100 == 0:
                    print(f"📊 Прогресс: {stats['updated']}/{stats['total']}")

        except Exception as e:
            stats['errors'] += 1
            if stats['errors'] <= 10:
                print(f"❌ Ошибка: {e}")

    # Итог
    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА")
    print("=" * 70)
    print(f"  Всего файлов: {stats['total']}")
    print(f"  Обновлено AbstractIngredient: {stats['updated']}")
    print(f"  Не найдено в БД: {stats['not_found']}")
    print(f"  Нет данных в HTML: {stats['no_data']}")
    print(f"  Ошибок: {stats['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    fix_calories()