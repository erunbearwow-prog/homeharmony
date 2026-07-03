# kitchen/management/commands/clean_category_names.py
from django.core.management.base import BaseCommand
from django.db import transaction
from kitchen.models import IngredientCategory
import re


class Command(BaseCommand):
    help = 'Убирает коды из названий категорий'

    def handle(self, *args, **options):
        self.stdout.write("🧹 Очищаем названия категорий от кодов...")

        categories = IngredientCategory.objects.all()
        updated_count = 0

        with transaction.atomic():
            for cat in categories:
                old_name = cat.name
                # Убираем код в начале: "01. ОВОЩИ" → "ОВОЩИ"
                # или "01.01 --- Картофель" → "Картофель"
                new_name = re.sub(r'^[\d.]+\s*---\s*', '', old_name)
                new_name = re.sub(r'^[\d.]+\s+', '', new_name)
                new_name = new_name.strip()

                if new_name != old_name:
                    cat.name = new_name
                    cat.save(update_fields=['name'])
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ "{old_name}" → "{new_name}"'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(f'\n✨ Готово! Обновлено: {updated_count} категорий')
        )