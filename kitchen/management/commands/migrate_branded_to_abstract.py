# kitchen/management/commands/migrate_branded_to_abstract.py

from django.core.management.base import BaseCommand
from django.db import transaction
from kitchen.models import AbstractIngredient, BrandedIngredient, Ingredient
import re


class Command(BaseCommand):
    help = 'Переносит брендовые продукты из AbstractIngredient в BrandedIngredient'

    BRANDS = [
        'Пятерочка', 'KFC', 'Ростикc', 'Макдональдс', 'Burger King',
        'Перекресток', 'Ашан', 'METRO', 'Окей', 'Лента', 'Магнит',
    ]

    # Маппинг для поиска подходящего AbstractIngredient
    KEYWORD_MAPPING = {
        'стрипс': 'Курица',  # 2 Стрипса Острые → Курица
        'банан': 'Банан',  # Choco Banana → Банан
        'смузи': 'Смузи',  # Easy Смузи → Смузи
        'энергетик': 'Энергетический напиток',  # Energy To Go → Энергетический напиток
        'вишня': 'Вишня',  # Cherry Fresh → Вишня
        'лимонад': 'Лимонад',
        'мокка': 'Кофе',  # топпинг мокка-карамель → Кофе
        'шоколад': 'Шоколад',
        'пончик': 'Пончик',
        'сок': 'Сок',
        'вода': 'Вода',
        'молоко': 'Молоко',
        'йогурт': 'Йогурт',
        'творог': 'Творог',
        'сыр': 'Сыр',
        'колбаса': 'Колбаса',
        'мясо': 'Мясо',
        'рыба': 'Рыба',
        'хлеб': 'Хлеб',
        'булка': 'Булка',
        'торт': 'Торт',
        'пирожное': 'Пирожное',
        'печенье': 'Печенье',
        'вафли': 'Вафли',
        'кекс': 'Кекс',
        'маффин': 'Маффин',
        'круассан': 'Круассан',
    }

    def find_abstract_ingredient(self, product_name):
        """Находит подходящий AbstractIngredient для продукта"""
        # Приводим к нижнему регистру для поиска
        name_lower = product_name.lower()

        # Ищем по ключевым словам
        for keyword, abstract_name in self.KEYWORD_MAPPING.items():
            if keyword in name_lower:
                # Ищем AbstractIngredient с таким именем
                abstract = AbstractIngredient.objects.filter(
                    name__icontains=abstract_name
                ).exclude(
                    name__icontains='Пятерочка'
                ).exclude(
                    name__icontains='KFC'
                ).first()

                if abstract:
                    self.stdout.write(f'   🔍 Найден AbstractIngredient: {abstract.name} (по ключу: {keyword})')
                    return abstract

        # Если не нашли по ключевым словам - ищем по первому слову
        first_word = product_name.split()[0] if product_name.split() else ''
        if first_word:
            # Ищем AbstractIngredient, начинающийся с этого слова
            abstract = AbstractIngredient.objects.filter(
                name__istartswith=first_word
            ).exclude(
                name__icontains='Пятерочка'
            ).exclude(
                name__icontains='KFC'
            ).first()

            if abstract:
                self.stdout.write(f'   🔍 Найден AbstractIngredient: {abstract.name} (по первому слову)')
                return abstract

        # Если ничего не нашли - возвращаем None
        self.stdout.write(f'   ⚠️ Не найден AbstractIngredient для: {product_name}')
        return None

    def handle(self, *args, **options):
        self.stdout.write('🚀 ПЕРЕНОС БРЕНДОВЫХ ПРОДУКТОВ В BRANDEDINGREDIENT')
        self.stdout.write('=' * 60)

        # Находим все брендовые продукты
        q = None
        for brand in self.BRANDS:
            if q is None:
                q = AbstractIngredient.objects.filter(name__icontains=brand)
            else:
                q = q | AbstractIngredient.objects.filter(name__icontains=brand)

        branded_abstracts = q.distinct() if q else AbstractIngredient.objects.none()
        total = branded_abstracts.count()

        self.stdout.write(f'📊 Найдено брендовых продуктов: {total}')

        # Показываем примеры
        self.stdout.write('\n📋 ПРИМЕРЫ:')
        for abstract in branded_abstracts[:10]:
            self.stdout.write(f'  - {abstract.name}')
        if total > 10:
            self.stdout.write(f'  ... и еще {total - 10}')

        confirm = input(f'\n🔄 Перенести {total} продуктов? (y/n): ')
        if confirm.lower() != 'y':
            self.stdout.write(self.style.WARNING('❌ Операция отменена'))
            return

        with transaction.atomic():
            processed = 0
            errors = 0
            no_abstract = []
            found_abstract = []

            for abstract in branded_abstracts:
                try:
                    self.stdout.write(f'\n📦 {abstract.name}')

                    # Находим бренд
                    brand = None
                    for b in self.BRANDS:
                        if b in abstract.name:
                            brand = b
                            break

                    if not brand:
                        brand = 'Неизвестный бренд'

                    # Находим подходящий AbstractIngredient
                    base_abstract = self.find_abstract_ingredient(abstract.name)

                    if base_abstract is None:
                        no_abstract.append(abstract.name)
                        self.stdout.write(f'   ⚠️ ПРОПУСКАЕМ: не найден AbstractIngredient')
                        continue

                    found_abstract.append((abstract.name, base_abstract.name))

                    # Создаем BrandedIngredient
                    branded, created = BrandedIngredient.objects.get_or_create(
                        abstract=base_abstract,
                        brand=brand,
                        product_name=abstract.name,
                        defaults={
                            'calories': abstract.calories,
                            'protein': abstract.protein,
                            'fat': abstract.fat,
                            'carbohydrates': abstract.carbohydrates,
                        }
                    )

                    if created:
                        self.stdout.write(f'   ✅ Создан BrandedIngredient')
                    else:
                        self.stdout.write(f'   🔄 Обновлен существующий BrandedIngredient')

                    # Обновляем Ingredient
                    ingredients = Ingredient.objects.filter(abstract=abstract)
                    for ing in ingredients:
                        ing.abstract = base_abstract
                        ing.branded = branded
                        ing.save()

                    # Удаляем старый AbstractIngredient
                    abstract.delete()
                    processed += 1

                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))

            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS(f'✅ Перенесено: {processed}'))
            self.stdout.write(self.style.ERROR(f'❌ Ошибок: {errors}'))
            self.stdout.write(f'⚠️ Пропущено (нет AbstractIngredient): {len(no_abstract)}')

            if no_abstract:
                self.stdout.write('\n📋 СПИСОК ПРОПУЩЕННЫХ:')
                for name in no_abstract[:20]:
                    self.stdout.write(f'  - {name}')
                if len(no_abstract) > 20:
                    self.stdout.write(f'  ... и еще {len(no_abstract) - 20}')

        # Финальная статистика
        self.stdout.write('\n📊 СТАТИСТИКА:')
        self.stdout.write(f'  AbstractIngredient: {AbstractIngredient.objects.count()}')
        self.stdout.write(f'  BrandedIngredient: {BrandedIngredient.objects.count()}')