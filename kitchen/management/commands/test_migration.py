# kitchen/management/commands/test_migration.py

from django.core.management.base import BaseCommand
from kitchen.models import AbstractIngredient, BrandedIngredient, Ingredient


class Command(BaseCommand):
    help = 'Тестирует перенос брендовых продуктов из AbstractIngredient'

    def handle(self, *args, **options):
        BRANDS = ['Пятерочка', 'KFC', 'Ростикc', 'Макдональдс', 'Burger King']

        # Находим брендовые продукты
        q = None
        for brand in BRANDS:
            if q is None:
                q = AbstractIngredient.objects.filter(name__icontains=brand)
            else:
                q = q | AbstractIngredient.objects.filter(name__icontains=brand)

        branded_abstracts = q.distinct() if q else AbstractIngredient.objects.none()
        total = branded_abstracts.count()

        self.stdout.write(f'📊 Найдено брендовых продуктов: {total}')

        # Берем первые 5 для теста
        test_abstracts = branded_abstracts[:5]
        self.stdout.write(f'🧪 Тестируем на {len(test_abstracts)} продуктах...')
        self.stdout.write('-' * 60)

        for abstract in test_abstracts:
            self.stdout.write(f'\n📋 Обработка: {abstract.name}')
            self.stdout.write(f'   Категория: {abstract.category}')
            self.stdout.write(
                f'   КБЖУ: {abstract.calories}, {abstract.protein}, {abstract.fat}, {abstract.carbohydrates}')

            # Определяем бренд
            brand = None
            for b in BRANDS:
                if b in abstract.name:
                    brand = b
                    break

            # Извлекаем базовое имя
            base_name = abstract.name
            for b in BRANDS:
                base_name = base_name.replace(b, '').strip()
            base_name = base_name.replace('--', '').strip()
            base_name = base_name.replace('-', '').strip()

            self.stdout.write(f'   Бренд: {brand}')
            self.stdout.write(f'   Базовое имя: {base_name}')

            # Проверяем, есть ли уже такой базовый ингредиент
            existing = AbstractIngredient.objects.filter(name__iexact=base_name).first()
            if existing:
                self.stdout.write(f'   ⚠️ Базовый ингредиент уже существует: {existing.name}')
            else:
                self.stdout.write(f'   ✅ Базовый ингредиент будет создан')

            # Проверяем Ingredient
            ingredients = Ingredient.objects.filter(abstract=abstract)
            self.stdout.write(f'   📦 Ingredient: {ingredients.count()}')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Тест завершен. Проверьте результат.'))