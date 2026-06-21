# scripts/parse_all_recipes.py

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Optional

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
import django

django.setup()

from kitchen.models import Cuisine, Recipe, ProfessionalIngredient, AbstractIngredient, RecipeStep


def parse_recipes_from_text(text_path: Path) -> List[Dict]:
    """Парсит все рецептуры из текстового файла"""

    print("📖 Чтение текста...")
    with open(text_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Разбиваем по страницам
    pages = re.split(r'СТРАНИЦА \d+', content)

    recipes = []
    current_recipe = None
    current_cuisine = None
    in_technique = False

    print(f"📄 Обработка {len(pages)} страниц...")

    for page_idx, page_text in enumerate(pages, 1):
        if not page_text.strip():
            continue

        lines = page_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Проверяем, не кухня ли это
            if re.match(r'^[А-ЯЁ\s\-]+КУХНЯ$', line):
                current_cuisine = line.strip()
                continue

            # Проверяем, не начало ли новой рецептуры
            match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if match:
                # Сохраняем предыдущую
                if current_recipe:
                    recipes.append(current_recipe)

                # Начинаем новую
                current_recipe = {
                    'number': int(match.group(1)),
                    'name': match.group(2).strip(),
                    'cuisine': current_cuisine,
                    'ingredients': [],
                    'yield': None,
                    'technique': [],
                    'page': page_idx + 37  # страница в PDF
                }
                in_technique = False
                continue

            # Парсим ингредиенты
            ing_match = re.match(r'^([А-Яа-я\s\-\(\)]+)\s+([\d,]+(?:\s+шт\.)?)\s+([\d,]+)$', line)
            if ing_match and current_recipe and not in_technique:
                name = ing_match.group(1).strip()
                gross_str = ing_match.group(2).strip()
                net_str = ing_match.group(3).strip()

                gross_str = re.sub(r'\s+шт\.', '', gross_str)
                net_str = re.sub(r'\s+шт\.', '', net_str)

                try:
                    gross = float(gross_str.replace(',', '.'))
                    net = float(net_str.replace(',', '.'))

                    current_recipe['ingredients'].append({
                        'name': name,
                        'gross': gross,
                        'net': net
                    })
                except ValueError:
                    if current_recipe:
                        current_recipe['technique'].append(line)
                continue

            # Проверяем выход
            if 'Выход' in line and current_recipe:
                yield_match = re.search(r'(\d+)', line)
                if yield_match:
                    current_recipe['yield'] = int(yield_match.group(1))
                continue

            # Технология
            if current_recipe:
                if not re.match(r'^[А-Яа-я\s\-\(\)]+\s+[\d,]+\s+[\d,]+', line):
                    if not re.match(r'^\d+\.', line):
                        current_recipe['technique'].append(line)
                        in_technique = True

    # Добавляем последнюю
    if current_recipe:
        recipes.append(current_recipe)

    return recipes


def save_recipes_to_json(recipes: List[Dict], output_path: Path):
    """Сохраняет рецептуры в JSON"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)
    print(f"✅ Сохранено {len(recipes)} рецептур в {output_path}")


def import_to_db(recipes: List[Dict]):
    """Импортирует рецептуры в базу данных"""

    stats = {
        'created': 0,
        'ingredients_added': 0,
        'ingredients_not_found': 0,
        'errors': 0
    }

    print("\n" + "=" * 70)
    print("📥 ИМПОРТ РЕЦЕПТУР В БАЗУ ДАННЫХ")
    print("=" * 70)

    for i, recipe_data in enumerate(recipes, 1):
        try:
            # Пропускаем слишком короткие рецептуры
            if len(recipe_data['ingredients']) < 2:
                continue

            print(f"\n{i}. {recipe_data['number']}. {recipe_data['name']}")

            # Находим или создаем кухню
            cuisine = None
            if recipe_data.get('cuisine'):
                cuisine_name = recipe_data['cuisine'].replace('КУХНЯ', '').strip()
                cuisine, _ = Cuisine.objects.get_or_create(
                    name=cuisine_name,
                    defaults={'region': cuisine_name}
                )

            # Создаем рецепт (профессиональный)
            recipe, created = Recipe.objects.get_or_create(
                title=recipe_data['name'],
                defaults={
                    'cuisine': cuisine,
                    'description': '\n'.join(recipe_data.get('technique', [])),
                    'servings': 4,
                    'is_professional': True,
                    'total_time': 30,  # по умолчанию
                }
            )

            if created:
                stats['created'] += 1
                print(f"  ✅ Создан рецепт #{recipe.id}")
            else:
                print(f"  ℹ️ Рецепт уже существует (ID: {recipe.id})")
                continue

            # Добавляем ингредиенты
            for ing_data in recipe_data['ingredients']:
                # Ищем ингредиент по названию
                ingredient = AbstractIngredient.objects.filter(
                    name__icontains=ing_data['name']
                ).first()

                if ingredient:
                    # Создаем ProfessionalIngredient
                    ProfessionalIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        gross_weight=ing_data['gross'],
                        net_weight=ing_data['net'],
                        unit='г'
                    )
                    stats['ingredients_added'] += 1
                else:
                    stats['ingredients_not_found'] += 1
                    print(f"    ⚠️ Ингредиент не найден: {ing_data['name']}")

            # Создаем шаг из технологии
            if recipe_data.get('technique'):
                technique_text = '\n'.join(recipe_data['technique'])
                RecipeStep.objects.create(
                    recipe=recipe,
                    order=1,
                    title='Приготовление',
                    instruction=technique_text,
                    duration=30
                )

            print(f"  ✅ Добавлено ингредиентов: {len(recipe_data['ingredients'])}")

        except Exception as e:
            stats['errors'] += 1
            print(f"  ❌ Ошибка: {e}")

    return stats


def main():
    print("=" * 70)
    print("🍽️  ИЗВЛЕЧЕНИЕ ВСЕХ РЕЦЕПТУР")
    print("=" * 70)

    extracted_dir = project_root / 'data' / 'extracted_pdf'
    text_path = extracted_dir / 'full_text.txt'
    output_json = extracted_dir / 'all_recipes.json'

    if not text_path.exists():
        print(f"❌ Файл не найден: {text_path}")
        print("   Сначала запустите extract_pdf_text.py")
        return

    # Парсим
    print("\n📊 Парсинг рецептур...")
    recipes = parse_recipes_from_text(text_path)

    print(f"\n📊 Найдено рецептур: {len(recipes)}")

    # Статистика по кухням
    cuisines = {}
    for r in recipes:
        cuisine = r.get('cuisine', 'Не указана')
        cuisines[cuisine] = cuisines.get(cuisine, 0) + 1

    print("\n📊 КУХНИ:")
    for cuisine, count in sorted(cuisines.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cuisine}: {count} рецептур")

    # Сохраняем JSON
    save_recipes_to_json(recipes, output_json)

    # Импортируем
    print("\n" + "=" * 70)
    response = input("💡 Импортировать рецептуры в базу данных? (y/n): ")

    if response.lower() == 'y':
        stats = import_to_db(recipes)

        print("\n" + "=" * 70)
        print("📊 СТАТИСТИКА ИМПОРТА")
        print("=" * 70)
        print(f"  Создано рецептов: {stats['created']}")
        print(f"  Добавлено ингредиентов: {stats['ingredients_added']}")
        print(f"  Ингредиентов не найдено: {stats['ingredients_not_found']}")
        print(f"  Ошибок: {stats['errors']}")
        print("=" * 70)
    else:
        print("ℹ️ Импорт отменен. Данные сохранены в JSON.")


if __name__ == '__main__':
    main()