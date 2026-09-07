#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Универсальный парсер справочника Скурихина
Берет только строки с порцией 100г
"""

import os
import re
import json
import argparse
from datetime import datetime
from docx import Document


class SkurikhinParserUniversal:
    def __init__(self, file_path, debug=False):
        self.file_path = file_path
        self.doc = None
        self.products = []
        self.current_category = {}
        self.column_mapping_left = {}
        self.column_mapping_right = {}
        self.debug = debug
        self.table_side = 'left'
        self.current_code = None

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
            self.table_side = self._detect_side(table)
            side_label = "ЛЕВАЯ" if self.table_side == 'left' else "ПРАВАЯ"
            print(f"  📊 Обработка таблицы #{table_idx + 1} ({side_label})")
            self._parse_table(table)

        merged = self._merge_by_code()
        print(f"✅ Найдено продуктов: {len(merged)}")
        return merged

    def _detect_side(self, table):
        for row in table.rows:
            row_text = ' '.join([cell.text.strip() for cell in row.cells])
            if 'Na' in row_text and 'К' in row_text and 'Са' in row_text:
                return 'right'
            if 'Вода' in row_text and 'Бел' in row_text and 'Жир' in row_text:
                return 'left'
        return 'left'

    def _parse_table(self, table):
        rows_data = []
        for row in table.rows:
            row_texts = [cell.text.strip() for cell in row.cells]
            rows_data.append(row_texts)

        rows_data = [r for r in rows_data if any(r)]
        if not rows_data:
            return

        if self.debug:
            print(f"    📋 Всего строк: {len(rows_data)}")

        if self.table_side == 'left':
            self._analyze_structure_left(rows_data)
        else:
            self._analyze_structure_right(rows_data)
            self.current_code = None

        i = 0
        while i < len(rows_data):
            row = rows_data[i]

            if self._is_header_row(row):
                if self.debug:
                    print(f"      Пропуск заголовка")
                i += 1
                continue

            if self.table_side == 'left':
                if self._is_category_row_left(row):
                    if self.debug:
                        print(f"      Категория: {row[0]}")
                    self._parse_category(row)
                    i += 1
                    continue

                if self._is_product_row_left(row):
                    if self.debug:
                        print(f"      Продукт: {row[0]}")
                    self._parse_product_left(row)
                    i += 1
                    continue
            else:
                if self._is_data_row_right(row):
                    if self.debug:
                        print(f"      Данные: {row[:3]}")
                    self._parse_product_right(row)
                    i += 1
                    continue

            i += 1

    def _analyze_structure_left(self, rows):
        for row in rows[:5]:
            row_text = ' '.join(row)
            if 'Код' in row_text and 'Продукты' in row_text:
                for idx, cell in enumerate(row):
                    cell_lower = cell.lower()
                    if 'код' in cell_lower:
                        self.column_mapping_left['code'] = idx
                    elif 'продукт' in cell_lower or 'название' in cell_lower:
                        self.column_mapping_left['name'] = idx
                    elif 'порц' in cell_lower:
                        self.column_mapping_left['portion'] = idx
                    elif 'вода' in cell_lower:
                        self.column_mapping_left['water'] = idx
                    elif 'бел' in cell_lower and 'ж' not in cell_lower:
                        self.column_mapping_left['protein'] = idx
                    elif 'жир' in cell_lower and 'насыщ' not in cell_lower:
                        self.column_mapping_left['fat'] = idx
                    elif 'нжк' in cell_lower:
                        self.column_mapping_left['saturated_fat'] = idx
                    elif 'хол' in cell_lower:
                        self.column_mapping_left['cholesterol'] = idx
                    elif 'мдс' in cell_lower:
                        self.column_mapping_left['sugar'] = idx
                    elif 'кр' in cell_lower and 'рахм' not in cell_lower:
                        self.column_mapping_left['starch'] = idx
                    elif 'угл' in cell_lower:
                        self.column_mapping_left['carbohydrates'] = idx
                    elif 'пв' in cell_lower:
                        self.column_mapping_left['fiber'] = idx
                    elif 'ок' in cell_lower:
                        self.column_mapping_left['organic_acids'] = idx
                    elif 'зол' in cell_lower:
                        self.column_mapping_left['ash'] = idx
                if self.debug:
                    print(f"    🔍 Найдено колонок (левая): {list(self.column_mapping_left.keys())}")
                break

    def _analyze_structure_right(self, rows):
        """Анализирует структуру правой части — ищем все возможные колонки"""
        for row in rows[:5]:
            row_text = ' '.join(row)
            if 'Na' in row_text and 'К' in row_text and 'Са' in row_text:
                for idx, cell in enumerate(row):
                    cell_lower = cell.lower()
                    # Минералы
                    if 'na' in cell_lower:
                        self.column_mapping_right['sodium'] = idx
                    elif 'к' in cell_lower and 'алий' not in cell_lower and 'ка' not in cell_lower:
                        self.column_mapping_right['potassium'] = idx
                    elif 'са' in cell_lower:
                        self.column_mapping_right['calcium'] = idx
                    elif 'мд' in cell_lower or 'mg' in cell_lower:
                        self.column_mapping_right['magnesium'] = idx
                    elif 'р' in cell_lower and 'э' not in cell_lower and 'рр' not in cell_lower:
                        self.column_mapping_right['phosphorus'] = idx
                    elif 'fe' in cell_lower:
                        self.column_mapping_right['iron'] = idx
                    # Витамины
                    elif 'а' in cell_lower and 'витам' not in cell_lower:
                        self.column_mapping_right['vitamin_a'] = idx
                    elif 'кар' in cell_lower:
                        self.column_mapping_right['beta_carotene'] = idx
                    elif 'рэ' in cell_lower:
                        self.column_mapping_right['retinol_equivalent'] = idx
                    elif 'тэ' in cell_lower or 'токофер' in cell_lower:
                        self.column_mapping_right['vitamin_e'] = idx
                    elif 'b1' in cell_lower or 'в1' in cell_lower:
                        self.column_mapping_right['vitamin_b1'] = idx
                    elif 'b2' in cell_lower or 'в2' in cell_lower:
                        self.column_mapping_right['vitamin_b2'] = idx
                    elif 'рр' in cell_lower:
                        self.column_mapping_right['vitamin_b3'] = idx
                    elif 'нэ' in cell_lower:
                        self.column_mapping_right['niacin_equivalent'] = idx
                    elif 'с' in cell_lower and 'витам' not in cell_lower:
                        self.column_mapping_right['vitamin_c'] = idx
                    # Калории — ищем по разным названиям
                    elif 'эц' in cell_lower or 'энерг' in cell_lower or 'ккал' in cell_lower:
                        self.column_mapping_right['calories'] = idx
                if self.debug:
                    print(f"    🔍 Найдено колонок (правая): {list(self.column_mapping_right.keys())}")
                break

        # Если калории не найдены, пробуем найти по индексу (последняя колонка с числами)
        if 'calories' not in self.column_mapping_right:
            # Ищем колонку с числами в конце таблицы
            for row in rows[4:10]:  # строки с данными
                for idx, cell in enumerate(row):
                    if re.match(r'^[\d.]+$', cell.strip()) and idx > 5:
                        self.column_mapping_right['calories'] = idx
                        if self.debug:
                            print(f"    🔍 Калории найдены по индексу: {idx}")
                        break
                if 'calories' in self.column_mapping_right:
                    break

    def _is_header_row(self, row):
        if not row:
            return False
        row_text = ' '.join(row)
        return 'Код' in row_text and 'Продукты' in row_text

    def _is_category_row_left(self, row):
        if not row:
            return False
        first_cell = row[0].strip()
        return bool(re.match(r'^\d+(?:\.\d+){0,2}$', first_cell))

    def _parse_category(self, row):
        code = row[0].strip()

        name = ''
        for cell in row[1:]:
            if cell.strip() and not re.match(r'^[\d.]+$', cell.strip()):
                if len(cell.strip()) > 3:
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

    def _is_product_row_left(self, row):
        if not row:
            return False
        first_cell = row[0].strip()
        return bool(re.match(r'^\d+(?:\.\d+){2,}$', first_cell))

    def _parse_product_left(self, row):
        code = row[0].strip()

        name = ''
        for i, cell in enumerate(row):
            if i == 0:
                continue
            if cell.strip() and not re.match(r'^[\d.]+$', cell.strip()):
                if not re.match(r'^%с\.п\.', cell.strip()):
                    if not name:
                        name = cell.strip()

        if not name:
            name = f"Продукт {code}"

        name = re.sub(r'\s*(100|200|300|%с\.п\.\s*\d+)\s*', '', name).strip()
        name = re.sub(r'\s+', ' ', name).strip()

        product = {
            'code': code,
            'name': name,
            'category': self.current_category.copy(),
            'values': {}
        }

        for field, col_idx in self.column_mapping_left.items():
            if col_idx < len(row):
                value = self._parse_number(row[col_idx])
                if value is not None:
                    product['values'][field] = value

        if product['values']:
            self.products.append(product)
            if self.debug:
                print(f"      ✅ Добавлен продукт: {code} - {name} ({len(product['values'])} значений)")

    def _is_data_row_right(self, row):
        if not row:
            return False
        # Проверяем наличие кода в последних колонках
        for idx in range(len(row) - 1, max(0, len(row) - 4), -1):
            if re.match(r'^\d+(?:\.\d+){2,}$', row[idx].strip()):
                return True
        return False

    def _parse_product_right(self, row):
        """Парсит продукт из правой части — берем первую строку для каждого кода (100г)"""
        # Находим код в последних колонках
        code = None
        for idx in range(len(row) - 1, max(0, len(row) - 4), -1):
            if re.match(r'^\d+(?:\.\d+){2,}$', row[idx].strip()):
                code = row[idx].strip()
                break

        if not code:
            return

        # Проверяем, есть ли уже данные для этого кода из правой части
        for p in self.products:
            if p.get('code') == code and p.get('_right_data_added', False):
                if self.debug:
                    print(f"      ⏭️ Данные для {code} уже добавлены (первая строка)")
                return

        # Находим или создаем продукт
        product = None
        for p in self.products:
            if p['code'] == code:
                product = p
                break

        if not product:
            name = None
            for p in self.products:
                if p['code'] == code:
                    name = p['name']
                    break
            if not name:
                name = f"Продукт {code}"

            product = {
                'code': code,
                'name': name,
                'category': self.current_category.copy(),
                'values': {}
            }
            self.products.append(product)

        # Парсим значения по маппингу
        for field, col_idx in self.column_mapping_right.items():
            if col_idx < len(row):
                value = self._parse_number(row[col_idx])
                if value is not None and field not in product['values']:
                    product['values'][field] = value

        # ===== НОВАЯ ЛОГИКА: ВСЕГДА ищем калории в последних колонках =====
        # Ищем число, которое похоже на калории (0-1000) в последних 3 колонках
        for idx in range(1, 4):
            if len(row) >= idx:
                cell = row[-idx].strip()
                value = self._parse_number(cell)
                if value is not None and 0 < value < 1000:
                    # Проверяем, что это не sodium, potassium и т.д.
                    # Если калорий еще нет или это значение больше, берем его
                    if 'calories' not in product['values'] or value > product['values'].get('calories', 0):
                        product['values']['calories'] = value
                        if self.debug:
                            print(f"      🔍 Найдены калории для {code}: {value} (колонка -{idx})")
                    break

        # Отмечаем, что данные из правой части добавлены
        product['_right_data_added'] = True
        product['values']['portion'] = 100

        if self.debug:
            print(f"      ✅ Добавлены данные для: {code} ({len(product['values'])} значений)")

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
            for field, value in product['values'].items():
                if field not in merged[code]['values']:
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
    parser.add_argument('--output', type=str)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    print("=" * 70)
    print("🍽️  УНИВЕРСАЛЬНЫЙ ПАРСИНГ СПРАВОЧНИКА СКУРИХИНА (ТОЛЬКО 100г)")
    print("=" * 70)
    print(f"📄 Файл: {args.file}")

    p = SkurikhinParserUniversal(args.file, debug=args.debug)
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
        for product in products[:10]:
            values = product.get('values', {})
            print(f"  {product.get('code')}: {product.get('name')[:40]}")
            if 'calories' in values:
                print(f"    Калории: {values['calories']}")
            if 'portion' in values:
                print(f"    Порция: {values['portion']}г")
    else:
        print("❌ Не удалось распарсить продукты")


if __name__ == "__main__":
    main()