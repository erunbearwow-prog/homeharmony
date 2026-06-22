# test_recipe_extraction.py
import json
import ollama
from pydantic import ValidationError
from kitchen.recipe_schema import Recipe


def extract_recipe_from_text(text: str) -> dict:
    prompt = f"""
    Ты — помощник повара. Извлеки из текста рецепт и верни его в строгом формате JSON.

    СХЕМА JSON (ОБЯЗАТЕЛЬНО СЛЕДУЙ ЭТОЙ СХЕМЕ!):
    {{
        "title": "название рецепта",
        "ingredients": [
            {{"name": "название", "quantity": число, "unit": "единица измерения"}}
        ],
        "steps": [
            {{"order": 1, "instruction": "описание шага"}}
        ]
    }}

    ПРАВИЛА:
    1. Поле "title" — ОБЯЗАТЕЛЬНО. Название рецепта (первая строка или самое заметное название).
    2. Поле "ingredients" — ОБЯЗАТЕЛЬНО. Каждый ингредиент имеет:
       - "name": строка (название)
       - "quantity": число (количество, если нет — поставь 0)
       - "unit": строка (единица измерения: г, мл, шт, ст.л., ч.л.)
    3. Поле "steps" — ОБЯЗАТЕЛЬНО. Каждый шаг имеет:
       - "order": число (порядковый номер)
       - "instruction": строка (описание)

    Вот текст рецепта:
    ---
    {text}
    ---

    ВЕРНИ ТОЛЬКО JSON, БЕЗ ДОПОЛНИТЕЛЬНЫХ ПОЯСНЕНИЙ. НЕ ДОБАВЛЯЙ ДРУГИЕ ПОЛЯ.
    """

    response = ollama.chat(
        model='qwen2.5:7b',
        messages=[{'role': 'user', 'content': prompt}],
        format='json'
    )

    print("Сырой ответ модели:", response['message']['content'])  # Отладка

    # Парсим и валидируем через Pydantic
    try:
        recipe = Recipe.model_validate_json(response['message']['content'])
        return recipe.model_dump()
    except ValidationError as e:
        print(f"Ошибка валидации: {e}")
        # Пробуем исправить распространённые ошибки
        data = json.loads(response['message']['content'])

        # Если модель использовала recipe_name вместо title
        if 'recipe_name' in data and 'title' not in data:
            data['title'] = data.pop('recipe_name')

        # Если нет steps, пробуем извлечь из инструкции
        if 'steps' not in data or not data['steps']:
            if 'instructions' in data:
                data['steps'] = data.pop('instructions')
            elif 'instruction' in data:
                data['steps'] = [{"order": 1, "instruction": data.pop('instruction')}]

        # Повторная валидация
        recipe = Recipe.model_validate(data)
        return recipe.model_dump()


# Тестовый рецепт
test_text = """
Блины на молоке

Ингредиенты:
- Молоко 500 мл
- Яйца 2 шт
- Мука 200 г
- Сахар 2 ст.л.
- Соль 1/2 ч.л.
- Растительное масло 2 ст.л.

Приготовление:
1. В миске взбейте яйца с сахаром и солью.
2. Добавьте молоко и перемешайте.
3. Постепенно всыпьте муку, постоянно помешивая, чтобы не было комков.
4. Добавьте растительное масло и перемешайте.
5. Жарьте блины на разогретой сковороде с двух сторон до золотистого цвета.
"""

if __name__ == "__main__":
    result = extract_recipe_from_text(test_text)
    print("\n=== РЕЗУЛЬТАТ ===\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))