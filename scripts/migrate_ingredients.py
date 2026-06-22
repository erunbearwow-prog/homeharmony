# migrate_ingredients.py
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeharmony.settings')
django.setup()

from kitchen.models import Recipe, RecipeFoodItem


def migrate():
    print("🚀 Начинаем миграцию ингредиентов...")

    recipes = Recipe.objects.all()
    total_migrated = 0

    for recipe in recipes:
        # Получаем старые ингредиенты
        old_ingredients = recipe.recipe_ingredients.select_related('ingredient').all()

        for old in old_ingredients:
            # Создаём новую запись, если её ещё нет
            obj, created = RecipeFoodItem.objects.get_or_create(
                recipe=recipe,
                ingredient=old.ingredient,
                defaults={
                    'quantity': old.quantity,
                    'unit': old.unit,
                    'notes': old.notes,
                    'is_scalable': old.is_scalable,
                }
            )
            if created:
                total_migrated += 1

        print(f"✅ Рецепт '{recipe.title}': обработано {old_ingredients.count()} ингредиентов")

    print(f"\n✅ Миграция завершена! Перенесено ингредиентов: {total_migrated}")


if __name__ == '__main__':
    migrate()