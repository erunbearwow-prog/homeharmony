# kitchen/management/commands/split_pdf_to_texts.py
import os
import re
import json
import pymupdf4llm
import ollama
from django.core.management.base import BaseCommand


def extract_recipe_texts_llm(page_text: str) -> list:
    """
    Использует LLM для выделения отдельных рецептов из текста страницы
    Возвращает список текстов рецептов
    """
    prompt = f"""
    Ты — анализатор кулинарных книг. На странице может быть несколько рецептов.

    ВОТ ТЕКСТ СТРАНИЦЫ:
    ---
    {page_text[:4000]}
    ---

    ЗАДАНИЕ:
    1. Найди все рецепты на этой странице
    2. Для каждого рецепта верни его ПОЛНЫЙ ТЕКСТ (как в оригинале, без изменений)
    3. Сохрани ВСЕ детали, включая примечания, советы, варианты подачи
    4. Не вырезай ингредиенты и шаги — верни текст целиком

    ФОРМАТ ОТВЕТА (ТОЛЬКО JSON):
    {{
        "recipes": [
            "Полный текст первого рецепта...",
            "Полный текст второго рецепта...",
            "Полный текст третьего рецепта..."
        ]
    }}

    Если на странице один рецепт — верни массив с одним элементом.
    Верни ТОЛЬКО JSON, без пояснений.
    """

    response = ollama.chat(
        model='qwen2.5:7b',
        messages=[{'role': 'user', 'content': prompt}],
        format='json'
    )

    data = json.loads(response['message']['content'])
    return data.get('recipes', [])


class Command(BaseCommand):
    help = 'Разбивает PDF на отдельные текстовые файлы (по одному на рецепт)'

    def add_arguments(self, parser):
        parser.add_argument('pdf_path', type=str, help='Путь к PDF-файлу')
        parser.add_argument('--output-dir', type=str, default='./extracted_recipes',
                            help='Папка для сохранения текстовых файлов')
        parser.add_argument('--debug', action='store_true', help='Показать отладочную информацию')

    def handle(self, *args, **options):
        pdf_path = options['pdf_path']
        output_dir = options['output_dir']
        debug = options['debug']

        if not os.path.exists(pdf_path):
            self.stderr.write(self.style.ERROR(f'❌ Файл не найден: {pdf_path}'))
            return

        # Создаём папку для вывода
        os.makedirs(output_dir, exist_ok=True)

        self.stdout.write(self.style.SUCCESS(f'📄 Читаю PDF: {pdf_path}'))

        # Извлекаем текст из PDF
        md_text = pymupdf4llm.to_markdown(pdf_path)

        # Разбиваем на страницы
        pages = md_text.split('\f')

        self.stdout.write(f"📊 Всего страниц: {len(pages)}")

        all_recipes = []
        recipe_counter = 1

        for page_num, page_text in enumerate(pages, 1):
            if not page_text.strip():
                continue

            self.stdout.write(f"\n📄 Обрабатываю страницу {page_num}...")

            try:
                # Получаем тексты рецептов со страницы
                recipes = extract_recipe_texts_llm(page_text)

                if debug:
                    self.stdout.write(f"   Найдено рецептов: {len(recipes)}")

                for i, recipe_text in enumerate(recipes):
                    if not recipe_text or len(recipe_text.strip()) < 50:
                        continue

                    # Очищаем название для имени файла
                    first_line = recipe_text.strip().split('\n')[0]
                    # Убираем номера и спецсимволы
                    clean_title = re.sub(r'^\d+\.?\s*', '', first_line)
                    clean_title = re.sub(r'[^\w\s-]', '', clean_title)
                    clean_title = clean_title.strip()[:50]

                    if not clean_title:
                        clean_title = f"recipe_{recipe_counter}"

                    filename = f"{recipe_counter:03d}_{clean_title}.txt"
                    filepath = os.path.join(output_dir, filename)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(recipe_text.strip())

                    self.stdout.write(f"   ✅ Сохранён: {filename}")
                    all_recipes.append(filepath)
                    recipe_counter += 1

            except Exception as e:
                self.stderr.write(self.style.ERROR(f'   ❌ Ошибка на странице {page_num}: {e}'))
                continue

        # Создаём файл-манифест
        manifest_path = os.path.join(output_dir, '_manifest.txt')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(f"Всего рецептов: {len(all_recipes)}\n")
            f.write(f"Источник: {pdf_path}\n")
            f.write("\nФайлы:\n")
            for fp in all_recipes:
                f.write(f"  {os.path.basename(fp)}\n")

        self.stdout.write(self.style.SUCCESS(f'\n✅ Готово!'))
        self.stdout.write(f'   📁 Результаты в папке: {output_dir}')
        self.stdout.write(f'   📄 Сохранено рецептов: {len(all_recipes)}')
        self.stdout.write(f'   📋 Манифест: {manifest_path}')