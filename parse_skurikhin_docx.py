#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Универсальный парсер справочника Скурихина
Автоматически определяет структуру таблицы
"""

import os
import re
import json
import argparse
from datetime import datetime
from docx import Document


class SkurikhinParserUniversal:
    """Универсальный парсер справочника Скурихина"""

    def __init__(self, file_path):
        self.file_path = file_path
        self.doc = None
        self.products = []
        self.current_category = {}
        self.current_code = None
        self.current_name = None

        # Определяем маппинг колонок после анализа
        self.column_mapping = {}

    def parse(self):
        print(f"📄 Чтение файла: {self.file_path}")

        if not os.path.exists(self.file_path):
            print(f"❌ Файл не найден: {self.file_path}")
            return []

        try:
            self.doc = Document(self.file_path)
        except Exception as e:
            print(f"❌ Ошибка открытия файла: {e}")
            return []

        for table_idx, table in enumerate(self.doc.tables):
            print(f"  📊 Обработка таблицы #{table_idx + 1}")
            self._parse_table(table)

        # Объединяем дубликаты по коду
        merged = self._merge_by_code()
        print(f"✅ Найдено продуктов: {len(merged)}")
        return merged

    def _parse_table(self, table):
        """Парсинг таблицы с автоопределением структуры"""
        rows_data = []
        for row in table.rows:
            row_texts = [cell.text.strip() for cell in row.cells]
            rows_data.append(row_texts)

        rows_data = [r for r in rows_data if any(r)]
        if not rows_data:
            return

        # Определяем структуру таблицы
        self._analyze_structure(rows_data)

        # Парсим строки
        i = 0
        while i < len(rows_data):
            row = rows_data[i]

            # Пропускаем заголовки
            if self._is_header_row(row):
                i += 1
                continue

            # Проверяем категорию
            if self._is_category_row(row):
                self._parse_category(row)
                i += 1
                continue

            # Проверяем продукт
            if self._is_product_row(row):
                self._parse_product(row)
                i += 1
                continue

            i += 1

    def _analyze_structure(self, rows):
        """Анализирует структуру таблицы: где код, название, порция, нутриенты"""
        # Ищем строку с заголовками
        header_row = None
        for row in rows[:5]:
            row_text = ' '.join(row)
            if 'Код' in row_text and 'Продукты' in row_text:
                header_row = row
                break

        if not header_row:
            return

        # Определяем индексы колонок
        for idx, cell in enumerate(header_row):
            cell_lower = cell.lower()
            if 'код' in cell_lower:
                self.column_mapping['code'] = idx
            elif 'продукт' in cell_lower or 'название' in cell_lower:
                self.column_mapping['name'] = idx
            elif 'порц' in cell_lower:
                self.column_mapping['portion'] = idx
            elif 'вода' in cell_lower:
                self.column_mapping['water'] = idx
            elif 'бел' in cell_lower and 'ж' not in cell_lower:
                self.column_mapping['protein'] = idx
            elif 'жир' in cell_lower and 'насыщ' not in cell_lower:
                self.column_mapping['fat'] = idx
            elif 'нжк' in cell_lower:
                self.column_mapping['saturated_fat'] = idx
            elif 'хол' in cell_lower:
                self.column_mapping['cholesterol'] = idx
            elif 'мдс' in cell_lower:
                self.column_mapping['sugar'] = idx
            elif 'кр' in cell_lower and 'рахм' not in cell_lower:
                self.column_mapping['starch'] = idx
            elif 'угл' in cell_lower:
                self.column_mapping['carbohydrates'] = idx
            elif 'пв' in cell_lower:
                self.column_mapping['fiber'] = idx
            elif 'ок' in cell_lower:
                self.column_mapping['organic_acids'] = idx
            elif 'зол' in cell_lower:
                self.column_mapping['ash'] = idx
            elif 'na' in cell_lower:
                self.column_mapping['sodium'] = idx
            elif 'к' in cell_lower and 'алий' not in cell_lower:
                self.column_mapping['potassium'] = idx
            elif 'са' in cell_lower:
                self.column_mapping['calcium'] = idx
            elif 'мд' in cell_lower or 'mg' in cell_lower:
                self.column_mapping['magnesium'] = idx
            elif 'р' in cell_lower and 'э' not in cell_lower:
                self.column_mapping['phosphorus'] = idx
            elif 'fe' in cell_lower:
                self.column_mapping['iron'] = idx
            elif 'а' in cell_lower and 'витам' in cell_lower:
                self.column_mapping['vitamin_a'] = idx
            elif 'кар' in cell_lower:
                self.column_mapping['beta_carotene'] = idx
            elif 'рэ' in cell_lower:
                self.column_mapping['retinol_equivalent'] = idx
            elif 'тэ' in cell_lower or 'токофер' in cell_lower:
                self.column_mapping['vitamin_e'] = idx
            elif 'b1' in cell_lower or 'в1' in cell_lower:
                self.column_mapping['vitamin_b1'] = idx
            elif 'b2' in cell_lower or 'в2' in cell_lower:
                self.column_mapping['vitamin_b2'] = idx
            elif 'рр' in cell_lower:
                self.column_mapping['vitamin_b3'] = idx
            elif 'нэ' in cell_lower:
                self.column_mapping['niacin_equivalent'] = idx
            elif 'с' in cell_lower and 'витам' in cell_lower:
                self.column_mapping['vitamin_c'] = idx
            elif 'эц' in cell_lower or 'энерг' in cell_lower:
                self.column_mapping['calories'] = idx

        print(f"    🔍 Найдено колонок: {list(self.column_mapping.keys())}")

    def _is_header_row(self, row):
        if not row:
            return False
        row_text = ' '.join(row)
        return 'Код' in row_text and 'Продукты' in row_text

    def _is_category_row(self, row):
        if not row:
            return False
        first_cell = row[0].strip()
        return bool(re.match(r'^\d+(?:\.\d+){0,2}$', first_cell)) and len(row[0]) < 10

    def _parse_category(self, row):
        code = row[0].strip()
        # Ищем название категории в строке
        name = ''
        for cell in row[1:]:
            if cell.strip() and not re.match(r'^\d+(?:\.\d+)*$', cell.strip()):
                name = cell.strip()
                break

        name = re.sub(r'[«»"]', '', name).strip()
        name = re.sub(r'^Таблица\s+\d+\.\s*', '', name)

        depth = len(code.split('.'))

        if depth == 1:
            self.current_category = {
                'level_0': f"{code}. {name}",
                'level_1': None,
                'level_2': None,
            }
        elif depth == 2:
            self.current_category['level_1'] = f"{code}. {name}"
        elif depth == 3:
            self.current_category['level_2'] = f"{code}. {name}"

    def _is_product_row(self, row):
        if not row:
            return False
        first_cell = row[0].strip()
        return bool(re.match(r'^\d+(?:\.\d+){3,}$', first_cell))

    def _parse_product(self, row):
        code = row[0].strip()

        # Ищем название продукта
        name = ''
        for i, cell in enumerate(row):
            if i == 0:
                continue
            if cell.strip() and not re.match(r'^[\d.]+$', cell.strip()) and not re.match(r'^%с\.п\.', cell.strip()):
                if not name:
                    name = cell.strip()
                elif len(cell.strip()) > 5 and len(name) < 10:
                    name = cell.strip()

        if not name:
            name = f"Продукт {code}"

        # Очищаем название
        name = re.sub(r'\s*(100|200|300|%с\.п\.\s*\d+)\s*', '', name).strip()
        name = re.sub(r'\s+', ' ', name).strip()

        product = {
            'code': code,
            'name': name,
            'category': self.current_category.copy(),
            'values': {}
        }

        # Парсим значения
        for field, col_idx in self.column_mapping.items():
            if col_idx < len(row):
                value = self._parse_number(row[col_idx])
                if value is not None:
                    product['values'][field] = value

        # Если есть значения, добавляем продукт
        if product['values']:
            self.products.append(product)
        else:
            # Пробуем найти значения в следующей строке (для %с.п.)
            pass

    def _parse_number(self, text):
        if not text or text.strip() == '' or text.strip() == '~':
            return None
        text = text.strip().replace(',', '.')
        text = re.sub(r'[гмкгл%]', '', text)
        text = re.sub(r'[\(\)\[\]]', '', text)
        text = re.sub(r'[^\d.]', '', text)
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _merge_by_code(self):
        """Объединяет дубликаты по коду (берем порцию 100г)"""
        merged = {}

        for product in self.products:
            code = product['code']

            if code not in merged:
                merged[code] = {
                    'code': code,
                    'name': product['name'],
                    'category': product['category'],
                    'values': {}
                }

            # Объединяем значения
            for field, value in product['values'].items():
                # Если поле уже есть, проверяем порцию
                if field in merged[code]['values']:
                    # Если это порция 100г, приоритет
                    if product.get('values', {}).get('portion') == 100:
                        merged[code]['values'][field] = value
                else:
                    merged[code]['values'][field] = value

        return list(merged.values())


def save_to_json(products, output_file):
    data = {
        'source': 'Скурихин И.М., Тутельян В.А. Химический состав российских пищевых продуктов',
        'year': 2002,
        'export_date': datetime.now().isoformat(),
        'total_products': len(products),
        'products': products
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Сохранено в {output_file} ({len(products)} продуктов)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str, default='skurikhin_shrinked_milk.docx')
    parser.add_argument('--output', type=str, help='Выходной JSON-файл')

    args = parser.parse_args()

    print("=" * 70)
    print("🍽️  УНИВЕРСАЛЬНЫЙ ПАРСИНГ СПРАВОЧНИКА СКУРИХИНА")
    print("=" * 70)
    print(f"📄 Файл: {args.file}")

    p = SkurikhinParserUniversal(args.file)
    products = p.parse()

    if products:
        if args.output:
            output_file = args.output
        else:
            base_name = os.path.splitext(os.path.basename(args.file))[0]
            output_file = f"{base_name}_parsed.json"

        save_to_json(products, output_file)

        with_calories = [p for p in products if 'calories' in p.get('values', {})]
        print(f"\n📊 Всего: {len(products)}, с калориями: {len(with_calories)}")

        print("\n📋 ПРИМЕРЫ:")
        for product in products[:5]:
            print(f"  {product.get('code')}: {product.get('name')[:40]}...")
    else:
        print("❌ Не удалось распарсить продукты")


if __name__ == "__main__":
    main()