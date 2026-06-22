# kitchen/management/commands/delete_garbage_abstracts.py

from django.core.management.base import BaseCommand
from django.db import transaction
from kitchen.models import AbstractIngredient, Ingredient, BrandedIngredient, HomeIngredient


class Command(BaseCommand):
    help = 'Удаляет мусорные записи из AbstractIngredient'

    # Список мусорных ключевых слов
    GARBAGE_KEYWORDS = [
        'Ашан', 'Яшкино', 'Nature', 'Chocolate',
        'Прованские', 'Солодом', 'АнанасАпельсин',
        'Бисквитное Печенье', 'Заварной Хлеб',
        'Салат АнанасАпельсин', 'Молочный Шоколад с Карамелизованным',
        'Рулет Абрикосовый', 'Багет 8 Злаков',
        'Блинчики с Творогом', 'Слойка Дрожжевая',
        'Пончик Ашан', 'Мягкий Сыр',
    ]

    def handle(self, *args, **options):
        self.stdout.write('🗑️ УДАЛЕНИЕ МУСОРНЫХ ЗАПИСЕЙ ИЗ ABSTRACTINGREDIENT')
        self.stdout.write('=' * 60)

        # Находим все мусорные записи
        q = None
        for keyword in self.GARBAGE_KEYWORDS:
            if q is None:
                q = AbstractIngredient.objects.filter(name__icontains=keyword)
            else:
                q = q | AbstractIngredient.objects.filter(name__icontains=keyword)

        garbage = q.distinct() if q else AbstractIngredient.objects.none()
        total = garbage.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Мусор не найден!'))
            return

        self.stdout.write(f'📊 Найдено мусорных записей: {total}')
        self.stdout.write('\n📋 СПИСОК МУСОРА:')
        for item in garbage:
            # Проверяем, используется ли в рецептах
            is_used = HomeIngredient.objects.filter(
                ingredient__abstract=item
            ).exists()

            if is_used:
                status = '⚠️ ИСПОЛЬЗУЕТСЯ В РЕЦЕПТАХ!'
            else:
                status = '🗑️ не используется'

            self.stdout.write(f'  {status}: {item.name}')

        confirm = input(f'\n🗑️ УДАЛИТЬ {total} записей? (y/n): ')
        if confirm.lower() != 'y':
            self.stdout.write(self.style.WARNING('❌ Операция отменена'))
            return

        with transaction.atomic():
            deleted_abstracts = 0
            deleted_ingredients = 0
            deleted_branded = 0

            for abstract in garbage:
                try:
                    # Проверяем, используется ли в рецептах
                    is_used = HomeIngredient.objects.filter(
                        ingredient__abstract=abstract
                    ).exists()

                    if is_used:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ ПРОПУСКАЕМ: {abstract.name} (используется в рецептах)'))
                        continue

                    # 1. Удаляем связанные Ingredient
                    ingredients = Ingredient.objects.filter(abstract=abstract)
                    ing_count = ingredients.count()
                    if ing_count > 0:
                        ingredients.delete()
                        deleted_ingredients += ing_count

                    # 2. Удаляем связанные BrandedIngredient
                    branded = BrandedIngredient.objects.filter(abstract=abstract)
                    branded_count = branded.count()
                    if branded_count > 0:
                        branded.delete()
                        deleted_branded += branded_count

                    # 3. Удаляем сам AbstractIngredient
                    abstract.delete()
                    deleted_abstracts += 1
                    self.stdout.write(f'  🗑️ {abstract.name} - удален')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Ошибка {abstract.name}: {e}'))

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


