#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import shutil
import base64
import re
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.db import models
from slugify import slugify
from kitchen.models import AbstractIngredient


class Command(BaseCommand):
    help = 'Экспорт всех AbstractIngredient в отдельные JSON-файлы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='exported_ingredients',
            help='Папка для сохранения JSON-файлов (по умолчанию: exported_ingredients)'
        )
        parser.add_argument(
            '--filter',
            type=str,
            help='Фильтр по названию (поиск по подстроке)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Ограничить количество экспортируемых ингредиентов'
        )
        parser.add_argument(
            '--skip-empty',
            action='store_true',
            help='Пропустить ингредиенты без КБЖУ'
        )
        parser.add_argument(
            '--include-images',
            action='store_true',
            help='Включить экспорт картинок'
        )
        parser.add_argument(
            '--image-mode',
            type=str,
            choices=['path', 'copy', 'base64'],
            default='path',
            help='Режим экспорта картинок: path - только путь, copy - копировать, base64 - встроить в JSON'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Подробный вывод'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        search_filter = options.get('filter')
        limit = options.get('limit')
        skip_empty = options.get('skip_empty')
        include_images = options.get('include_images')
        image_mode = options.get('image_mode', 'path')
        verbose = options.get('verbose')

        # Создаем папку для экспорта
        os.makedirs(output_dir, exist_ok=True)

        # Папка для изображений (если нужно)
        images_dir = None
        if include_images and image_mode == 'copy':
            images_dir = os.path.join(output_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)

        # Получаем ингредиенты
        queryset = AbstractIngredient.objects.all().order_by('name')

        if search_filter:
            queryset = queryset.filter(name__icontains=search_filter)
            self.stdout.write(f"🔍 Фильтр: '{search_filter}'")

        if skip_empty:
            queryset = queryset.exclude(
                calories__isnull=True,
                protein__isnull=True,
                fat__isnull=True,
                carbohydrates__isnull=True
            )
            self.stdout.write("⏭️ Пропускаем ингредиенты без КБЖУ")

        total = queryset.count()
        if limit:
            queryset = queryset[:limit]
            total = limit

        self.stdout.write(f"📊 Найдено ингредиентов для экспорта: {total}")
        self.stdout.write(f"📸 Режим картинок: {image_mode}")

        if total == 0:
            self.stdout.write(self.style.WARNING("⚠️ Нет ингредиентов для экспорта"))
            return

        # ===== ЭКСПОРТ =====
        stats = {
            'total': total,
            'exported': 0,
            'errors': 0,
            'with_images': 0,
            'skipped': 0,
        }

        errors_list = []

        for ingredient in queryset.iterator():
            try:
                self._export_ingredient(
                    ingredient,
                    output_dir,
                    images_dir,
                    include_images,
                    image_mode,
                    verbose,
                    stats
                )
                stats['exported'] += 1

            except Exception as e:
                stats['errors'] += 1
                error_msg = f"❌ Ошибка при экспорте #{ingredient.id} '{ingredient.name}': {e}"
                errors_list.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))

            if stats['exported'] % 50 == 0 and stats['exported'] > 0:
                self.stdout.write(f"  📄 Экспортировано: {stats['exported']}/{stats['total']}")

        # ===== ИТОГ =====
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("📊 СТАТИСТИКА ЭКСПОРТА"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"  Всего ингредиентов:   {stats['total']}")
        self.stdout.write(f"  Экспортировано:       {stats['exported']}")
        self.stdout.write(f"  С изображениями:      {stats['with_images']}")
        self.stdout.write(f"  Пропущено:            {stats['skipped']}")
        self.stdout.write(f"  Ошибок:               {stats['errors']}")
        self.stdout.write("=" * 70)
        self.stdout.write(f"📁 Результат сохранен в: {output_dir}")

        if errors_list and verbose:
            self.stdout.write("\n" + self.style.WARNING("⚠️ ОШИБКИ:"))
            for error in errors_list[:10]:
                self.stdout.write(f"  {error}")
            if len(errors_list) > 10:
                self.stdout.write(f"  ... и еще {len(errors_list) - 10} ошибок")

        self.stdout.write(self.style.SUCCESS("\n✅ Экспорт завершен!"))

    def _export_ingredient(self, ingredient, output_dir, images_dir, include_images, image_mode, verbose, stats):
        """Экспорт одного ингредиента в JSON-файл"""

        # Сериализуем ингредиент
        data = self._serialize_ingredient(ingredient, include_images, image_mode, verbose)

        # ===== КОПИРОВАНИЕ КАРТИНКИ (режим copy) =====
        if include_images and image_mode == 'copy' and ingredient.image and ingredient.image.path:
            try:
                src_path = ingredient.image.path
                if os.path.exists(src_path):
                    # Генерируем имя файла
                    ext = os.path.splitext(src_path)[1]
                    safe_name = self._safe_filename(ingredient.name)
                    dst_name = f"{ingredient.id}_{safe_name}{ext}"
                    dst_path = os.path.join(images_dir, dst_name)

                    # Копируем файл
                    shutil.copy2(src_path, dst_path)

                    # Сохраняем путь в JSON
                    if data.get('image') and isinstance(data['image'], dict):
                        data['image']['path'] = os.path.join('images', dst_name)
                    else:
                        data['image'] = {
                            'name': os.path.basename(ingredient.image.name),
                            'path': os.path.join('images', dst_name),
                        }
                    stats['with_images'] += 1

                    if verbose:
                        self.stdout.write(f"  🖼️ Скопировано изображение для '{ingredient.name}'")

            except Exception as e:
                if verbose:
                    self.stdout.write(f"  ⚠️ Ошибка копирования изображения для '{ingredient.name}': {e}")
                if data.get('image') and isinstance(data['image'], dict):
                    data['image']['error'] = str(e)

        # Генерируем имя файла
        safe_name = self._safe_filename(ingredient.name)
        file_path = os.path.join(output_dir, f"{ingredient.id}_{safe_name}.json")

        # Сохраняем JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if verbose:
            self.stdout.write(f"  ✅ Экспортирован: {ingredient.name} (ID: {ingredient.id})")

    def _serialize_ingredient(self, ingredient, include_images=False, image_mode='path', verbose=False):
        """
        Сериализация ингредиента в словарь с ВСЕМИ простыми полями
        """
        data = {
            '_meta': {
                'id': ingredient.id,
                'export_date': datetime.now().isoformat(),
                'schema_version': '2.0',
                'model': 'kitchen.AbstractIngredient',
            }
        }

        # Получаем все поля модели
        for field in ingredient._meta.get_fields():
            # Пропускаем сложные связи
            if field.many_to_many or field.one_to_many or field.auto_created:
                continue

            # Пропускаем поле semantic_tags (обрабатываем отдельно)
            if field.name == 'semantic_tags':
                continue

            field_name = field.name
            value = getattr(ingredient, field_name, None)

            # Обработка разных типов
            if isinstance(value, models.Model):
                # ForeignKey - сохраняем ID и название
                data[field_name] = {
                    'id': value.id,
                    'name': str(value)
                }
            elif isinstance(value, datetime):
                data[field_name] = value.isoformat()
            elif isinstance(value, date):
                data[field_name] = value.isoformat()
            elif isinstance(value, (int, float, str, bool, list, dict)):
                data[field_name] = value
            elif value is None:
                data[field_name] = None
            else:
                data[field_name] = str(value)

        # === ОБРАБОТКА ОСОБЫХ СЛУЧАЕВ ===

        # category — упрощаем до названия
        if ingredient.category:
            data['category_name'] = ingredient.category.name
            data['category_id'] = ingredient.category.id

        # semantic_tags — как список названий
        if ingredient.semantic_tags.exists():
            data['tags'] = list(ingredient.semantic_tags.values_list('name', flat=True))
            data['tags_full'] = [
                {
                    'id': tag.id,
                    'name': tag.name,
                    'slug': tag.slug,
                    'tag_type': tag.tag_type,
                }
                for tag in ingredient.semantic_tags.all()
            ]
        else:
            data['tags'] = []
            data['tags_full'] = []

        # semantic_data — упрощаем
        data['semantic_data'] = ingredient.semantic_data or {}

        # ===== ОБРАБОТКА КАРТИНКИ =====
        if include_images and ingredient.image:
            try:
                if image_mode == 'path':
                    # Только пути
                    data['image'] = {
                        'url': ingredient.image.url if hasattr(ingredient.image, 'url') else None,
                        'path': ingredient.image.path if hasattr(ingredient.image, 'path') else None,
                        'name': os.path.basename(ingredient.image.name) if ingredient.image.name else None,
                    }

                elif image_mode == 'copy':
                    # Копирование файла (путь будет заполнен позже)
                    data['image'] = {
                        'name': os.path.basename(ingredient.image.name) if ingredient.image.name else None,
                        'path': None,  # Заполнится при копировании
                    }

                elif image_mode == 'base64':
                    # Встраивание в JSON
                    try:
                        if ingredient.image.path and os.path.exists(ingredient.image.path):
                            with open(ingredient.image.path, 'rb') as f:
                                image_data = f.read()
                                data['image'] = {
                                    'name': os.path.basename(ingredient.image.name) if ingredient.image.name else None,
                                    'base64': base64.b64encode(image_data).decode('utf-8'),
                                    'size': len(image_data),
                                }
                        else:
                            data['image'] = None
                            if verbose:
                                self.stdout.write(f"  ⚠️ Файл картинки не найден: {ingredient.image.path}")
                    except Exception as e:
                        if verbose:
                            self.stdout.write(f"  ⚠️ Ошибка конвертации картинки для {ingredient.name}: {e}")
                        data['image'] = None
            except Exception as e:
                if verbose:
                    self.stdout.write(f"  ⚠️ Ошибка обработки картинки для {ingredient.name}: {e}")
                data['image'] = None
        else:
            data['image'] = None

        # Для обратной совместимости оставляем старые поля
        if data.get('image') and isinstance(data['image'], dict):
            data['image_url'] = data['image'].get('url')
            data['image_name'] = data['image'].get('name')
        else:
            data['image_url'] = None
            data['image_name'] = None

        return data

    def _safe_filename(self, name):
        """Генерирует безопасное имя файла"""
        slug = slugify(name)
        slug = re.sub(r'[^a-zA-Z0-9\-]', '', slug)
        slug = slug[:100]
        return slug or 'unnamed'


# ==================== ФУНКЦИЯ ДЛЯ ИСПОЛЬЗОВАНИЯ В SHELL ====================

def export_ingredient_to_json(ingredient, output_dir='exported_ingredients', include_images=False, image_mode='path'):
    """
    Экспорт одного ингредиента в JSON (для использования в shell)

    Пример:
        from kitchen.management.commands.export_ingredients_to_json import export_ingredient_to_json
        ingredient = AbstractIngredient.objects.get(id=110)
        export_ingredient_to_json(ingredient, include_images=True, image_mode='copy')
    """
    import os
    import json
    from datetime import datetime

    os.makedirs(output_dir, exist_ok=True)

    # Создаем экземпляр команды
    cmd = Command()

    # Сериализуем
    data = cmd._serialize_ingredient(ingredient, include_images, image_mode)

    # Копируем картинку если нужно
    if include_images and image_mode == 'copy' and ingredient.image:
        images_dir = os.path.join(output_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)

        try:
            src_path = ingredient.image.path
            if os.path.exists(src_path):
                ext = os.path.splitext(src_path)[1]
                safe_name = cmd._safe_filename(ingredient.name)
                dst_name = f"{ingredient.id}_{safe_name}{ext}"
                dst_path = os.path.join(images_dir, dst_name)

                shutil.copy2(src_path, dst_path)
                data['image']['path'] = os.path.join('images', dst_name)
        except Exception as e:
            print(f"⚠️ Ошибка копирования картинки: {e}")

    # Сохраняем JSON
    safe_name = cmd._safe_filename(ingredient.name)
    file_path = os.path.join(output_dir, f"{ingredient.id}_{safe_name}.json")

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return file_path