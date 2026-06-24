# kitchen/management/commands/auto_create_nutrient_relations.py

from django.core.management.base import BaseCommand
from django.db.models import Avg
from kitchen.models import (
    AbstractIngredient, IngredientCategory,
    SemanticTag, RelationType, SemanticRelation
)

# Нутриенты, для которых будем создавать связи
NUTRIENT_MAPPING = {
    # Энергия
    'calories': {'name': 'Калорийность', 'icon': '🔥', 'tag_type': 'nutrient'},
    # Макронутриенты
    'protein': {'name': 'Белок', 'icon': '💪', 'tag_type': 'nutrient'},
    'fat': {'name': 'Жиры', 'icon': '🧈', 'tag_type': 'nutrient'},
    'carbohydrates': {'name': 'Углеводы', 'icon': '🍞', 'tag_type': 'nutrient'},
    'fiber': {'name': 'Клетчатка', 'icon': '🌾', 'tag_type': 'nutrient'},
    # Минералы
    'calcium': {'name': 'Кальций', 'icon': '🦴', 'tag_type': 'mineral'},
    'iron': {'name': 'Железо', 'icon': '🩸', 'tag_type': 'mineral'},
    'magnesium': {'name': 'Магний', 'icon': '⚡', 'tag_type': 'mineral'},
    'potassium': {'name': 'Калий', 'icon': '🍌', 'tag_type': 'mineral'},
    'sodium': {'name': 'Натрий', 'icon': '🧂', 'tag_type': 'mineral'},
    'zinc': {'name': 'Цинк', 'icon': '🔋', 'tag_type': 'mineral'},
    'phosphorus': {'name': 'Фосфор', 'icon': '🦷', 'tag_type': 'mineral'},
    'copper': {'name': 'Медь', 'icon': '🔶', 'tag_type': 'mineral'},
    'manganese': {'name': 'Марганец', 'icon': '🔷', 'tag_type': 'mineral'},
    'selenium': {'name': 'Селен', 'icon': '🧬', 'tag_type': 'mineral'},
    # Витамины
    'vitamin_a': {'name': 'Витамин A', 'icon': '👁️', 'tag_type': 'vitamin'},
    'beta_carotene': {'name': 'Бета-каротин', 'icon': '🥕', 'tag_type': 'vitamin'},
    'vitamin_b1': {'name': 'Витамин B1 (тиамин)', 'icon': '⚡', 'tag_type': 'vitamin'},
    'vitamin_b2': {'name': 'Витамин B2 (рибофлавин)', 'icon': '⚡', 'tag_type': 'vitamin'},
    'vitamin_b3': {'name': 'Витамин B3 (ниацин)', 'icon': '⚡', 'tag_type': 'vitamin'},
    'vitamin_b4': {'name': 'Витамин B4 (холин)', 'icon': '🧠', 'tag_type': 'vitamin'},
    'vitamin_b5': {'name': 'Витамин B5 (пантотеновая)', 'icon': '⚡', 'tag_type': 'vitamin'},
    'vitamin_b6': {'name': 'Витамин B6', 'icon': '⚡', 'tag_type': 'vitamin'},
    'vitamin_b7': {'name': 'Витамин B7 (биотин)', 'icon': '💇', 'tag_type': 'vitamin'},
    'vitamin_b9_folate': {'name': 'Витамин B9 (фолаты)', 'icon': '🤰', 'tag_type': 'vitamin'},
    'vitamin_b12': {'name': 'Витамин B12', 'icon': '💉', 'tag_type': 'vitamin'},
    'vitamin_c': {'name': 'Витамин C', 'icon': '🍊', 'tag_type': 'vitamin'},
    'vitamin_d': {'name': 'Витамин D', 'icon': '☀️', 'tag_type': 'vitamin'},
    'vitamin_e': {'name': 'Витамин E', 'icon': '✨', 'tag_type': 'vitamin'},
    'vitamin_k': {'name': 'Витамин K', 'icon': '🩸', 'tag_type': 'vitamin'},
    # Жиры
    'cholesterol': {'name': 'Холестерин', 'icon': '❤️', 'tag_type': 'nutrient'},
    'omega_3': {'name': 'Омега-3', 'icon': '🐟', 'tag_type': 'nutrient'},
    'omega_6': {'name': 'Омега-6', 'icon': '🌻', 'tag_type': 'nutrient'},
    'saturated_fat': {'name': 'Насыщенные жиры', 'icon': '🧈', 'tag_type': 'nutrient'},
    'trans_fat': {'name': 'Трансжиры', 'icon': '🚫', 'tag_type': 'nutrient'},
}


class Command(BaseCommand):
    help = 'Автоматически создает семантические связи "богат" и "источник" на основе КБЖУ'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write('🧠 АВТОМАТИЧЕСКОЕ СОЗДАНИЕ СЕМАНТИЧЕСКИХ СВЯЗЕЙ')
        self.stdout.write('=' * 70)

        # Получаем существующие типы связей
        try:
            rich_in = RelationType.objects.get(name='богат')
        except RelationType.DoesNotExist:
            self.stdout.write('❌ Тип связи "богат" не найден!')
            return

        try:
            source_of = RelationType.objects.get(name='источник')
        except RelationType.DoesNotExist:
            self.stdout.write('❌ Тип связи "источник" не найден!')
            return

        stats = {'rich': 0, 'source': 0, 'skipped': 0, 'errors': 0}

        for field, info in NUTRIENT_MAPPING.items():
            nutrient_name = info['name']
            tag_type = info.get('tag_type', 'nutrient')
            icon = info.get('icon', '')

            self.stdout.write(f'\n📊 Обработка: {nutrient_name}')

            # Создаём SemanticTag
            tag, created = SemanticTag.objects.get_or_create(
                name=nutrient_name,
                defaults={
                    'tag_type': tag_type,
                    'icon': icon,
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'  🏷️ Создан тег: {nutrient_name}')

            # Находим ингредиенты с этим нутриентом
            ingredients = AbstractIngredient.objects.filter(
                **{f"{field}__isnull": False}
            ).exclude(**{f"{field}": 0})

            if not ingredients.exists():
                self.stdout.write(f'  ⚠️ Нет ингредиентов с {nutrient_name}')
                continue

            # Считаем среднее
            values = list(ingredients.values_list(field, flat=True))
            avg_value = sum(values) / len(values) if values else 0
            values_sorted = sorted(values)
            percentile_90 = values_sorted[int(len(values_sorted) * 0.9)] if values_sorted else 0

            threshold = max(avg_value * 2, percentile_90 * 0.8)
            top_ingredients = ingredients.filter(
                **{f"{field}__gte": threshold}
            ).order_by(f'-{field}')[:10]

            if not top_ingredients:
                top_ingredients = ingredients.order_by(f'-{field}')[:5]

            self.stdout.write(f'  Найдено лидеров: {top_ingredients.count()}')

            for ing in top_ingredients:
                value = getattr(ing, field)
                try:
                    if not ing.category:
                        continue

                    # Связь "богат"
                    if not SemanticRelation.objects.filter(
                            from_category=ing.category,
                            to_tag=tag,
                            relation_type=rich_in
                    ).exists():
                        SemanticRelation.objects.create(
                            from_category=ing.category,
                            to_tag=tag,
                            relation_type=rich_in,
                            weight=round(value / avg_value, 2) if avg_value > 0 else 1.0,
                            notes=f'Содержит {value:.2f} (в {round(value / avg_value, 1)}x выше среднего)'
                        )
                        stats['rich'] += 1
                        self.stdout.write(f'    ✅ {ing.category.name} → {nutrient_name} (богат)')
                    else:
                        stats['skipped'] += 1

                    # Связь "источник" (только если значительно выше среднего)
                    if value > avg_value * 1.5 and not SemanticRelation.objects.filter(
                            from_category=ing.category,
                            to_tag=tag,
                            relation_type=source_of
                    ).exists():
                        SemanticRelation.objects.create(
                            from_category=ing.category,
                            to_tag=tag,
                            relation_type=source_of,
                            weight=round(value / avg_value, 2) if avg_value > 0 else 1.0,
                            notes=f'Хороший источник: {value:.2f}'
                        )
                        stats['source'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    self.stdout.write(f'    ❌ Ошибка: {e}')

        # Итог
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('📊 СТАТИСТИКА')
        self.stdout.write('=' * 70)
        self.stdout.write(f'  Создано связей "богат": {stats["rich"]}')
        self.stdout.write(f'  Создано связей "источник": {stats["source"]}')
        self.stdout.write(f'  Пропущено (уже есть): {stats["skipped"]}')
        self.stdout.write(f'  Ошибок: {stats["errors"]}')
        self.stdout.write('=' * 70)