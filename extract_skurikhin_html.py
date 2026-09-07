#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Извлечение данных из PDF с HTML-таблицами
Справочник Скурихина и Тутельяна (2002)

Запуск:
    python extract_skurikhin_html.py ljproamn2jmgs_tables_only.pdf
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from slugify import slugify
from collections import defaultdict
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class HTMLTableExtractor:
    """Извлечение данных из HTML-таблиц в PDF"""

    NUTRIENT_MAPPING = {
        # Основные
        'Вода': 'water',
        'Бел': 'protein',
        'Белки': 'protein',
        'Жир': 'fat',
        'Жиры': 'fat',
        'Угл': 'carbohydrates',
        'Углеводы': 'carbohydrates',
        'НЖК': 'saturated_fat',
        'Хол': 'cholesterol',
        'МДС': 'sugar',
        'Кр': 'starch',
        'ПВ': 'fiber',
        'ОК': 'organic_acids',
        'Зола': 'ash',
        'Зона': 'ash',

        # Минералы (вторая часть таблиц)
        'Na': 'sodium',
        'K': 'potassium',
        'Ca': 'calcium',
        'Mg': 'magnesium',
        'P': 'phosphorus',
        'Fe': 'iron',

        # Витамины
        'A': 'vitamin_a',
        'B1': 'vitamin_b1',
        'B2': 'vitamin_b2',
        'PP': 'vitamin_b3',
        'C': 'vitamin_c',
        'E': 'vitamin_e',

        # Энергия
        'ккал': 'calories',
        'ЭЦ': 'calories',
    }

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.products = {}
        self.stats = {
            'pages_processed': 0,
            'html_tables_found': 0,
            'products_extracted': 0,
            'errors': 0
        }

    def extract_all(self) -> List[Dict[str, Any]]:
        """Извлечение всех данных из PDF"""
        logger.info(f"📂 Открываю PDF: {self.pdf_path}")

        try:
            doc = fitz.open(self.pdf_path)
            logger.info(f"📄 Всего страниц: {len(doc)}")

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Извлекаем HTML
                html = page.get_text("html")
                if html:
                    self._process_html(html, page_num + 1)

                self.stats['pages_processed'] += 1

                if (page_num + 1) % 10 == 0:
                    logger.info(f"  Обработано {page_num + 1}/{len(doc)} страниц...")

            doc.close()

            products_list = list(self.products.values())
            self.stats['products_extracted'] = len(products_list)

            logger.info(f"\n✅ Извлечено {len(products_list)} продуктов")
            logger.info(f"   Обработано страниц: {self.stats['pages_processed']}")
            logger.info(f"   Найдено HTML-таблиц: {self.stats['html_tables_found']}")

            return products_list

        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return []

    def _process_html(self, html: str, page_num: int):
        """Обработка HTML-содержимого страницы"""
        soup = BeautifulSoup(html, 'html.parser')

        # Ищем все таблицы
        tables = soup.find_all('table')

        for table in tables:
            self.stats['html_tables_found'] += 1
            self._parse_html_table(table, page_num)

    def _parse_html_table(self, table, page_num: int):
        """Парсинг HTML-таблицы"""
        rows = table.find_all('tr')
        if not rows:
            return

        # Находим заголовки
        headers = self._find_headers(rows)

        # Парсим строки с данными
        for row in rows:
            # Проверяем, что строка содержит ячейки с данными
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue

            # Извлекаем данные ячеек
            row_data = [cell.get_text(strip=True) for cell in cells]

            # Пропускаем пустые строки
            if not any(row_data):
                continue

            # Пропускаем строки-заголовки
            if self._is_header_row(row_data):
                continue

            # Извлекаем продукт
            product = self._extract_product(row_data, headers, page_num)
            if product and product.get('name'):
                # Используем название как ключ для избежания дубликатов
                key = product['name']
                if key in self.products:
                    # Объединяем данные из разных частей таблицы
                    self._merge_product(self.products[key], product)
                else:
                    self.products[key] = product

    def _find_headers(self, rows) -> Dict[str, int]:
        """Находит заголовки колонок"""
        headers = {}

        # Ищем заголовки в первых строках
        for row in rows[:5]:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue

            # Извлекаем текст ячеек
            header_texts = [cell.get_text(strip=True) for cell in cells]

            # Проверяем каждую ячейку
            for idx, text in enumerate(header_texts):
                if not text:
                    continue

                # Ищем совпадения с маппингом
                for key, field in self.NUTRIENT_MAPPING.items():
                    if text == key or key in text:
                        headers[field] = idx
                        break

            # Если нашли достаточно колонок
            if len(headers) >= 5:
                break

        # Если заголовков мало, используем стандартные позиции
        if len(headers) < 3:
            standard = {
                'name': 0,
                'code': 1,
                'water': 2,
                'protein': 3,
                'fat': 4,
                'carbohydrates': 5,
            }
            for field, idx in standard.items():
                if field not in headers:
                    headers[field] = idx

        return headers

    def _extract_product(self, row_data: List[str], headers: Dict[str, int],
                         page_num: int) -> Optional[Dict[str, Any]]:
        """Извлекает данные продукта из строки"""
        product = {
            'source_page': page_num,
            'data_source': 'skurikhin_tutelyan_2002'
        }

        # Извлекаем название
        name_idx = headers.get('name', 0)
        if name_idx < len(row_data) and row_data[name_idx]:
            name = row_data[name_idx].strip()
            name = self._clean_name(name)
            if name:
                product['name'] = name
            else:
                return None
        else:
            return None

        # Извлекаем код
        code_idx = headers.get('code', 1)
        if code_idx < len(row_data) and row_data[code_idx]:
            code = row_data[code_idx].strip()
            if code.isdigit():
                product['fdc_id'] = int(code)

        # Извлекаем нутриенты
        for field, col_idx in headers.items():
            if field in ['name', 'code']:
                continue

            if col_idx < len(row_data):
                value = row_data[col_idx]
                if value:
                    cleaned = self._clean_number(value)
                    if cleaned is not None:
                        product[field] = cleaned

        # Проверяем, что есть хотя бы один нутриент
        has_nutrient = any(
            v is not None for k, v in product.items()
            if k not in ['name', 'source_page', 'data_source', 'fdc_id', 'category']
        )

        if not has_nutrient:
            return None

        # Определяем категорию
        product['category'] = self._detect_category(product['name'])

        # Добавляем теги
        product['tags'] = self._generate_tags(product['name'], product['category'])

        # Добавляем описания
        product['short_description'] = self._generate_description(product)
        product['description'] = self._generate_full_description(product)

        # Поиск синонимов
        product['synonyms'] = self._find_synonyms(product['name'])

        return product

    def _clean_name(self, name: str) -> Optional[str]:
        """Очищает название продукта"""
        if not name:
            return None

        # Убираем коды в начале
        name = re.sub(r'^\d+\s+', '', name)

        # Убираем HTML-сущности
        name = name.replace('&amp;', '&').replace('&quot;', '"')

        # Убираем лишние пробелы
        name = re.sub(r'\s+', ' ', name).strip()

        # Пропускаем служебные строки
        skip_patterns = [
            r'^%$', r'^-$', r'^—$', r'^~$',
            r'^жирность', r'^таблица', r'^порция',
            r'^с\.п\.', r'^%с\.п\.',
            r'^\d+\.\d+$',  # Номера разделов
            r'^[А-Я]{2,}$',  # Заголовки из заглавных
        ]

        for pattern in skip_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return None

        if len(name) < 2:
            return None

        return name

    def _clean_number(self, value: str) -> Optional[float]:
        """Очищает числовое значение"""
        if not value:
            return None

        value = value.strip()

        # Пропускаем служебные символы
        if value in ['', '~', '-', '—', 'мг', '%', 'г', 'ккал']:
            return None

        # Убираем единицы измерения
        value = re.sub(r'[мкг мкг/100г мг г %]', '', value)
        value = re.sub(r'ккал', '', value)

        # Заменяем запятую на точку
        value = value.replace(',', '.')

        # Извлекаем число
        match = re.search(r'([\d.]+)', value)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None

        return None

    def _is_header_row(self, row_data: List[str]) -> bool:
        """Проверяет, является ли строка заголовком"""
        if not row_data:
            return False

        row_text = ' '.join(str(cell) for cell in row_data).lower()

        header_keywords = ['код', 'продукты', 'порция', 'вода', 'бел',
                           'жир', 'угл', 'нжк', 'хол', 'мдс', 'кр', 'пв', 'ок']

        count = sum(1 for kw in header_keywords if kw in row_text)
        return count >= 2

    def _merge_product(self, existing: Dict[str, Any], new: Dict[str, Any]):
        """Объединяет данные продукта из разных частей"""
        for key, value in new.items():
            if value is not None and value != '':
                if key not in existing or existing[key] is None or existing[key] == '':
                    existing[key] = value

    def _detect_category(self, name: str) -> str:
        """Определяет категорию продукта"""
        name_lower = name.lower()

        categories = {
            'Молочные продукты': ['молоко', 'сливки', 'сметан', 'творог', 'сыр', 'кефир', 'ряженк', 'йогурт',
                                  'простокваш'],
            'Мясо и мясные продукты': ['говядин', 'свинин', 'баранин', 'телятин', 'конин', 'колбас', 'сосиск',
                                       'сардельк'],
            'Мясо птицы': ['куриц', 'цыплен', 'бройлер', 'индейк', 'гус', 'утк'],
            'Субпродукты': ['печень', 'почк', 'сердц', 'мозг', 'язык'],
            'Рыба и морепродукты': ['рыб', 'окун', 'треск', 'минтай', 'сельд', 'лосос', 'форел', 'камбал', 'креветк',
                                    'краб'],
            'Яйца': ['яйцо', 'яичн', 'меланж', 'желток', 'белок'],
            'Зерно и крупы': ['пшениц', 'ржано', 'круп', 'мук', 'хлеб', 'рис', 'гречн', 'овсян', 'перлов', 'пшен'],
            'Овощи': ['капуст', 'морков', 'свекл', 'картоф', 'лук', 'чеснок', 'перец', 'томат', 'огурец'],
            'Фрукты и ягоды': ['яблок', 'груш', 'слив', 'вишн', 'абрикос', 'персик', 'апельсин', 'лимон', 'мандарин'],
            'Бобовые': ['горох', 'фасол', 'чечевиц', 'соя', 'нут'],
            'Орехи': ['орех', 'миндаль', 'кешью', 'фисташк', 'семечк'],
            'Кондитерские изделия': ['сахар', 'конфет', 'шоколад', 'мармелад', 'пастил', 'зефир', 'халв', 'вафл'],
            'Напитки': ['сок', 'компот', 'кисель', 'квас', 'чай', 'кофе', 'какао', 'вино', 'пиво'],
            'Жиры и масла': ['масло', 'маргарин', 'сало', 'жир', 'майонез'],
            'Грибы': ['гриб'],
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return category

        return 'Другое'

    def _generate_tags(self, name: str, category: str) -> List[str]:
        """Генерирует теги"""
        tags = []
        name_lower = name.lower()

        # Тег из категории
        if category:
            tags.append(slugify(category, separator='_'))

        # Специальные теги
        tag_keywords = {
            'молоко': 'молочные_продукты',
            'сыр': 'сыры',
            'творог': 'творог',
            'колбас': 'колбасные_изделия',
            'консерв': 'консервы',
            'копч': 'копченый',
            'вар': 'вареный',
            'суш': 'сушеный',
            'сол': 'соленый',
            'слад': 'сладкий',
            'жирн': 'жирный',
            'нежирн': 'нежирный',
        }

        for keyword, tag in tag_keywords.items():
            if keyword in name_lower:
                tags.append(tag)

        return list(set(tags))

    def _generate_description(self, product: Dict[str, Any]) -> str:
        """Генерирует краткое описание"""
        return f"Химический состав: {product.get('name', '')}"

    def _generate_full_description(self, product: Dict[str, Any]) -> str:
        """Генерирует полное описание"""
        name = product.get('name', '')
        category = product.get('category', '')
        page = product.get('source_page', '')

        description = f"<h3>{name}</h3>"
        description += f"<p><strong>Категория:</strong> {category}</p>"
        description += f"<p><strong>Источник:</strong> Скурихин И.М., Тутельян В.А. (ред.) Химический состав российских пищевых продуктов. М.: ДеЛи принт, 2002.</p>"
        description += f"<p><strong>Страница:</strong> {page}</p>"

        return description

    def _find_synonyms(self, name: str) -> str:
        """Находит синонимы"""
        synonyms = []
        name_lower = name.lower()

        synonym_pairs = [
            ('помидор', 'томат'),
            ('курага', 'абрикос сушеный'),
            ('чернослив', 'слива сушеная'),
        ]

        for word, syn in synonym_pairs:
            if word in name_lower:
                synonyms.append(syn)
            elif syn in name_lower:
                synonyms.append(word)

        return ', '.join(synonyms)

    def save_to_json(self, output_path: str):
        """Сохраняет данные в JSON"""
        if not self.products:
            logger.warning("⚠️ Нет данных для сохранения")
            return

        products_list = list(self.products.values())

        # Группировка по категориям
        grouped = defaultdict(list)
        for product in products_list:
            category = product.get('category', 'Другое')
            grouped[category].append(product)

        # Итоговая структура
        output_data = {
            'source': {
                'title': 'Химический состав российских пищевых продуктов',
                'editors': [
                    {'name': 'И. М. Скурихин', 'role': 'член-корр. МАИ, проф.'},
                    {'name': 'В. А. Тутельян', 'role': 'академик РАМН, проф.'}
                ],
                'publisher': 'ДеЛи принт',
                'place': 'Москва',
                'year': 2002,
                'pages': 236,
                'isbn': '5-94343-028-8',
                'bibliographic_reference': (
                    'Химический состав российских пищевых продуктов : Справочник / '
                    'Под ред. член-корр. МАИ, проф. И. М. Скурихина и академика РАМН, '
                    'проф. В. А. Тутельяна. — М. : ДеЛи принт, 2002. — 236 с. — ISBN 5-94343-028-8.'
                )
            },
            'extraction_info': {
                'date': '2026-09-01',
                'pdf_file': os.path.basename(self.pdf_path),
                'total_products': len(products_list),
                'pages_processed': self.stats['pages_processed'],
                'html_tables_found': self.stats['html_tables_found'],
                'errors': self.stats['errors']
            },
            'categories': list(grouped.keys()),
            'products_by_category': dict(grouped),
            'all_products': products_list
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n✅ Сохранено {len(products_list)} продуктов")
        logger.info(f"📂 Файл: {output_path}")

        # Статистика
        logger.info("\n📊 Распределение по категориям:")
        for category, products in sorted(grouped.items(), key=lambda x: -len(x[1])):
            logger.info(f"  {category}: {len(products)} продуктов")


def main():
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = 'ljproamn2jmgs_tables_only.pdf'

    if not os.path.exists(pdf_path):
        logger.error(f"❌ Файл не найден: {pdf_path}")
        logger.info("Использование: python extract_skurikhin_html.py <path_to_pdf>")
        return

    extractor = HTMLTableExtractor(pdf_path)
    products = extractor.extract_all()

    if products:
        extractor.save_to_json('nutrition_skurikhin_full.json')

        # Показываем пример
        logger.info("\n📋 Пример продукта:")
        sample = products[0]
        for key, value in list(sample.items())[:10]:
            if value is not None and value != '':
                logger.info(f"  {key}: {value}")
    else:
        logger.error("❌ Не удалось извлечь данные")


if __name__ == '__main__':
    main()