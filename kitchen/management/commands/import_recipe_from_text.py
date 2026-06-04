# kitchen/management/commands/import_recipe_from_text.py
import json
import re
import ollama
from pydantic import ValidationError
from django.core.management.base import BaseCommand
from kitchen.models import Recipe, RecipeIngredient, Ingredient
from kitchen.recipe_schema import Recipe as RecipeSchema


def normalize_quantity(value) -> float:
    """
    Нормализует количество ингредиента из разных форматов
    """
    if value is None:
        return 0

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return 0

        # Обработка дробей (например, "1/2")
        if '/' in value:
            parts = value.split('/')
            if len(parts) == 2:
                try:
                    return float(parts[0]) / float(parts[1])
                except:
                    pass

        # Обработка диапазонов (например, "1-1.5")
        if '-' in value:
            parts = value.split('-')
            if len(parts) == 2:
                try:
                    return (float(parts[0]) + float(parts[1])) / 2
                except:
                    pass

        # Простое число
        try:
            return float(value)
        except:
            return 0

    return 0


# kitchen/management/commands/import_recipe_from_text.py

def extract_recipe_from_text(text: str) -> dict:
    """
    Извлекает рецепт из текста с помощью LLM (без Pydantic валидации)
    """
    prompt = f"""
        Ты — профессиональный кулинарный редактор. Внимательно прочитай текст рецепта и извлеки из него структурированную информацию.

        ВОТ ТЕКСТ РЕЦЕПТА:
        ---
        {text}
        ---

        ПРАВИЛА ИЗВЛЕЧЕНИЯ:

        1. НАЗВАНИЕ (title):
           - Обычно в начале текста, часто с номером (1., 2. и т.д.)
           - Убери номер, оставь только название

        2. ИНГРЕДИЕНТЫ (ingredients):
           - Ищи строки с числами
           - Формат: "название количество единица"
           - Пример: "капуста 160" → {{"name": "капуста", "quantity": 160, "unit": "г"}}
           - Если единица не указана, добавь "г" по умолчанию

        3. ОПИСАНИЕ (description):
           - Текст между ингредиентами и шагами
           - Обычно начинается с "Эти щи готовят...", "Подают с...", "Совет..."

        4. ШАГИ (steps) — ЭТО САМОЕ ВАЖНОЕ:
           - Разбей ВЕСЬ ТЕКСТ после ингредиентов на логические шаги
           - Каждое предложение с действием — отдельный шаг
           - НЕ ПРОПУСКАЙ детали: время, температуру, последовательность
           - Сохраняй полные предложения

           ПРИМЕР правильного разбиения:
           Текст: "Коренья и лук нарезать дольками и спассеровать с жиром, а через 5-8 минут прибавить томат-пюре. Капусту нарезать шашками. В кипящий бульон положить капусту и варить 20-30 минут."

           Шаги:
           1. "Коренья и лук нарезать дольками и спассеровать с жиром"
           2. "Через 5-8 минут прибавить томат-пюре"
           3. "Капусту нарезать шашками"
           4. "В кипящий бульон положить капусту и варить 20-30 минут"

        ФОРМАТ ОТВЕТА (ТОЛЬКО JSON, БЕЗ ПОЯСНЕНИЙ):
        {{
            "title": "название рецепта",
            "description": "описание",
            "ingredients": [
                {{"name": "название", "quantity": число, "unit": "г"}}
            ],
            "steps": [
                {{"order": 1, "instruction": "полный текст шага"}},
                {{"order": 2, "instruction": "полный текст шага"}}
            ]
        }}

        ВАЖНО:
        - Не создавай пустых шагов
        - Каждый шаг должен быть содержательным
        - Сохраняй все детали из оригинального текста
        """

    response = ollama.chat(
        model='qwen2.5:7b',
        messages=[{'role': 'user', 'content': prompt}],
        format='json'
    )

    data = json.loads(response['message']['content'])

    # Нормализуем количества ингредиентов (без Pydantic)
    for ing in data.get('ingredients', []):
        quantity = ing.get('quantity', 0)
        if quantity is None or quantity == '':
            quantity = 0
        elif isinstance(quantity, str):
            # Обработка дробей
            if '/' in quantity:
                parts = quantity.split('/')
                if len(parts) == 2:
                    try:
                        quantity = float(parts[0]) / float(parts[1])
                    except:
                        quantity = 0
            # Обработка диапазонов
            elif '-' in quantity:
                parts = quantity.split('-')
                if len(parts) == 2:
                    try:
                        quantity = (float(parts[0]) + float(parts[1])) / 2
                    except:
                        quantity = 0
            else:
                try:
                    quantity = float(quantity)
                except:
                    quantity = 0
        elif isinstance(quantity, (int, float)):
            quantity = float(quantity)
        else:
            quantity = 0

        ing['quantity'] = quantity

    return data


class Command(BaseCommand):
    help = 'Импортирует рецепт из текста'

    def add_arguments(self, parser):
        parser.add_argument('text', type=str, help='Текст рецепта')
        parser.add_argument('--title', type=str, help='Название рецепта (опционально)', default=None)

    def handle(self, *args, **options):
        text = options['text']
        custom_title = options['title']

        self.stdout.write("🔄 Извлекаю рецепт с помощью LLM...")

        try:
            # Извлекаем JSON
            recipe_data = extract_recipe_from_text(text)

            # Валидируем через Pydantic
            validated = RecipeSchema.model_validate(recipe_data)

            # Используем указанное название, если передано
            title = custom_title if custom_title else validated.title

            self.stdout.write(f"📝 Сохраняю рецепт: {title}")

            # Сохраняем рецепт с описанием
            recipe = Recipe.objects.create(
                title=title,
                description=validated.description,  # ← добавляем описание
                total_time=0,
                servings=4,
                difficulty='medium'
            )

            # Сохраняем ингредиенты
            ingredients_count = 0
            for ing in validated.ingredients:
                if not ing.name:
                    continue

                ingredient_obj, created = Ingredient.objects.get_or_create(
                    name=ing.name.strip(),
                    defaults={'default_unit': ing.unit}
                )

                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient_obj,
                    quantity=ing.quantity or 0,
                    unit=ing.unit
                )
                ingredients_count += 1

            # Сохраняем шаги
            steps_count = 0
            for step in validated.steps:
                recipe.steps.create(
                    order=step.order,
                    title=f"Шаг {step.order}",
                    instruction=step.instruction
                )
                steps_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'✅ Рецепт "{recipe.title}" импортирован!\n'
                f'   📊 Ингредиентов: {ingredients_count}\n'
                f'   📝 Шагов: {steps_count}'
            ))

        except ValidationError as e:
            self.stderr.write(self.style.ERROR(f'❌ Ошибка валидации: {e}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'❌ Ошибка: {e}'))