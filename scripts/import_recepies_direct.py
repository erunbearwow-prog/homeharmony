# scripts/import_recipes_direct.py

"""
Прямой импорт рецептов из извлеченного текста
Запуск: python scripts/import_recipes_direct.py
"""

import os
import sys
import re
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import Recipe, ProfessionalIngredient, Ingredient, AbstractIngredient, RecipeStep

# Рецепты, которые точно есть и нужны
RECIPES_TO_IMPORT = {
    '16': 'Суп из баранины',
    '17': 'Суп из баранины с крупой',
    '18': 'Акудрца — суп из фасоли',
    '20': 'Окрошка по-абхазски',
    '21': 'Говядина, тушенная по-абхазски',
    '23': 'Акутеицарш — курица под ореховым соусом',
    '24': 'Цыпленок под томатным соусом',
    '51': 'Телятина по-башкирски',
    '53': 'Пельмени мясные с картофелем',
    '107': 'Птица жареная по-кабардински',
    '117': 'Курица, тушенная с картофелем',
    '131': 'Жаркое из баранины и свинины',
    '152': 'Жаркое по-кубански с баклажанами и алычой',
    '213': 'Азу по-татарски',
    '95': 'Салат по-ингушски',
    '100': 'Салат из свежих огурцов и помидоров',
    '171': 'Салат из зеленого лука',
    '110': 'Койжапха (соус сметанный)',
    '56': 'Вак-балеш (пирожки с начинкой)',
    '194': 'Пампушки',
    '219': 'Кыстыбый',
    '155': 'Блины по-кубански',
    '158': 'Кабачки, фаршированные овощами и рисом',
    '80': 'Рыба донская тушеная',
    '186': 'Полбяная каша',
    '188': 'Каша пшенная с тыквой',
    '204': 'Пельмени с вишнями',
}


def extract_ingredients_from_text(text, recipe_number):
    """Извлекает ингредиенты из текста рецепта"""

    ingredients = []
    lines = text.split('\n')

    in_ingredients = False
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Проверяем, не конец ли ингредиентов
        if 'Выход' in line:
            break

        # Парсим ингредиент
        # Формат: "Лук репчатый 75 63" или "Яйцо 6 шт. 240"
        patterns = [
            r'^([А-Яа-я\s\-\(\)]+?)\s+(\d+[\d,.]*)\s+(\d+[\d,.]*)$',
            r'^([А-Яа-я\s\-\(\)]+?)\s+(\d+[\d,.]*)\s+[а-яА-Я.]+\s+(\d+[\d,.]*)$',
        ]

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                name = match.group(1).strip()
                gross = float(match.group(2).replace(',', '.'))
                net = float(match.group(3).replace(',', '.'))
                ingredients.append({
                    'name': name,
                    'gross': gross,
                    'net': net
                })
                break

    return ingredients


def find_ingredient(name):
    """Находит ингредиент в базе"""
    # Пробуем найти по точному названию
    ing = Ingredient.objects.filter(name__iexact=name).first()
    if ing:
        return ing

    # Пробуем через AbstractIngredient
    abstract = AbstractIngredient.objects.filter(name__icontains=name).first()
    if abstract:
        return Ingredient.objects.filter(abstract=abstract).first()

    # Пробуем частичное совпадение
    ing = Ingredient.objects.filter(name__icontains=name).first()
    if ing:
        return ing

    return None


def import_recipe(recipe_data, text):
    """Импортирует один рецепт"""

    print(f"\n📄 #{recipe_data['number']}. {recipe_data['name']}")

    # Проверяем, существует ли уже
    existing = Recipe.objects.filter(title__icontains=recipe_data['name'][:30]).first()
    if existing:
        print(f"  ℹ️ Уже существует (ID: {existing.id})")
        return None

    # Извлекаем ингредиенты
    ingredients = extract_ingredients_from_text(text, recipe_data['number'])

    if not ingredients:
        print(f"  ⚠️ Не найдены ингредиенты")
        return None

    print(f"  📊 Найдено ингредиентов: {len(ingredients)}")

    # Создаем рецепт
    recipe = Recipe.objects.create(
        title=recipe_data['name'],
        description=f"Рецепт из сборника\nИнгредиенты: {len(ingredients)}",
        servings=4,
        is_professional=True,
        total_time=30,
    )
    print(f"  ✅ Создан рецепт #{recipe.id}")

    # Добавляем ингредиенты
    added = 0
    for ing_data in ingredients:
        ingredient = find_ingredient(ing_data['name'])

        if ingredient:
            ProfessionalIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                gross_weight=ing_data['gross'],
                net_weight=ing_data['net'],
                unit='г'
            )
            added += 1
        else:
            print(f"    ⚠️ Ингредиент не найден: {ing_data['name']}")

    print(f"  ✅ Добавлено ингредиентов: {added}")
    return recipe


def main():
    print("=" * 70)
    print("🍽️  ПРЯМОЙ ИМПОРТ РЕЦЕПТОВ")
    print("=" * 70)

    # Читаем текст
    text_path = project_root / 'data' / 'extracted_pdf' / 'full_text.txt'

    if not text_path.exists():
        print(f"❌ Файл не найден: {text_path}")
        return

    with open(text_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    # Разбиваем по страницам
    pages = re.split(r'СТРАНИЦА \d+', full_text)

    # Ищем рецепты
    found = 0
    for number, name in RECIPES_TO_IMPORT.items():
        # Ищем рецепт в тексте
        pattern = rf'{number}\.\s+{name}'

        for page in pages:
            if re.search(pattern, page):
                # Нашли рецепт
                import_recipe({'number': number, 'name': name}, page)
                found += 1
                break

    print(f"\n📊 Импортировано рецептов: {found}")


if __name__ == '__main__':
    main()