# kitchen/management/commands/create_missing_tags.py
from django.core.management.base import BaseCommand
from kitchen.models import SemanticTag


class Command(BaseCommand):
    help = 'Создает недостающие семантические теги'

    def handle(self, *args, **options):
        missing_tags = [
            "Соус для гриля",
            "Салат",
            "Макароны",
            "Цитрус",
            "Арбуз",
            "Банан",
            "Баранина",
            "Мясной полуфабрикат",
            "Рыба копченая",
            "Капуста",
            "Крупа",
            "Ягода",
            "Перец",
            "Томат",
            "Лук",
            "Груша",
            "Яблоко",
            "Консервы",
            "Говядина",
            "Свинина",
            "Птица",
            "Рыба",
            "Морепродукты",
            "Молоко",
            "Сыр",
            "Масло",
            "Хлеб",
            "Мука",
            "Крупы",
            "Бобовые",
            "Овощи",
            "Фрукты",
            "Зелень",
            "Пряности",
            "Специи",
            "Соус",
            "Кетчуп",
            "Майонез",
            "Горчица",
            "Уксус",
            "Соль",
            "Сахар",
            "Мед",
            "Шоколад",
            "Печенье",
            "Вафли",
            "Торт",
            "Мороженое",
            "Напиток",
            "Сок",
            "Чай",
            "Кофе",
            "Какао",
            "Алкоголь",
            "Пиво",
            "Вино",
            "Водка",
            "Коньяк",
            "Виски",
            "Джин",
            "Ром",
            "Ликер",
            "Сироп",
            "Джем",
            "Варенье",
            "Конфитюр",
            "Пастила",
            "Зефир",
            "Мармелад",
            "Драже",
            "Карамель",
            "Конфеты",
            "Халва",
            "Козинак",
            "Орехи",
            "Семена",
            "Чай",
            "Кофе",
            "Какао",
            "Квас",
            "Лимонад",
            "Кола",
            "Энергетик",
            "Вода",
            "Соки",
            "Мясо",
            "Рыба",
            "Морепродукты",
            "Субпродукты",
            "Колбаса",
            "Сосиски",
            "Ветчина",
            "Бекон",
            "Паштет",
            "Консервы",
            "Замороженные продукты",
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
                self.stdout.write(self.style.WARNING(f'⏩ Уже существует: {tag_name}'))

        self.stdout.write(self.style.SUCCESS(
            f'\n✨ Готово! Создано: {created_count}, уже существовало: {existing_count}'
        ))