# kitchen/management/commands/recalculate_nutrition.py

from django.core.management.base import BaseCommand
from django.db import transaction

from kitchen.models import Recipe
from kitchen.utils.nutrition import recalculate_recipe_nutrition


class Command(BaseCommand):
    help = 'Пересчитывает КБЖУ рецептов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only-empty',
            action='store_true',
            help='Только рецепты с пустым КБЖУ (calories=0 или NULL)'
        )
        parser.add_argument(
            '--recipe-id',
            type=int,
            help='Пересчитать только один рецепт по ID'
        )
        parser.add_argument(
            '--recipe-type',
            choices=['home', 'ttk', 'semi_finished'],
            help='Только рецепты указанного типа'
        )
        parser.add_argument(
            '--semi-first',
            action='store_true',
            default=True,
            help='Сначала пересчитать полуфабрикаты (по умолчанию)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Не сохранять в БД, только показать результат'
        )

    def handle(self, *args, **options):
        qs = Recipe.objects.all()

        # Фильтры
        if options['recipe_id']:
            qs = qs.filter(pk=options['recipe_id'])
        if options['recipe_type']:
            qs = qs.filter(recipe_type=options['recipe_type'])
        if options['only_empty']:
            qs = qs.filter(calories=0)

        # Сортировка: сначала полуфабрикаты, потом остальные
        if options['semi_first']:
            order = {'semi_finished': 0, 'home': 1, 'ttk': 2}
            qs = sorted(qs, key=lambda r: order.get(r.recipe_type, 99))
        else:
            qs = list(qs)

        total = len(qs)
        if total == 0:
            self.stdout.write(self.style.WARNING('Нет рецептов для пересчёта.'))
            return

        self.stdout.write(f"Найдено рецептов: {total}")
        self.stdout.write("")

        success = 0
        errors = 0

        for i, recipe in enumerate(qs, 1):
            try:
                with transaction.atomic():
                    totals = recalculate_recipe_nutrition(recipe)

                c100 = recipe.calories_per_100g or 0
                self.stdout.write(
                    f"[{i}/{total}] ✅ {recipe.recipe_type:13s} | "
                    f"{recipe.title[:40]:40s} | "
                    f"{recipe.calories:>4} ккал/порция | "
                    f"{c100:>6.1f} ккал/100г | "
                    f"вес: {recipe.total_weight or 0} г"
                )
                success += 1

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"[{i}/{total}] ❌ {recipe.title}: {type(e).__name__}: {e}"
                    )
                )
                errors += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Готово. Успешно: {success}, ошибок: {errors}"
        ))