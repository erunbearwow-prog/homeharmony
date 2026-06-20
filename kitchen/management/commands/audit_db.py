# kitchen/management/commands/audit_db.py

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count, Q
from kitchen.models import Ingredient, IngredientCategory, Recipe, RecipeIngredient


class Command(BaseCommand):
    help = 'Аудит текущей базы данных перед миграциями'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Исправить найденные проблемы (если возможно)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('🔍 АУДИТ БАЗЫ ДАННЫХ'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # 1. Основная статистика
        self.check_basic_stats()

        # 2. Проверка категорий
        self.check_categories()

        # 3. Проверка дубликатов
        self.check_duplicates()

        # 4. Проверка целостности данных
        self.check_data_integrity()

        # 5. Проверка связей
        self.check_relations()

        # 6. Анализ использования
        self.check_usage()

        # 7. Создание рекомендаций
        self.create_recommendations(options.get('fix', False))

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ Аудит завершен'))

    def check_basic_stats(self):
        """Базовая статистика"""
        self.stdout.write('\n📊 ОСНОВНАЯ СТАТИСТИКА:')
        self.stdout.write(f'  Ингредиентов: {Ingredient.objects.count()}')
        self.stdout.write(f'  Категорий: {IngredientCategory.objects.count()}')
        self.stdout.write(f'  Рецептов: {Recipe.objects.count()}')
        self.stdout.write(f'  Ингредиентов в рецептах: {RecipeIngredient.objects.count()}')

    def check_categories(self):
        """Проверка категорий"""
        self.stdout.write('\n📂 КАТЕГОРИИ:')

        # Ингредиенты без категорий
        without_cat = Ingredient.objects.filter(category__isnull=True)
        if without_cat.exists():
            self.stdout.write(self.style.WARNING(
                f'  ⚠️ Ингредиентов без категории: {without_cat.count()}'
            ))
            # Показываем первые 5
            for ing in without_cat[:5]:
                self.stdout.write(f'    - {ing.name}')
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ Все ингредиенты имеют категории'))

        # Статистика по категориям
        category_stats = IngredientCategory.objects.annotate(
            count=Count('ingredient')
        ).order_by('-count')

        self.stdout.write('\n  Топ категорий:')
        for cat in category_stats[:10]:
            self.stdout.write(f'    - {cat.name}: {cat.count} ингредиентов')

    def check_duplicates(self):
        """Проверка дубликатов"""
        self.stdout.write('\n🔄 ДУБЛИКАТЫ:')

        # Дубликаты по названию
        duplicates = Ingredient.objects.values('name').annotate(
            count=Count('id')
        ).filter(count__gt=1)

        if duplicates.exists():
            self.stdout.write(self.style.WARNING(
                f'  ⚠️ Найдено {duplicates.count()} дубликатов:'
            ))
            for dup in duplicates[:10]:
                self.stdout.write(f'    - "{dup["name"]}" повторяется {dup["count"]} раз')

                # Показываем ID дубликатов
                ids = Ingredient.objects.filter(name=dup['name']).values_list('id', flat=True)
                self.stdout.write(f'      ID: {", ".join(map(str, ids))}')
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ Дубликатов не найдено'))

        # Дубликаты по нормализованному имени
        dup_normalized = Ingredient.objects.values('name_normalized').annotate(
            count=Count('id')
        ).filter(count__gt=1, name_normalized__isnull=False)

        if dup_normalized.exists():
            self.stdout.write(self.style.WARNING(
                f'  ⚠️ Найдено {dup_normalized.count()} дубликатов по нормализованному имени:'
            ))
            for dup in dup_normalized[:5]:
                self.stdout.write(f'    - "{dup["name_normalized"]}" повторяется {dup["count"]} раз')

    def check_data_integrity(self):
        """Проверка целостности данных"""
        self.stdout.write('\n🔧 ЦЕЛОСТНОСТЬ ДАННЫХ:')

        issues = []

        # Проверка КБЖУ
        missing_nutrients = Ingredient.objects.filter(
            Q(calories__isnull=True) |
            Q(protein__isnull=True) |
            Q(fat__isnull=True) |
            Q(carbohydrates__isnull=True)
        )

        if missing_nutrients.exists():
            issues.append(f'  ⚠️ Ингредиентов без полного КБЖУ: {missing_nutrients.count()}')
            # Показываем примеры
            for ing in missing_nutrients[:5]:
                missing = []
                if ing.calories is None: missing.append('калории')
                if ing.protein is None: missing.append('белки')
                if ing.fat is None: missing.append('жиры')
                if ing.carbohydrates is None: missing.append('углеводы')
                self.stdout.write(f'    - {ing.name}: нет {", ".join(missing)}')

        # Проверка невалидных значений
        invalid_values = Ingredient.objects.filter(
            Q(calories__lt=0) |
            Q(protein__lt=0) |
            Q(fat__lt=0) |
            Q(carbohydrates__lt=0)
        )

        if invalid_values.exists():
            issues.append(f'  ⚠️ Ингредиентов с отрицательными значениями КБЖУ: {invalid_values.count()}')
            for ing in invalid_values[:5]:
                self.stdout.write(f'    - {ing.name}: калории={ing.calories}, белки={ing.protein}, жиры={ing.fat}')

        if not issues:
            self.stdout.write(self.style.SUCCESS('  ✅ Все данные корректны'))
        else:
            for issue in issues:
                self.stdout.write(self.style.WARNING(issue))

    def check_relations(self):
        """Проверка связей между моделями"""
        self.stdout.write('\n🔗 СВЯЗИ:')

        # Проверяем RecipeIngredient без ингредиента
        orphan_ri = RecipeIngredient.objects.filter(ingredient__isnull=True)
        if orphan_ri.exists():
            self.stdout.write(self.style.WARNING(
                f'  ⚠️ Записей RecipeIngredient без ингредиента: {orphan_ri.count()}'
            ))

        # Проверяем RecipeIngredient без рецепта
        orphan_ri_recipe = RecipeIngredient.objects.filter(recipe__isnull=True)
        if orphan_ri_recipe.exists():
            self.stdout.write(self.style.WARNING(
                f'  ⚠️ Записей RecipeIngredient без рецепта: {orphan_ri_recipe.count()}'
            ))

        # Проверяем рецепты без ингредиентов
        empty_recipes = Recipe.objects.filter(recipe_ingredients__isnull=True)
        if empty_recipes.exists():
            self.stdout.write(self.style.WARNING(
                f'  ⚠️ Рецептов без ингредиентов: {empty_recipes.count()}'
            ))
            for recipe in empty_recipes[:5]:
                # Используем правильное поле title вместо name
                recipe_title = getattr(recipe, 'title', getattr(recipe, 'name', f'Рецепт #{recipe.id}'))
                self.stdout.write(f'    - {recipe_title} (ID: {recipe.id})')

        # Проверяем ингредиенты, которые не используются в рецептах
        unused_ingredients = Ingredient.objects.filter(recipe_uses__isnull=True)
        if unused_ingredients.exists():
            self.stdout.write(self.style.WARNING(
                f'  ⚠️ Ингредиентов, не используемых в рецептах: {unused_ingredients.count()}'
            ))

    def check_usage(self):
        """Анализ использования"""
        self.stdout.write('\n📈 АНАЛИЗ ИСПОЛЬЗОВАНИЯ:')

        # Самые популярные ингредиенты
        popular = Ingredient.objects.annotate(
            usage_count=Count('recipe_uses')
        ).filter(usage_count__gt=0).order_by('-usage_count')[:10]

        if popular.exists():
            self.stdout.write('\n  🏆 Самые популярные ингредиенты:')
            for ing in popular:
                self.stdout.write(f'    - {ing.name}: используется в {ing.usage_count} рецептах')
        else:
            self.stdout.write('  ℹ️ Нет ингредиентов, используемых в рецептах')

        # Ингредиенты с самым высоким КБЖУ
        high_calorie = Ingredient.objects.filter(
            calories__isnull=False
        ).order_by('-calories')[:5]

        if high_calorie.exists():
            self.stdout.write('\n  🔥 Самые калорийные ингредиенты:')
            for ing in high_calorie:
                self.stdout.write(f'    - {ing.name}: {ing.calories} ккал')

        # Ингредиенты с самым низким КБЖУ
        low_calorie = Ingredient.objects.filter(
            calories__isnull=False,
            calories__gt=0
        ).order_by('calories')[:5]

        if low_calorie.exists():
            self.stdout.write('\n  🥗 Самые низкокалорийные ингредиенты:')
            for ing in low_calorie:
                self.stdout.write(f'    - {ing.name}: {ing.calories} ккал')

    def create_recommendations(self, fix=False):
        """Создание рекомендаций и исправлений"""
        self.stdout.write('\n💡 РЕКОМЕНДАЦИИ:')

        recommendations = []

        # Рекомендация по категориям
        without_cat = Ingredient.objects.filter(category__isnull=True)
        if without_cat.exists():
            recommendations.append(
                f'  - Назначить категории для {without_cat.count()} ингредиентов'
            )

        # Рекомендация по данным
        missing_nutrients = Ingredient.objects.filter(
            Q(calories__isnull=True) |
            Q(protein__isnull=True) |
            Q(fat__isnull=True) |
            Q(carbohydrates__isnull=True)
        )
        if missing_nutrients.exists():
            recommendations.append(
                f'  - Дополнить КБЖУ для {missing_nutrients.count()} ингредиентов ({(missing_nutrients.count() / Ingredient.objects.count() * 100):.1f}%)'
            )

        # Рекомендация по рецептам
        empty_recipes = Recipe.objects.filter(recipe_ingredients__isnull=True)
        if empty_recipes.exists():
            recommendations.append(
                f'  - Добавить ингредиенты в {empty_recipes.count()} рецептов'
            )

        if recommendations:
            for rec in recommendations:
                self.stdout.write(self.style.WARNING(rec))
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ База данных в отличном состоянии!'))