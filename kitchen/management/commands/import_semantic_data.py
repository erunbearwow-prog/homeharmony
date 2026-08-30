# kitchen/management/commands/import_semantic_data.py

import json
from django.core.management.base import BaseCommand
from kitchen.models import AbstractIngredient, SemanticTag


class Command(BaseCommand):
    help = 'Импорт семантических данных из JSON файлов'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к JSON файлу')
        parser.add_argument('--update', action='store_true', help='Обновить существующие')

    def handle(self, *args, **options):
        file_path = options['file_path']

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ищем или создаем ингредиент
        ingredient, created = AbstractIngredient.objects.get_or_create(
            name=data['name'],
            defaults={
                'name_normalized': data.get('name_normalized', ''),
                'short_description': data.get('short_description', ''),
                'description': data.get('description', ''),
                'semantic_data': data.get('semantic_data', {}),
            }
        )

        # Добавляем теги
        for tag_name in data.get('tags', []):
            tag, _ = SemanticTag.objects.get_or_create(
                name=tag_name,
                defaults={'tag_type': 'property'}
            )
            ingredient.semantic_tags.add(tag)

        self.stdout.write(
            self.style.SUCCESS(f'✅ {ingredient.name} {"создан" if created else "обновлен"}')
        )