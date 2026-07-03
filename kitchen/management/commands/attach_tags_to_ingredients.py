# kitchen/management/commands/attach_tags_to_ingredients.py
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from kitchen.models import AbstractIngredient, SemanticTag


class Command(BaseCommand):
    help = 'Автоматически привязывает теги к ингредиентам по ключевым словам'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Начинаем привязку тегов к ингредиентам...")

        # Получаем все теги (создаем словарь для быстрого доступа)
        all_tags = SemanticTag.objects.all()
        tag_dict = {tag.name.lower(): tag for tag in all_tags}
        tag_names = list(tag_dict.keys())

        # Получаем все ингредиенты
        ingredients = AbstractIngredient.objects.all()
        total = ingredients.count()

        attached_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for ingredient in ingredients:
                ingredient_name = ingredient.name.lower()
                tags_to_add = []

                # Ищем теги, которые содержатся в названии ингредиента
                for tag_name in tag_names:
                    if tag_name in ingredient_name:
                        tags_to_add.append(tag_dict[tag_name])

                # Если теги найдены — привязываем
                if tags_to_add:
                    ingredient.semantic_tags.add(*tags_to_add)
                    attached_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ {ingredient.name}: добавлено {len(tags_to_add)} тегов'
                        )
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'⏩ {ingredient.name}: теги не найдены'
                        )
                    )

            self.stdout.write(self.style.SUCCESS(
                f'\n✨ Готово! Привязано тегов к {attached_count} ингредиентам, пропущено: {skipped_count}, ошибок: {error_count}'
            ))