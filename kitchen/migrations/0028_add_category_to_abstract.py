# kitchen/migrations/0028_add_category_to_abstract.py

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kitchen', '0027_remove_ingredient_calories_and_more'),  # <-- правильная зависимость
    ]

    operations = [
        # ТОЛЬКО ДОБАВЛЯЕМ ПОЛЕ category В AbstractIngredient
        migrations.AddField(
            model_name='abstractingredient',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='kitchen.ingredientcategory',
                verbose_name='Категория'
            ),
        ),
        # НИЧЕГО НЕ УДАЛЯЕМ!
    ]