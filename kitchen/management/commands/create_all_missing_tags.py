# kitchen/management/commands/create_all_missing_tags.py
from django.core.management.base import BaseCommand
from kitchen.models import SemanticTag


class Command(BaseCommand):
    help = 'Создает все недостающие семантические теги'

    def handle(self, *args, **options):
        missing_tags = [
            "Батон", "Тыква", "Бекон", "Хлеб", "Вода",
            "Молоко", "Сыр", "Масло", "Мука", "Бобовые",
            "Рис", "Овощи", "Фрукты", "Зелень", "Пряность",
            "Специя", "Соус", "Кетчуп", "Майонез", "Уксус",
            "Соль", "Сахар", "Мед", "Шоколад", "Печенье",
            "Вафли", "Торт", "Мороженое", "Напиток", "Сок",
            "Чай", "Кофе", "Какао", "Алкоголь", "Пиво",
            "Вино", "Водка", "Коньяк", "Виски", "Джин",
            "Ром", "Ликер", "Сироп", "Джем", "Варенье",
            "Конфитюр", "Пастила", "Зефир", "Мармелад",
            "Драже", "Карамель", "Конфеты", "Халва",
            "Козинак", "Орехи", "Семена", "Квас", "Лимонад",
            "Кола", "Энергетик", "Замороженный", "Грибы",
            "Морепродукты", "Субпродукты", "Колбаса",
            "Сосиски", "Ветчина", "Паштет", "Консервы",
            "Рыба", "Птица", "Говядина", "Свинина",
        ]

        created_count = 0
        existing_count = 0

        for tag_name in missing_tags:
            tag, created = SemanticTag.objects.get_or_create(
                name=tag_name,
                defaults={
                    'tag_type': 'property',
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Создан тег: {tag_name}'))
            else:
                existing_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✨ Готово! Создано: {created_count}, уже существовало: {existing_count}'
        ))