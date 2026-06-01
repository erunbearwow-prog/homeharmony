from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .models import CookingMethod
from django.shortcuts import render, get_object_or_404
from .models import Recipe, RecipeStep, RecipeIngredient

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


from django.shortcuts import render, get_object_or_404
from .models import Recipe, RecipeIngredient, RecipeStep, Cuisine


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
    """Детальная страница рецепта"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    ingredients = recipe.recipe_ingredients.all()
    steps = recipe.steps.all().order_by('order')

    context = {
        'recipe': recipe,
        'ingredients': ingredients,
        'steps': steps,
    }
    return render(request, 'kitchen/recipe_detail.html', context)


def recipe_old(request):
    """Временная заглушка для старого URL (пока не перенесём данные)"""
    # Пока просто редиректим на первый рецепт или показываем заглушку
    first_recipe = Recipe.objects.first()
    if first_recipe:
        from django.shortcuts import redirect
        return redirect('kitchen:recipe_detail', recipe_id=first_recipe.id)
    return render(request, 'kitchen/cooking_recipe.html')