# kitchen/migrations/XXXX_migrate_recipeingredient_to_homeingredient.py

from django.db import migrations, models


def copy_recipeingredient_to_homeingredient(apps, schema_editor):
    RecipeIngredient = apps.get_model('kitchen', 'RecipeIngredient')
    HomeIngredient = apps.get_model('kitchen', 'HomeIngredient')

    total = RecipeIngredient.objects.count()
    print(f"📦 Копируем {total} записей из RecipeIngredient в HomeIngredient...")

    home_ingredients = []
    for ri in RecipeIngredient.objects.select_related('recipe', 'ingredient').iterator():
        home_ingredients.append(
            HomeIngredient(
                recipe=ri.recipe,
                ingredient=ri.ingredient,
                quantity=ri.quantity,
                unit=ri.unit,
                notes=ri.notes,
                is_scalable=ri.is_scalable,
            )
        )

    if home_ingredients:
        HomeIngredient.objects.bulk_create(home_ingredients, batch_size=1000)
        print(f"✅ Скопировано {len(home_ingredients)} записей")
    else:
        print("ℹ️ Нет данных для копирования")


class Migration(migrations.Migration):
    dependencies = [
        ('kitchen', 'последняя_миграция'),  # Укажите правильную
    ]

    operations = [
        # Шаг 1: Копируем данные
        migrations.RunPython(
            copy_recipeingredient_to_homeingredient,
            reverse_code=migrations.RunPython.noop
        ),

        # Шаг 2: Переименовываем старую таблицу (на всякий случай)
        migrations.AlterModelTable(
            name='RecipeIngredient',
            table='kitchen_recipeingredient_old',
        ),

        # Шаг 3: Удаляем модель из ORM (но таблица остается)
        migrations.DeleteModel(
            name='RecipeIngredient',
        ),

        # Шаг 4: Проверяем, что HomeIngredient существует
        # (она уже есть в models.py)
    ]