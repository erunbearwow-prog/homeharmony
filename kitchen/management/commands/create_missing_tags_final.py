# kitchen/management/commands/create_missing_tags_final.py
from django.core.management.base import BaseCommand
from kitchen.models import SemanticTag


class Command(BaseCommand):
    help = 'Создает недостающие семантические теги'

    def handle(self, *args, **options):
        missing_tags = [
            "Колбасные изделия",
            "Деликатесы",
            "Мясной деликатес",
            "Выпечка",
            "Дип",
            "Корнеплоды",
            "Дичь",
            "Мясные консервы",
            "Рыбные консервы",
            "Яйца",
            "Икра",
            "Молоко",
            "Кефир",
            "Сметана",
            "Йогурт",
            "Творог",
            "Сливки",
            "Замороженный картофель",
            "Рыба замороженная",
            "Рыбные пасты",
            "Лаваш",
            "Лепешка",
            "Сухари",
            "Сушки",
            "Маргарин",
            "Масло растительное",
            "Загуститель",
            "Пчелиный продукт",
            "Каша",
            "Отруби",
            "Рис",
            "Виноград",
            "Дыня",
            "Кешью",
            "Каштаны",
            "Фисташки",
            "Фундук",
            "Лимон",
            "Апельсин",
            "Мандарин",
            "Грейпфрут",
            "Лайм",
            "Помело",
            "Свежая зелень",
            "Травы сушеные",
            "Семена пряные",
            "Корица",
            "Ваниль",
            "Гвоздика",
            "Кардамон",
            "Мускатный орех",
            "Куркума",
            "Шафран",
            "Паприка",
        ]

        created = 0
        existing = 0
        for tag_name in missing_tags:
            tag, is_created = SemanticTag.objects.get_or_create(
                name=tag_name,
                defaults={'tag_type': 'property', 'is_active': True}
            )
            if is_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Создан тег: {tag_name}'))
            else:
                existing += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✨ Создано: {created}, уже существовало: {existing}'
        ))