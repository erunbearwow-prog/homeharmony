# kitchen/management/commands/import_pdf_recipes.py
"""
# Импорт одного рецепта из текста
python manage.py import_recipe_from_text "Ваш текст рецепта"

# Импорт из PDF
python manage.py import_pdf_recipes book.pdf

# С отладкой
python manage.py import_pdf_recipes book.pdf --debug

# Только первые 10 страниц
python manage.py import_pdf_recipes book.pdf --start-page 1 --end-page 10

# Максимум 5 рецептов (для теста)
python manage.py import_pdf_recipes book.pdf --max-recipes 5
"""
import os
import json
import hashlib
import re
import pymupdf4llm
from django.core.management.base import BaseCommand
from django.core.cache import cache
from kitchen.models import Recipe, RecipeIngredient, Ingredient
from kitchen.management.commands.import_recipe_from_text import extract_recipe_from_text
import ollama


class Command(BaseCommand):
    help = 'Импортирует рецепты из PDF-файла с автоматическим определением границ рецептов'

    def add_arguments(self, parser):
        parser.add_argument('pdf_path', type=str, help='Путь к PDF-файлу')
        parser.add_argument('--start-page', type=int, help='Номер начальной страницы', default=1)
        parser.add_argument('--end-page', type=int, help='Номер конечной страницы', default=None)
        parser.add_argument('--max-recipes', type=int, help='Максимальное количество рецептов', default=None)
        parser.add_argument('--no-cache', action='store_true', help='Не использовать кэш')
        parser.add_argument('--debug', action='store_true', help='Показать детальную информацию о разбиении')

    def extract_recipe_blocks_quick(self, text: str) -> list:
        """
        Быстрое разбиение на рецепты с помощью регулярных выражений
        """
        # Признаки начала нового рецепта
        patterns = [
            r'(?=\n[А-Я][^а-я]*?\n)',  # Строка с заглавными
            r'(?=\nИнгредиенты:?\n)',  # Слово "Ингредиенты"
            r'(?=\n\d+\.\s+[А-Я])',  # Обычные цифры
        ]

        # Если текст короткий — один рецепт
        if len(text) < 1500:
            return [text]

        # Пробуем разделить
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if len(matches) >= 2:
                combined_pattern = '|'.join(patterns)
                blocks = re.split(combined_pattern, text)
                blocks = [block.strip() for block in blocks if block and len(block.strip()) > 50]
                if len(blocks) > 1:
                    return blocks

        return [text]

    def extract_recipe_boundaries_with_llm(self, page_text: str, debug: bool = False) -> list:
        """
        Определяет границы рецептов на странице с помощью LLM
        """
        prompt = f"""
        Ты — анализатор кулинарных книг. Разбери страницу на отдельные рецепты.

        Для каждого рецепта определи:
        1. Название (title)
        2. Начало текста (start) — позиция символа в строке
        3. Конец текста (end) — позиция символа в строке

        Верни ТОЛЬКО JSON в формате:
        {{
            "recipes": [
                {{"title": "Название рецепта 1", "start": 0, "end": 450}},
                {{"title": "Название рецепта 2", "start": 451, "end": 890}}
            ]
        }}

        Если на странице один рецепт, верни массив с одним элементом.

        Текст страницы:
        {page_text[:4000]}
        """

        try:
            response = ollama.chat(
                model='qwen2.5:7b',
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )

            data = json.loads(response['message']['content'])
            recipes = data.get('recipes', [])

            if debug:
                self.stdout.write(f"      LLM нашла {len(recipes)} рецептов")
                for i, r in enumerate(recipes):
                    self.stdout.write(f"         {i + 1}. {r.get('title', 'Без названия')[:40]}...")

            return recipes

        except Exception as e:
            if debug:
                self.stdout.write(f"      ⚠️ Ошибка LLM: {e}")
            return []

    def get_page_hash(self, text: str) -> str:
        """Возвращает хеш страницы для кэширования"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def smart_split_page(self, page_text: str, debug: bool = False, use_cache: bool = True) -> list:
        """
        Умное разбиение страницы на рецепты (комбинация методов)
        Возвращает список словарей с полями: title, text
        """
        # 1. Пробуем получить из кэша
        if use_cache:
            page_hash = self.get_page_hash(page_text)
            cache_key = f'recipe_boundaries_{page_hash}'
            cached = cache.get(cache_key)
            if cached:
                if debug:
                    self.stdout.write("   💾 Использую кэшированное разбиение")
                return cached

        # 2. Пробуем быстрый метод
        quick_blocks = self.extract_recipe_blocks_quick(page_text)

        if len(quick_blocks) > 1 and len(quick_blocks) <= 3:
            if debug:
                self.stdout.write(f"   ⚡ Быстрый метод нашёл {len(quick_blocks)} рецепта")

            recipes = []
            for i, block in enumerate(quick_blocks):
                lines = block.strip().split('\n')
                title = lines[0][:100] if lines else f"Рецепт {i + 1}"
                recipes.append({'title': title, 'text': block})

            if use_cache:
                cache.set(cache_key, recipes, 3600 * 24 * 7)
            return recipes

        # 3. Используем LLM для точного разбиения
        if debug:
            self.stdout.write("   🤖 Использую LLM для точного разбиения")

        llm_recipes = self.extract_recipe_boundaries_with_llm(page_text, debug)

        if llm_recipes and len(llm_recipes) > 0:
            recipes = []
            for recipe_info in llm_recipes:
                start = recipe_info.get('start', 0)
                end = recipe_info.get('end', len(page_text))
                title = recipe_info.get('title', 'Без названия')

                recipe_text = page_text[start:end].strip()
                if recipe_text:
                    recipes.append({'title': title, 'text': recipe_text})

            if recipes and use_cache:
                cache.set(cache_key, recipes, 3600 * 24 * 7)
            return recipes

        # 4. Если ничего не сработало — вся страница как один рецепт
        if debug:
            self.stdout.write("   📄 Вся страница как один рецепт")

        lines = page_text.strip().split('\n')
        title = lines[0][:100] if lines else "Рецепт без названия"

        recipes = [{'title': title, 'text': page_text}]
        if use_cache:
            cache.set(cache_key, recipes, 3600 * 24 * 7)
        return recipes

    def safe_import_recipe(self, recipe_text: str, title: str = None, debug: bool = False) -> bool:
        try:
            # Очищаем текст от мусора
            import re

            # Убираем номера рецептов в скобках
            cleaned_text = re.sub(r'\(\d+\)', '', recipe_text)
            # Убираем сноски
            cleaned_text = re.sub(r'[*⁰¹²³⁴⁵⁶⁷⁸⁹†‡]+', '', cleaned_text)
            # Убираем номера страниц
            cleaned_text = re.sub(r'\n\s*\d+\s*$', '', cleaned_text, flags=re.MULTILINE)
            # Убираем лишние переводы строк
            cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

            # Убираем строки с "г." и подобным мусором
            lines = cleaned_text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and not re.match(r'^\d+\.?\s*$', line):  # не пустая и не просто номер
                    cleaned_lines.append(line)
            cleaned_text = '\n'.join(cleaned_lines)

            # Извлекаем JSON через LLM
            recipe_data = extract_recipe_from_text(cleaned_text)

            # Используем переданное название или извлечённое
            recipe_title = title or recipe_data.get('title', 'Без названия')

            # Сохраняем в базу
            recipe = Recipe.objects.create(
                title=recipe_title,
                total_time=0,
                servings=4,
                difficulty='medium'
            )

            # Сохраняем ингредиенты
            ingredients_count = 0
            for ing in recipe_data.get('ingredients', []):
                if not ing.get('name'):
                    continue

                quantity = ing.get('quantity', 0)
                if quantity is None or quantity == '':
                    quantity = 0
                else:
                    try:
                        quantity = float(quantity)
                    except (ValueError, TypeError):
                        quantity = 0

                ingredient_obj, _ = Ingredient.objects.get_or_create(
                    name=ing['name'].strip(),
                    defaults={'default_unit': ing.get('unit', 'г')}
                )

                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient_obj,
                    quantity=quantity,
                    unit=ing.get('unit', 'г')
                )
                ingredients_count += 1

            # Сохраняем шаги
            steps_count = 0
            for step in recipe_data.get('steps', []):
                recipe.steps.create(
                    order=step.get('order', steps_count + 1),
                    title=f"Шаг {step.get('order', steps_count + 1)}",
                    instruction=step.get('instruction', '')
                )
                steps_count += 1

            if debug:
                self.stdout.write(
                    f"      ✅ Импортирован: {recipe_title} (ингр.: {ingredients_count}, шагов: {steps_count})")
            else:
                self.stdout.write(f"      ✅ Рецепт импортирован")
            return True

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'      ❌ Ошибка импорта: {e}'))
            if debug:
                import traceback
                traceback.print_exc()
            return False

    def debug_page_analysis(self, page_text: str, page_num: int):
        """Показывает детальный анализ страницы для отладки"""
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(f"📄 АНАЛИЗ СТРАНИЦЫ {page_num}")
        self.stdout.write("=" * 70)
        self.stdout.write(f"Длина текста: {len(page_text)} символов")

        # Пробуем все методы
        quick_blocks = self.extract_recipe_blocks_quick(page_text)
        self.stdout.write(f"\n⚡ Быстрый метод: {len(quick_blocks)} блоков")

        llm_recipes = self.extract_recipe_boundaries_with_llm(page_text, debug=True)
        self.stdout.write(f"\n🤖 LLM метод: {len(llm_recipes)} рецептов")

        # Визуальное представление
        self.stdout.write("\n📊 Карта страницы (LLM):")
        if llm_recipes:
            for i, recipe in enumerate(llm_recipes):
                start = recipe.get('start', 0)
                end = recipe.get('end', len(page_text))
                length = end - start
                title = recipe.get('title', f'Рецепт {i + 1}')
                bar_length = int(length / len(page_text) * 50) if len(page_text) > 0 else 0
                self.stdout.write(f"   {i + 1}. {title[:30]:30} {'█' * bar_length}")
        else:
            self.stdout.write("   Нет данных от LLM")

        self.stdout.write("\n" + "=" * 70 + "\n")

    def handle(self, *args, **options):
        pdf_path = options['pdf_path']
        start_page = options['start_page']
        end_page = options['end_page']
        max_recipes = options['max_recipes']
        no_cache = options['no_cache']
        debug = options['debug']

        if not os.path.exists(pdf_path):
            self.stderr.write(self.style.ERROR(f'❌ Файл не найден: {pdf_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'📄 Читаю PDF: {pdf_path}'))

        # Извлекаем текст из PDF
        md_text = pymupdf4llm.to_markdown(pdf_path)

        # Разбиваем на страницы
        pages = md_text.split('\f')
        total_pages = len(pages)

        if end_page is None:
            end_page = total_pages

        end_page = min(end_page, total_pages)

        self.stdout.write(f"📊 Всего страниц: {total_pages}")
        self.stdout.write(f"🔍 Обрабатываю страницы: {start_page} - {end_page}")
        self.stdout.write(f"💾 Кэширование: {'выключено' if no_cache else 'включено'}")

        if debug:
            self.stdout.write("\n🔧 РЕЖИМ ОТЛАДКИ ВКЛЮЧЁН\n")

        imported_count = 0

        for page_num in range(start_page - 1, end_page):
            page_text = pages[page_num]

            if not page_text.strip():
                if debug:
                    self.stdout.write(f"⚠️ Страница {page_num + 1} пуста, пропускаю")
                continue

            if debug:
                self.debug_page_analysis(page_text, page_num + 1)

            # Разбиваем страницу на рецепты
            recipes = self.smart_split_page(page_text, debug, not no_cache)

            self.stdout.write(f"\n📄 Страница {page_num + 1}: {len(recipes)} рецептов")

            for i, recipe_info in enumerate(recipes):
                if max_recipes and imported_count >= max_recipes:
                    self.stdout.write(
                        self.style.WARNING(f'\n⚠️ Достигнуто максимальное количество рецептов: {max_recipes}'))
                    break

                title = recipe_info.get('title', f'Рецепт со страницы {page_num + 1}')
                recipe_text = recipe_info.get('text', '')

                if not recipe_text:
                    continue

                self.stdout.write(f"   🍲 Импортирую: {title[:50]}...")

                if self.safe_import_recipe(recipe_text, title, debug):
                    imported_count += 1

            if max_recipes and imported_count >= max_recipes:
                break

        self.stdout.write(self.style.SUCCESS(f'\n✅ Всего импортировано рецептов: {imported_count}'))