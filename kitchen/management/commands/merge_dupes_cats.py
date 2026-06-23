# kitchen/management/commands/merge_dupes_cats.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from kitchen.models import IngredientCategory, AbstractIngredient, SemanticRelation


class Command(BaseCommand):
    help = 'Объединяет дублирующиеся категории'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Поиск дублирующихся категорий...')

        # Находим все дубликаты
        duplicates = IngredientCategory.objects.values('name').annotate(
            count=models.Count('id')
        ).filter(count__gt=1).order_by('-count')

        total_duplicates = duplicates.count()
        self.stdout.write(f'📊 Найдено {total_duplicates} дублирующихся названий')

        if total_duplicates == 0:
            self.stdout.write(self.style.SUCCESS('✅ Дубликатов нет!'))
            return

        for dup in duplicates:
            name = dup['name']
            categories = IngredientCategory.objects.filter(name=name).order_by('id')

            main_category = categories.first()
            duplicate_categories = categories.exclude(id=main_category.id)

            self.stdout.write(f'\n📦 Обработка: "{name}"')
            self.stdout.write(f'   Основная: ID {main_category.id}')
            self.stdout.write(f'   Дубли: {[c.id for c in duplicate_categories]}')

            with transaction.atomic():
                # 1. Переназначаем AbstractIngredient
                for dup_cat in duplicate_categories:
                    count = AbstractIngredient.objects.filter(category=dup_cat).update(category=main_category)
                    if count:
                        self.stdout.write(f'   ✅ Перемещено {count} абстрактных ингредиентов из {dup_cat.id}')

                # 2. Переназначаем SemanticRelation (from_category) с проверкой на дубликаты
                for dup_cat in duplicate_categories:
                    # Находим все связи, которые нужно перенести
                    relations = SemanticRelation.objects.filter(from_category=dup_cat)
                    for rel in relations:
                        # Проверяем, существует ли уже такая связь
                        existing = SemanticRelation.objects.filter(
                            from_category=main_category,
                            to_category=rel.to_category,
                            relation_type=rel.relation_type
                        ).first()

                        if existing:
                            # Если существует — удаляем дублирующуюся
                            rel.delete()
                            self.stdout.write(
                                f'   🗑️ Удалена дублирующаяся связь из {dup_cat.id} → {rel.to_category.id}')
                        else:
                            # Если нет — переносим
                            rel.from_category = main_category
                            rel.save()
                            self.stdout.write(f'   ✅ Перемещена связь из {dup_cat.id} → {main_category.id}')

                # 3. Переназначаем SemanticRelation (to_category)
                for dup_cat in duplicate_categories:
                    relations = SemanticRelation.objects.filter(to_category=dup_cat)
                    for rel in relations:
                        existing = SemanticRelation.objects.filter(
                            from_category=rel.from_category,
                            to_category=main_category,
                            relation_type=rel.relation_type
                        ).first()

                        if existing:
                            rel.delete()
                            self.stdout.write(
                                f'   🗑️ Удалена дублирующаяся связь {rel.from_category.id} → {dup_cat.id}')
                        else:
                            rel.to_category = main_category
                            rel.save()
                            self.stdout.write(f'   ✅ Перемещена связь {rel.from_category.id} → {main_category.id}')

                # 4. Удаляем дубликаты
                for dup_cat in duplicate_categories:
                    dup_cat.delete()
                    self.stdout.write(f'   🗑️ Удалена категория {dup_cat.id}')

            self.stdout.write(self.style.SUCCESS(f'   ✅ Категория "{name}" объединена'))

        self.stdout.write(self.style.SUCCESS('\n🎉 ВСЕ ДУБЛИКАТЫ ОБЪЕДИНЕНЫ!'))

        remaining = IngredientCategory.objects.count()
        self.stdout.write(f'📊 Всего категорий после объединения: {remaining}')