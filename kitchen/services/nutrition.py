# kitchen/services/nutrition.py

class NutritionCalculator:

    @staticmethod
    def calculate_final_weight(ingredient_name, raw_weight, cooking_method_code):
        """Расчет конечного веса продукта после обработки"""
        try:
            loss_norm = ProductLossNorm.objects.filter(
                product_name__icontains=ingredient_name,
                processing_method__code=cooking_method_code
            ).first()

            if loss_norm:
                if loss_norm.processing_behavior == 'gain' and loss_norm.gain_factor:
                    # Продукт увеличивается в весе
                    return raw_weight * loss_norm.gain_factor
                else:
                    # Продукт теряет вес
                    loss_factor = 1 - (loss_norm.heat_loss_percent / 100)
                    return raw_weight * loss_factor
        except:
            pass
        return raw_weight

    @staticmethod
    def calculate_recipe_nutrition(recipe_id, servings=None, cooking_method_code='boil'):
        """Расчет КБЖУ с учетом потерь/увеличения веса"""
        recipe = Recipe.objects.get(id=recipe_id)
        total_nutrition = {'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0}
        total_final_weight = 0

        for item in recipe.food_items.select_related('ingredient').all():
            if not item.ingredient:
                continue

            raw_weight = item.quantity
            final_weight = NutritionCalculator.calculate_final_weight(
                item.ingredient.name,
                raw_weight,
                cooking_method_code
            )

            total_final_weight += final_weight

            # КБЖУ ингредиента на 100г (исходные данные для сырого продукта)
            calories_100g = item.ingredient.calories or 0
            protein_100g = item.ingredient.protein or 0
            fat_100g = item.ingredient.fat or 0
            carbs_100g = item.ingredient.carbohydrates or 0

            # КБЖУ ингредиента в блюде (сохраняется, даже если вес изменился)
            total_nutrition['calories'] += calories_100g * raw_weight / 100
            total_nutrition['protein'] += protein_100g * raw_weight / 100
            total_nutrition['fat'] += fat_100g * raw_weight / 100
            total_nutrition['carbs'] += carbs_100g * raw_weight / 100

        servings = servings or recipe.servings

        if servings == 0:
            servings = 1

        # Расчет на порцию
        per_serving = {
            'calories': round(total_nutrition['calories'] / servings),
            'protein': round(total_nutrition['protein'] / servings, 1),
            'fat': round(total_nutrition['fat'] / servings, 1),
            'carbs': round(total_nutrition['carbs'] / servings, 1),
            'weight': round(total_final_weight / servings),
        }

        # Расчет на 100г готового блюда
        if total_final_weight > 0:
            per_100g = {
                'calories': round(total_nutrition['calories'] / total_final_weight * 100),
                'protein': round(total_nutrition['protein'] / total_final_weight * 100, 1),
                'fat': round(total_nutrition['fat'] / total_final_weight * 100, 1),
                'carbs': round(total_nutrition['carbs'] / total_final_weight * 100, 1),
            }
        else:
            per_100g = {'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0}

        return {
            'per_serving': per_serving,
            'per_100g': per_100g,
            'total_final_weight': round(total_final_weight),
            'servings': servings
        }