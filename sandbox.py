from kitchen.models import Ingredient, AbstractIngredient

# 1. Проверяем, есть ли ингредиенты с category_id
with_old_category = Ingredient.objects.filter(category__isnull=False).count()
print(f"Ингредиентов со старой категорией: {with_old_category}")

# 2. Переносим категории в abstract
for ing in Ingredient.objects.filter(category__isnull=False).select_related('abstract'):
    if ing.abstract:
        ing.abstract.category = ing.category
        ing.abstract.save()
        print(f"✅ Перенесена категория для: {ing.name}")

# 3. Очищаем старые категории
Ingredient.objects.all().update(category=None)
print("✅ Старые категории очищены")

# 4. Проверяем
remaining = Ingredient.objects.filter(category__isnull=False).count()
print(f"Осталось ингредиентов со старой категорией: {remaining}")