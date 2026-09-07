# inspect_docx.py

import sys
from docx import Document


def inspect_docx(file_path):
    print(f"📄 Анализ файла: {file_path}")
    print("=" * 70)

    doc = Document(file_path)

    for table_idx, table in enumerate(doc.tables):
        print(f"\n📊 Таблица #{table_idx + 1}")
        print("-" * 40)

        for row_idx, row in enumerate(table.rows):
            cells = [cell.text.strip()[:30] for cell in row.cells]
            print(f"  Строка {row_idx:2d}: {cells}")

        if table_idx >= 2:  # Показываем только первые 3 таблицы
            print("  ... (дальше пропущено)")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_docx(sys.argv[1])
    else:
        inspect_docx("skurikhin_shrinked_eggs.docx")