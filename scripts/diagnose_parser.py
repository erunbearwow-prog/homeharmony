#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Диагностика парсера HealthDiet
Запуск: python scripts/diagnose_parser.py
"""

import os
import sys
import glob
from pathlib import Path
from bs4 import BeautifulSoup

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import Ingredient


def diagnose_parser():
    """Диагностика парсера"""
    print("=" * 70)
    print("🔍 ДИАГНОСТИКА ПАРСЕРА")
    print("=" * 70)

    # Путь к HTML файлам
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
    print("\n" + "=" * 70)

    # Проверяем первые 10 файлов
    for file_path in html_files[:10]:
        print(f"\n📄 Файл: {os.path.basename(file_path)}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'lxml')

            # 1. Проверяем название
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else "Нет заголовка"
            print(f"   Заголовок: {title[:80]}...")

            # 2. Ищем таблицу
            table = soup.select_one('table.mzr-table.mzr-table-border.mzr-tc-chemical-table')
            if not table:
                table = soup.select_one('table.mzr-table')

            if not table:
                print("   ⚠️ Таблица не найдена!")
                continue

            print(f"   ✅ Таблица найдена")

            # 3. Ищем калорийность
            rows = table.find_all('tr')
            found_calories = False
            found_protein = False
            found_fat = False
            found_carbs = False

            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue

                first_col = cols[0].get_text(strip=True)
                value_text = cols[1].get_text(strip=True)

                # Проверяем наличие ключевых нутриентов
                if 'Калорийность' in first_col or 'Энергетическая' in first_col:
                    found_calories = True
                    print(f"   ✅ Калорийность: {value_text}")

                if 'Белки' in first_col and not 'Витамин' in first_col:
                    found_protein = True
                    print(f"   ✅ Белки: {value_text}")

                if 'Жиры' in first_col and not 'Насыщенные' in first_col and not 'Трансжиры' in first_col:
                    found_fat = True
                    print(f"   ✅ Жиры: {value_text}")

                if 'Углеводы' in first_col and not 'Моно' in first_col and not 'Крахмал' in first_col:
                    found_carbs = True
                    print(f"   ✅ Углеводы: {value_text}")

            # 4. Статистика
            print(f"\n   📊 Найдено:")
            print(f"      Калорийность: {'✅' if found_calories else '❌'}")
            print(f"      Белки: {'✅' if found_protein else '❌'}")
            print(f"      Жиры: {'✅' if found_fat else '❌'}")
            print(f"      Углеводы: {'✅' if found_carbs else '❌'}")

            if not found_calories:
                print("\n   🔍 Ищем калорийность вручную:")
                # Ищем span с itemprop="calories"
                calories_span = soup.find('span', itemprop='calories')
                if calories_span:
                    print(f"      Найдено через itemprop: {calories_span.get_text(strip=True)}")

                # Ищем любые числа с ккал
                import re
                kcal_matches = re.findall(r'(\d+\.?\d*)\s*ккал', html_content)
                if kcal_matches:
                    print(f"      Найдено чисел с ккал: {kcal_matches[:5]}")

            # 5. Проверяем, есть ли такой ингредиент в БД
            # Извлекаем имя из файла
            base = os.path.basename(file_path)
            base = base.replace('.html', '').replace('.htm', '')
            parts = base.split('_', 2)
            product_name = parts[2].strip() if len(parts) >= 3 else base

            ingredient = Ingredient.objects.filter(name=product_name).first()
            if ingredient:
                print(f"\n   📦 В БД:")
                print(f"      Калории: {ingredient.calories}")
                print(f"      Белки: {ingredient.protein}")
                print(f"      Жиры: {ingredient.fat}")
                print(f"      Углеводы: {ingredient.carbohydrates}")
            else:
                print(f"\n   ❌ Ингредиент не найден в БД: {product_name[:50]}")

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")


if __name__ == "__main__":
    diagnose_parser()