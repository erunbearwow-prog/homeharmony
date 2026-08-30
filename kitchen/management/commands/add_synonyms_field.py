# kitchen/management/commands/add_synonyms_field.py

import os
import json
import glob
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Добавляет поле "synonyms": "" в JSON файлы ингредиентов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет изменено без сохранения',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Путь к директории с JSON файлами
        base_dir = '/homeharmony/semantic_data/abstractIngredients/'
        # Если скрипт запускается из корня проекта
        if not os.path.exists(base_dir):
            base_dir = 'semantic_data/abstractIngredients/'

        # Получаем все JSON файлы
        json_files = glob.glob(os.path.join(base_dir, '*.json'))

        if not json_files:
            self.stdout.write(self.style.ERROR(f'❌ Файлы не найдены в {base_dir}'))
            return

        self.stdout.write(f'📁 Найдено файлов: {len(json_files)}')

        updated = 0
        skipped = 0

        for file_path in json_files:
            self.stdout.write(f'📄 Обработка: {os.path.basename(file_path)}')

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    data = json.loads(content)

                # Проверяем, есть ли поле synonyms
                if 'synonyms' in data:
                    self.stdout.write(f'   ⏭️  Поле synonyms уже есть, пропускаем')
                    skipped += 1
                    continue

                # Создаем новый порядок полей
                new_data = {}
                for key, value in data.items():
                    new_data[key] = value
                    # Вставляем synonyms после name_normalized
                    if key == 'name_normalized':
                        new_data['synonyms'] = ""

                if dry_run:
                    self.stdout.write(f'   🔍 [DRY RUN] Будет добавлено поле synonyms')
                    updated += 1
                else:
                    # Сохраняем обновленный файл
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(new_data, f, ensure_ascii=False, indent=2)
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Добавлено поле synonyms'))
                    updated += 1

            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Ошибка JSON: {e}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Ошибка: {e}'))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n🔍 СУХОЙ ЗАПУСК. Будет обновлено {updated} файлов, пропущено {skipped}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Готово! Обновлено {updated} файлов, пропущено {skipped}'
                )
            )