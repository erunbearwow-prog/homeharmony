# kitchen/management/commands/import_single_recipe.py
import os
import json
import re
import pymupdf4llm
import ollama
from django.core.management.base import BaseCommand
from kitchen.models import Recipe, RecipeIngredient, Ingredient


def clean_text(text: str) -> str:
    """Очищает текст от мусора"""
    # Убираем номера рецептов в скобках
    text = re.sub(r'\(\d+\)', '', text)
    # Убираем сноски
    text = re.sub(r'[*⁰¹²³⁴⁵⁶⁷⁸⁹†‡]+', '', text)
    # Убираем номера страниц
    text = re.sub(r'\n\s*\d+\s*$', '', text, flags=re.MULTILINE)
    # Убираем лишние переводы строк
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_recipe_from_text(text: str) -> dict:
    """Извлекает рецепт из текста с помощью LLM"""

    prompt = f"""
    Ты — профессиональный кулинарный редактор. Извлеки из текста рецепт в формате JSON.

    ТЕКСТ РЕЦЕПТА:
    ---
    {text[:3000]}
    ---

    ФОРМАТ ОТВЕТА (ТОЛЬКО JSON):
    {{
        "title": "Название рецепта",
        "description": "Краткое описание (если есть)",
        "ingredients": [
            {{"name": "название ингредиента", "quantity": число, "unit": "г/мл/шт/ст.л"}}
        ],
        "steps": [
            "Первый шаг приготовления",
            "Второй шаг приготовления"
        ]
    }}

    ПРАВИЛА:
    1. Название — первая строка или самое заметное название.
    2. Ингредиенты: каждое количество и название. Если нет количества — поставь 0.
    3. Шаги: разбей на логические действия, НЕ ПРОПУСКАЙ детали.
    4. Единицы измерения: г, мл, шт, ст.л., ч.л.
    5. Верни ТОЛЬКО JSON, без пояснений.
    """

    response = ollama.chat(
        model='qwen2.5:7b',
        messages=[{'role': 'user', 'content': prompt}],
        format='json'
    )

    data = json.loads(response['message']['content'])

    # Нормализуем данные
    # Ингредиенты
    for ing in data.get('ingredients', []):
        if not ing.get('name'):
            continue
        if not ing.get('unit') or ing.get('unit') == '':
            # Определяем единицу по умолчанию
            name = ing['name'].lower()
            if any(w in name for w in ['молоко', 'вода', 'бульон', 'сок', 'масло']):
                ing['unit'] = 'мл'
            else:
                ing['unit'] = 'г'

        quantity = ing.get('quantity', 0)
        if quantity is None or quantity == '':
            quantity = 0
        elif isinstance(quantity, str):
            # Обработка дробей
            if '/' in quantity:
                parts = quantity.split('/')
                try:
                    quantity = float(parts[0]) / float(parts[1])
                except:
                    quantity = 0
            else:
                try:
                    quantity = float(quantity.replace(',', '.'))
                except:
                    quantity = 0
        ing['quantity'] = float(quantity)

    # Шаги — оставляем как есть (должен быть массив)
    if 'steps' in data and isinstance(data['steps'], list):
        # Если шаги пришли как строки, оставляем
        if data['steps'] and isinstance(data['steps'][0], str):
            data['steps'] = [{'order': i + 1, 'instruction': step} for i, step in enumerate(data['steps']) if
                             step.strip()]

    return data


class Command(BaseCommand):
    help = 'Импортирует один рецепт из PDF'

    def add_arguments(self, parser):
        parser.add_argument('pdf_path', type=str, help='Путь к PDF-файлу')
        parser.add_argument('--debug', action='store_true', help='Показать отладочную информацию')

    def handle(self, *args, **options):
        pdf_path = options['pdf_path']
        debug = options['debug']

        if not os.path.exists(pdf_path):
            self.stderr.write(self.style.ERROR(f'❌ Файл не найден: {pdf_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'📄 Читаю PDF: {pdf_path}'))

        # Извлекаем текст из PDF
        md_text = pymupdf4llm.to_markdown(pdf_path)

        # Очищаем текст
        cleaned_text = clean_text(md_text)

        if debug:
            self.stdout.write(f"\n📝 Очищенный текст (первые 500 символов):\n{cleaned_text[:500]}\n")

        self.stdout.write("🔄 Извлекаю рецепт с помощью LLM...")

        try:
            # Извлекаем рецепт
            recipe_data = extract_recipe_from_text(cleaned_text)

            if debug:
                self.stdout.write(
                    f"\n📊 Полученные данные:\n{json.dumps(recipe_data, indent=2, ensure_ascii=False)[:1000]}\n")

            # Проверяем, не существует ли уже
            title = recipe_data.get('title', 'Без названия')

            if Recipe.objects.filter(title=title).exists():
                self.stdout.write(self.style.WARNING(f'⚠️ Рецепт "{title}" уже существует'))
                return

            # Сохраняем рецепт
            recipe = Recipe.objects.create(
                title=title,
                description=recipe_data.get('description', ''),
                total_time=0,
                servings=4,
                difficulty='medium'
            )

            self.stdout.write(f"📝 Сохраняю рецепт: {title}")

            # Сохраняем ингредиенты
            ingredients_count = 0
            for ing in recipe_data.get('ingredients', []):
                if not ing.get('name'):
                    continue

                name = ing['name'].strip()
                unit = ing.get('unit', 'г')
                quantity = ing.get('quantity', 0)

                ingredient_obj, created = Ingredient.objects.get_or_create(
                    name=name,
                    defaults={'default_unit': unit}
                )

                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient_obj,
                    quantity=quantity,
                    unit=unit
                )
                ingredients_count += 1

            # Сохраняем шаги
            steps_count = 0
            for step in recipe_data.get('steps', []):
                instruction = step.get('instruction', '') if isinstance(step, dict) else step
                if instruction and len(instruction.strip()) > 5:
                    recipe.steps.create(
                        order=steps_count + 1,
                        title=f"Шаг {steps_count + 1}",
                        instruction=instruction.strip()
                    )
                    steps_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Рецепт "{title}" импортирован!\n'
                f'   📊 Ингредиентов: {ingredients_count}\n'
                f'   📝 Шагов: {steps_count}'
            ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'❌ Ошибка: {e}'))
            if debug:
                import traceback
                traceback.print_exc()