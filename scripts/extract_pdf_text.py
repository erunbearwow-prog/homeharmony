#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Извлечение текста из PDF-файла с рецептурами (с 38-й страницы)
Запуск: python scripts/extract_pdf_text.py
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

try:
    import pdfplumber

    print("✅ Используем pdfplumber")
    USE_PDFPLUMBER = True
except ImportError:
    try:
        import fitz

        print("✅ Используем PyMuPDF")
        USE_PDFPLUMBER = False
    except ImportError:
        print("❌ Установите pdfplumber: pip install pdfplumber")
        sys.exit(1)


def extract_with_pdfplumber(pdf_path, output_dir, start_page=38, end_page=None):
    """Извлекает текст через pdfplumber с указанной страницы"""
    print(f"\n📄 Обработка PDF: {pdf_path}")

    all_text = []
    metadata = {}

    with pdfplumber.open(pdf_path) as pdf:
        metadata = {
            'total_pages': len(pdf.pages),
            'metadata': pdf.metadata
        }
        print(f"  Всего страниц: {len(pdf.pages)}")
        print(f"  Начинаем с: {start_page}")

        # Определяем страницы для обработки
        if end_page:
            end = min(end_page, len(pdf.pages))
        else:
            end = len(pdf.pages)

        print(f"  Заканчиваем: {end}")
        print(f"  Всего страниц с рецептами: {end - start_page + 1}")

        for i in range(start_page - 1, end):
            page = pdf.pages[i]
            text = page.extract_text()
            if text:
                all_text.append({
                    'page': i + 1,
                    'text': text
                })

            if (i + 1) % 10 == 0:
                print(f"  Обработано страниц: {i + 1}")

    return all_text, metadata


def extract_with_pymupdf(pdf_path, output_dir, start_page=38, end_page=None):
    """Извлекает текст через PyMuPDF с указанной страницы"""
    import fitz

    print(f"\n📄 Обработка PDF: {pdf_path}")

    doc = fitz.open(pdf_path)
    all_text = []
    metadata = {
        'total_pages': len(doc),
        'metadata': doc.metadata
    }

    print(f"  Всего страниц: {len(doc)}")
    print(f"  Начинаем с: {start_page}")

    if end_page:
        end = min(end_page, len(doc))
    else:
        end = len(doc)

    print(f"  Заканчиваем: {end}")
    print(f"  Всего страниц с рецептами: {end - start_page + 1}")

    for i in range(start_page - 1, end):
        page = doc[i]
        text = page.get_text()
        if text:
            all_text.append({
                'page': i + 1,
                'text': text
            })

        if (i + 1) % 10 == 0:
            print(f"  Обработано страниц: {i + 1}")

    doc.close()
    return all_text, metadata


def save_extracted_text(all_text, metadata, output_dir):
    """Сохраняет извлеченный текст"""

    full_text_path = output_dir / 'full_text.txt'
    with open(full_text_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ИЗВЛЕЧЕННЫЙ ТЕКСТ ИЗ PDF\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Страниц с рецептами: {len(all_text)}\n")
        f.write("=" * 80 + "\n\n")

        for page_data in all_text:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"СТРАНИЦА {page_data['page']}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(page_data['text'])
            f.write("\n\n")

    print(f"✅ Сохранен полный текст: {full_text_path}")

    pages_dir = output_dir / 'pages'
    pages_dir.mkdir(exist_ok=True)

    for page_data in all_text:
        page_path = pages_dir / f'page_{page_data["page"]:04d}.txt'
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(page_data['text'])

    print(f"✅ Сохранены отдельные страницы: {pages_dir}")

    meta_path = output_dir / 'metadata.json'
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ Сохранены метаданные: {meta_path}")


def extract_recipe_headers(text):
    """Извлекает заголовки рецептур"""
    # Ищем "номер. Название"
    pattern = r'^(\d+)\.\s+(.+)$'
    matches = re.findall(pattern, text, re.MULTILINE)
    return matches


def analyze_extraction(all_text, output_dir):
    """Анализирует качество извлечения"""

    print("\n" + "=" * 70)
    print("📊 АНАЛИЗ КАЧЕСТВА ИЗВЛЕЧЕНИЯ")
    print("=" * 70)

    total_chars = sum(len(p['text']) for p in all_text)
    total_lines = sum(p['text'].count('\n') for p in all_text)

    print(f"  Всего символов: {total_chars:,}")
    print(f"  Всего строк: {total_lines:,}")
    print(f"  Средняя длина страницы: {total_chars // len(all_text):,} символов")

    # Ищем рецептуры
    all_text_combined = '\n'.join(p['text'] for p in all_text)
    recipes = extract_recipe_headers(all_text_combined)

    print(f"\n  Найдено заголовков рецептур: {len(recipes)}")

    if recipes:
        print("\n  Первые 10 рецептур:")
        for num, name in recipes[:10]:
            print(f"    {num}. {name}")

    # Проверяем наличие ингредиентов
    ingredient_pattern = r'([А-Яа-я\s\-\(\)]+)\s+([\d,]+)\s+([\d,]+)'
    ingredients = re.findall(ingredient_pattern, all_text_combined)
    print(f"\n  Найдено строк с ингредиентами: {len(ingredients)}")

    if ingredients:
        print("\n  Примеры ингредиентов:")
        for ing in ingredients[:10]:
            print(f"    {ing[0].strip()}: {ing[1]}г → {ing[2]}г")

    # Проверяем кухни
    cuisine_pattern = r'^([А-ЯЁ\s\-]+КУХНЯ)'
    cuisines = re.findall(cuisine_pattern, all_text_combined, re.MULTILINE)
    print(f"\n  Найдено кухонь: {len(set(cuisines))}")

    if cuisines:
        print("\n  Кухни:")
        for cuisine in sorted(set(cuisines)):
            print(f"    - {cuisine}")

    # Сохраняем список рецептур
    if recipes:
        recipes_path = output_dir / 'recipe_headers.json'
        with open(recipes_path, 'w', encoding='utf-8') as f:
            json.dump(recipes, f, ensure_ascii=False, indent=2)
        print(f"\n  ✅ Список рецептур сохранен: {recipes_path}")


def main():
    """Главная функция"""
    print("=" * 70)
    print("📄 ИЗВЛЕЧЕНИЕ ТЕКСТА ИЗ PDF (с 38-й страницы)")
    print("=" * 70)

    project_root = Path(__file__).parent.parent
    pdf_dir = project_root / 'data'
    pdf_path = pdf_dir / 'Васюкова А.Т.-Сборник рецептур.pdf'
    output_dir = project_root / 'data' / 'extracted_pdf'

    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        pdf_files = list(pdf_dir.glob('*.pdf'))
        if pdf_files:
            pdf_path = pdf_files[0]
            print(f"📁 Найден PDF: {pdf_path.name}")
        else:
            print(f"❌ PDF не найден в {pdf_dir}")
            return

    print(f"📁 PDF: {pdf_path.name}")
    print(f"📁 Размер: {pdf_path.stat().st_size / (1024 * 1024):.2f} MB")
    print(f"📁 Результаты: {output_dir}")

    print("\n" + "=" * 70)
    print("ВАРИАНТЫ ОБРАБОТКИ:")
    print("  1. Обработать все страницы с 38-й до конца (полный)")
    print("  2. Обработать только 38-ю страницу (тест)")
    print("  3. Указать диапазон страниц")

    choice = input("\nВыберите вариант (1-3): ").strip()

    start_page = 38
    end_page = None

    if choice == '2':
        end_page = 38
        print("  Тестовый режим: только страница 38")
    elif choice == '3':
        start_page = int(input("  Начальная страница: "))
        end_page = int(input("  Конечная страница: "))
        print(f"  Диапазон: страницы {start_page}-{end_page}")
    else:
        print("  Полный режим: с 38-й страницы до конца")

    try:
        if USE_PDFPLUMBER:
            all_text, metadata = extract_with_pdfplumber(pdf_path, output_dir, start_page, end_page)
        else:
            all_text, metadata = extract_with_pymupdf(pdf_path, output_dir, start_page, end_page)

        if not all_text:
            print("❌ Текст не извлечен")
            return

        save_extracted_text(all_text, metadata, output_dir)
        analyze_extraction(all_text, output_dir)

        print("\n" + "=" * 70)
        print("✅ ИЗВЛЕЧЕНИЕ ЗАВЕРШЕНО")
        print("=" * 70)
        print(f"📁 Результаты: {output_dir}")
        print("   - full_text.txt — полный текст рецептур")
        print("   - pages/ — отдельные страницы")
        print("   - metadata.json — метаданные")
        print("   - recipe_headers.json — список рецептур")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()