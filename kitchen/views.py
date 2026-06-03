from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import Recipe, RecipeIngredient, RecipeStep, Cuisine
from .models import CookingMethod, IngredientPreparation, RecommendedUtensil

# Create your views here.
def home(request):
    return render(request, 'kitchen/index.html')

def recipe(request):
    return render(request, 'kitchen/cooking_recipe.html')

@require_http_methods(['GET'])
def get_method_details(request, method_id):
    """API для получения деталей метода приготовления"""
    try:
        method = CookingMethod.objects.get(id=method_id)
        data = {
            'id': method.id,
            'name': method.name,
            'icon': method.icon,
            'short_description': method.short_description,
            'description': method.description,
            'scientific_background': method.scientific_background,
            'typical_temperature': method.typical_temperature,
            'typical_duration': method.typical_duration,
            'tips': method.tips,
            'common_mistakes': method.common_mistakes,
            'advanced_notes': method.advanced_notes,
        }
        return JsonResponse(data)
    except CookingMethod.DoesNotExist:
        return JsonResponse({'error': 'Method not found'}, status=404)


def get_preparation_details(request, preparation_id):
    try:
        prep = IngredientPreparation.objects.get(id=preparation_id)
        data = {
            'id': prep.id,
            'name': prep.name,
            'description': prep.description,
            'tips': prep.tips,
            'time_factor': prep.time_factor,
        }
        return JsonResponse(data)
    except IngredientPreparation.DoesNotExist:
        return JsonResponse({'error': 'Preparation not found'}, status=404)


def get_utensil_details(request, utensil_id):
    print('Here is get_utensil_details !!!')
    try:
        utensil = RecommendedUtensil.objects.get(id=utensil_id)
        data = {
            'id': utensil.id,
            'name': utensil.name,
            'description': utensil.description,
            'alternative': utensil.alternative,
            'care_instructions': utensil.care_instructions,
        }
        return JsonResponse(data)
    except RecommendedUtensil.DoesNotExist:
        return JsonResponse({'error': 'Utensil not found'}, status=404)


def index(request):
    """Главная страница раздела кулинарии (список рецептов)"""
    recipes = Recipe.objects.all().order_by('-created_at')[:10]
    cuisines = Cuisine.objects.all()

    context = {
        'recipes': recipes,
        'cuisines': cuisines,
    }
    return render(request, 'kitchen/index.html', context)


def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    ingredients = recipe.recipe_ingredients.select_related('ingredient').all()
    steps = recipe.steps.all().order_by('order')

    # Получаем параметры возврата
    return_to = request.GET.get('return_to')
    return_title = request.GET.get('return_title')
    return_step = request.GET.get('return_step')
    return_context = request.GET.get('return_context')
    return_mode = request.GET.get('return_mode')
    return_meat = request.GET.get('return_meat')
    return_portions = request.GET.get('return_portions')

    # Получаем ratio из GET параметров
    ratio = request.GET.get('ratio')
    if ratio:
        try:
            ratio = float(ratio)
        except ValueError:
            ratio = None
    else:
        ratio = None

    context = {
        'recipe': recipe,
        'ingredients': ingredients,
        'steps': steps,
        'return_to': return_to,
        'return_title': return_title,
        'return_step': return_step,
        'return_context': return_context,
        'return_mode': return_mode,
        'return_meat': return_meat,
        'return_portions': return_portions,
        'ratio': ratio,  # ← передаём в шаблон
    }
    print(context)
    return render(request, 'kitchen/recipe_detail.html', context)


def recipe_old(request):
    """Временная заглушка для старого URL (пока не перенесём данные)"""
    # Пока просто редиректим на первый рецепт или показываем заглушку
    first_recipe = Recipe.objects.first()
    if first_recipe:
        from django.shortcuts import redirect
        return redirect('kitchen:recipe_detail', recipe_id=first_recipe.id)
    return render(request, 'kitchen/cooking_recipe.html')


def get_substitutions(request, recipe_ingredient_id):
    """Возвращает список допустимых замен для ингредиента в рецепте"""
    try:
        recipe_ingredient = RecipeIngredient.objects.get(id=recipe_ingredient_id)
        substitutions = recipe_ingredient.substitutions.all()
        data = {
            'original_name': recipe_ingredient.ingredient.name,
            'original_unit': recipe_ingredient.unit,
            'substitutions': [
                {
                    'name': sub.substitute_name,
                    'unit': sub.substitute_unit,
                    'ratio': sub.ratio,
                    'notes': sub.notes,
                } for sub in substitutions
            ]
        }
        return JsonResponse(data)
    except RecipeIngredient.DoesNotExist:
        return JsonResponse({'error': 'Ингредиент не найден'}, status=404)