# kitchen/management/commands/delete_remaining_branded.py

from django.core.management.base import BaseCommand
from django.db import transaction
from kitchen.models import AbstractIngredient, Ingredient, BrandedIngredient


class Command(BaseCommand):
    help = 'Удаляет оставшиеся брендовые продукты из AbstractIngredient'

    BRANDS = ['Пятерочка', 'KFC', 'Ростикc']

    def handle(self, *args, **options):
        self.stdout.write('🗑️ УДАЛЕНИЕ ОСТАВШИХСЯ БРЕНДОВЫХ ПРОДУКТОВ')
        self.stdout.write('=' * 60)

        # Находим оставшиеся брендовые продукты
        q = None
        for brand in self.BRANDS:
            if q is None:
                q = AbstractIngredient.objects.filter(name__icontains=brand)
            else:
                q = q | AbstractIngredient.objects.filter(name__icontains=brand)

        to_delete = q.distinct() if q else AbstractIngredient.objects.none()
        total = to_delete.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Нет брендовых продуктов для удаления!'))
            return

        self.stdout.write(f'📊 Найдено для удаления: {total}')

        # Показываем примеры
        self.stdout.write('\n📋 БУДУТ УДАЛЕНЫ:')
        for item in to_delete[:20]:
            self.stdout.write(f'  - {item.name}')
        if total > 20:
            self.stdout.write(f'  ... и еще {total - 20}')

        confirm = input(f'\n🗑️ УДАЛИТЬ {total} продуктов? (y/n): ')
        if confirm.lower() != 'y':
            self.stdout.write(self.style.WARNING('❌ Операция отменена'))
            return

        with transaction.atomic():
            deleted_abstracts = 0
            deleted_ingredients = 0
            deleted_branded = 0

            for abstract in to_delete:
                try:
                    # 1. Удаляем связанные Ingredient
                    ingredients = Ingredient.objects.filter(abstract=abstract)
                    ing_count = ingredients.count()
                    if ing_count > 0:
                        ingredients.delete()
                        deleted_ingredients += ing_count
                        self.stdout.write(f'  🗑️ Удалено Ingredient: {ing_count} для {abstract.name}')

                    # 2. Удаляем связанные BrandedIngredient (если есть)
                    branded = BrandedIngredient.objects.filter(abstract=abstract)
                    branded_count = branded.count()
                    if branded_count > 0:
                        branded.delete()
                        deleted_branded += branded_count
                        self.stdout.write(f'  🗑️ Удалено BrandedIngredient: {branded_count} для {abstract.name}')

                    # 3. Удаляем сам AbstractIngredient
                    abstract.delete()
                    deleted_abstracts += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Ошибка при удалении {abstract.name}: {e}'))

            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS('✅ УДАЛЕНИЕ ЗАВЕРШЕНО:'))
            self.stdout.write(f'  🗑️ Удалено AbstractIngredient: {deleted_abstracts}')
            self.stdout.write(f'  🗑️ Удалено Ingredient: {deleted_ingredients}')
            self.stdout.write(f'  🗑️ Удалено BrandedIngredient: {deleted_branded}')

        # Финальная статистика
        self.stdout.write('\n📊 ИТОГОВАЯ СТАТИСТИКА:')
        self.stdout.write(f'  AbstractIngredient: {AbstractIngredient.objects.count()}')
        self.stdout.write(f'  Ingredient: {Ingredient.objects.count()}')
        self.stdout.write(f'  BrandedIngredient: {BrandedIngredient.objects.count()}')