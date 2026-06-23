# kitchen/management/commands/move_brands_to_branded.py

from django.core.management.base import BaseCommand
from kitchen.models import AbstractIngredient, BrandedIngredient, Ingredient


class Command(BaseCommand):
    help = 'Переносит брендовые продукты из AbstractIngredient в BrandedIngredient'

    def handle(self, *args, **options):
        # Список брендов для поиска
        brands = ['PIZZA HUT', 'Subway', 'Роллтон', 'Бондюэль', 'Черкизово']

        for brand in brands:
            abstracts = AbstractIngredient.objects.filter(name__icontains=brand)
            count = abstracts.count()
            self.stdout.write(f"Обработка бренда '{brand}': найдено {count} записей")

            for abstract in abstracts:
                # Создаём BrandedIngredient
                branded = BrandedIngredient.objects.create(
                    abstract=None,  # Временно без Abstract
                    brand=brand,
                    product_name=abstract.name,
                    calories=abstract.calories,
                    protein=abstract.protein,
                    fat=abstract.fat,
                    carbohydrates=abstract.carbohydrates,
                )

                # Обновляем Ingredient, чтобы ссылались на BrandedIngredient
                ingredients = Ingredient.objects.filter(abstract=abstract)
                for ing in ingredients:
                    ing.branded = branded
                    ing.abstract = None
                    ing.save()

                # Удаляем AbstractIngredient
                abstract.delete()
                self.stdout.write(f"  ✅ {abstract.name} → BrandedIngredient")

            self.stdout.write(self.style.SUCCESS(f"✅ Бренд '{brand}' обработан"))