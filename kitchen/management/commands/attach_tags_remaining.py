# kitchen/management/commands/attach_tags_remaining.py
from django.core.management.base import BaseCommand
from django.db import transaction
from kitchen.models import AbstractIngredient, SemanticTag
from slugify import slugify


class Command(BaseCommand):
    help = 'Дорабатывает привязку тегов для ингредиентов без тегов'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Ищем ингредиенты без тегов...")

        # Находим ингредиенты без тегов
        ingredients_without_tags = AbstractIngredient.objects.filter(semantic_tags__isnull=True)
        total = ingredients_without_tags.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Все ингредиенты уже имеют теги!'))
            return

        self.stdout.write(f"📊 Найдено ингредиентов без тегов: {total}")

        # Получаем все теги
        all_tags = SemanticTag.objects.all()
        tag_dict = {tag.name.lower(): tag for tag in all_tags}
        tag_names = list(tag_dict.keys())

        # Создаем словарь для частичных совпадений
        partial_matches = {}

        # Создаем "карту" ключевых слов для тегов
        tag_keywords = {}
        for tag_name in tag_names:
            # Разбиваем тег на слова
            words = tag_name.lower().split()
            for word in words:
                if len(word) > 2:  # Игнорируем слишком короткие слова
                    if word not in tag_keywords:
                        tag_keywords[word] = []
                    tag_keywords[word].append(tag_name)

        attached_count = 0
        still_empty = 0

        with transaction.atomic():
            for ingredient in ingredients_without_tags:
                ingredient_name = ingredient.name.lower()
                tags_to_add = set()

                # 1. Прямое совпадение (уже было в первом скрипте)
                for tag_name in tag_names:
                    if tag_name in ingredient_name:
                        tags_to_add.add(tag_name)

                # 2. Частичное совпадение (по словам)
                if not tags_to_add:
                    # Разбиваем название ингредиента на слова
                    words = ingredient_name.split()
                    for word in words:
                        # Очищаем слово от спецсимволов
                        clean_word = ''.join(c for c in word if c.isalpha())
                        if len(clean_word) > 2:
                            # Ищем совпадения в тегах
                            for tag_name in tag_names:
                                if clean_word in tag_name.lower() or tag_name.lower() in clean_word:
                                    tags_to_add.add(tag_name)

                # 3. Поиск по ключевым словам (если тегов всё еще нет)
                if not tags_to_add:
                    for word in ingredient_name.split():
                        clean_word = ''.join(c for c in word if c.isalpha())
                        if len(clean_word) > 2 and clean_word in tag_keywords:
                            for tag_name in tag_keywords[clean_word]:
                                tags_to_add.add(tag_name)

                # 4. Если теги найдены — привязываем
                if tags_to_add:
                    tag_objects = [tag_dict.get(tag_name) for tag_name in tags_to_add if tag_name in tag_dict]
                    if tag_objects:
                        ingredient.semantic_tags.add(*tag_objects)
                        attached_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ {ingredient.name}: добавлено {len(tag_objects)} тегов'
                            )
                        )
                    else:
                        still_empty += 1
                else:
                    still_empty += 1
                    # Логируем ингредиенты без тегов для анализа
                    self.stdout.write(
                        self.style.WARNING(
                            f'⏩ {ingredient.name}: теги не найдены'
                        )
                    )

            self.stdout.write(self.style.SUCCESS(
                f'\n✨ Готово! Добавлены теги для {attached_count} ингредиентов, '
                f'без тегов осталось: {still_empty}'
            ))