from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404
import json
from .models import (
    Recipe, RecipeIngredient, RecipeStep, Cuisine,
    CookingMethod, CookingMethodSubstitution,
    IngredientPreparation,
    RecommendedUtensil, UtensilSubstitution
)

def home(request):
    return render(request, 'kitchen/index.html')

def recipe(request):
    return render(request, 'kitchen/cooking_recipe.html')


@require_http_methods(['GET'])
def get_method_details(request, method_id):
    """API для получения деталей метода приготовления"""
    try:
        method = CookingMethod.objects.get(id=method_id)
        # Получаем замены для этого метода
        substitutions = CookingMethodSubstitution.objects.filter(original_method=method).select_related(
            'substitute_method')

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
            'substitutions': [
                {
                    'id': sub.id,
                    'name': sub.substitute_method.name,
                    'reason': sub.reason,
                    'notes': sub.notes,
                } for sub in substitutions
            ]
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
    """API для получения деталей утвари"""
    print('Here is get_utensil_details !!!')
    try:
        utensil = RecommendedUtensil.objects.get(id=utensil_id)
        # Получаем замены для этой утвари
        substitutions = UtensilSubstitution.objects.filter(original_utensil=utensil).select_related(
            'substitute_utensil')

        data = {
            'id': utensil.id,
            'name': utensil.name,
            'description': utensil.description,
            'alternative': utensil.alternative,
            'care_instructions': utensil.care_instructions,
            'substitutions': [
                {
                    'id': sub.id,
                    'name': sub.substitute_utensil.name,
                    'reason': sub.reason,
                    'notes': sub.notes,
                } for sub in substitutions
            ]
        }
        return JsonResponse(data)
    except RecommendedUtensil.DoesNotExist:
        return JsonResponse({'error': 'Utensil not found'}, status=404)


@require_http_methods(['POST'])
@csrf_exempt
def update_component_progress(request):
    """Обновляет прогресс приготовления компонента"""
    try:
        data = json.loads(request.body)
        recipe_id = data.get('recipe_id')
        progress = data.get('progress')

        print(f"DEBUG: update_component_progress - recipe_id={recipe_id}, progress={progress}")  # отладка

        if recipe_id and progress is not None:
            progress_key = f'recipe_progress_{recipe_id}'
            request.session[progress_key] = progress
            request.session.modified = True
            return JsonResponse({'status': 'ok', 'progress': progress})

        return JsonResponse({'error': 'Invalid data'}, status=400)
    except Exception as e:
        print(f"ERROR: {e}")
        return JsonResponse({'error': str(e)}, status=500)

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
    steps = recipe.steps.all().order_by('order').select_related(
        'cooking_method',
        'ingredient_preparation',
        'subrecipe'
    ).prefetch_related(
        'recommended_utensils'
    )

    components = recipe.components.all()

    # ======================= РАСЧЁТ ПРОГРЕССА ПО ШАГАМ =======================
    total_steps = steps.count()
    completed_steps = 0

    # Получаем сохранённые состояния шагов из сессии
    for step in steps:
        step_key = f'step_{recipe_id}_{step.id}'
        if request.session.get(step_key, False):
            completed_steps += 1

    # Вычисляем процент
    if total_steps > 0:
        current_recipe_progress = int((completed_steps / total_steps) * 100)
    else:
        current_recipe_progress = request.session.get(f'recipe_progress_{recipe_id}', 0)

    # Сохраняем прогресс в сессию
    request.session[f'recipe_progress_{recipe_id}'] = current_recipe_progress

    # ======================= ПРОГРЕСС КОМПОНЕНТОВ =======================
    progress_data = {}
    for component in components:
        progress_key = f'recipe_progress_{component.id}'
        progress_data[component.id] = request.session.get(progress_key, 0)

    # ======================= ПАРАМЕТРЫ ВОЗВРАТА =======================
    return_to = request.GET.get('return_to')
    return_title = request.GET.get('return_title')
    return_step = request.GET.get('return_step')
    return_context = request.GET.get('return_context')
    return_mode = request.GET.get('return_mode')
    return_meat = request.GET.get('return_meat')
    return_portions = request.GET.get('return_portions')

    # Добавляем прогресс в параметры возврата
    if current_recipe_progress > 0 and return_to:
        if '?' in return_to:
            return_to += f'&progress={current_recipe_progress}'
        else:
            return_to += f'?progress={current_recipe_progress}'

    # Получаем ratio из GET параметров
    ratio = request.GET.get('ratio')
    if ratio:
        try:
            ratio = float(ratio)
        except ValueError:
            ratio = None
    else:
        ratio = None

    # Получаем изображение основного рецепта для блока возврата
    return_image = None
    if return_to:
        import re
        match = re.search(r'/recipe/(\d+)/', return_to)
        if match:
            parent_recipe_id = match.group(1)
            try:
                parent_recipe = Recipe.objects.get(id=parent_recipe_id)
                if parent_recipe.image:
                    return_image = parent_recipe.image.url
            except Recipe.DoesNotExist:
                pass

    context = {
        'recipe': recipe,
        'ingredients': ingredients,
        'steps': steps,
        'components': components,
        'components_progress': progress_data,
        'current_recipe_progress': current_recipe_progress,
        'return_to': return_to,
        'return_title': return_title,
        'return_step': return_step,
        'return_context': return_context,
        'return_mode': return_mode,
        'return_meat': return_meat,
        'return_portions': return_portions,
        'ratio': ratio,
        'return_image': return_image,
    }

    return render(request, 'kitchen/recipe_detail.html', context)


@require_http_methods(['GET'])
def get_step_states(request, recipe_id):
    """Возвращает состояния всех шагов рецепта"""
    steps = RecipeStep.objects.filter(recipe_id=recipe_id)
    states = {}
    for step in steps:
        step_key = f'step_{recipe_id}_{step.id}'
        states[step.id] = request.session.get(step_key, False)
    return JsonResponse(states)


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


# kitchen/views.py

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import (
    Ingredient, RecommendedUtensil, CookingMethod,
    IngredientPreparation, Recipe, RecipeIngredient
)


# ======================= ИНГРЕДИЕНТЫ =======================

def ingredient_list(request):
    """Список всех ингредиентов"""
    ingredients = Ingredient.objects.annotate(
        recipes_count=Count('recipe_uses')
    ).order_by('name')

    print('========================= ingredient_list =========================')

    # Поиск
    query = request.GET.get('q')
    if query:
        ingredients = ingredients.filter(name__icontains=query)

    # Пагинация
    paginator = Paginator(ingredients, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'title': 'Ингредиенты',
        'description': 'База продуктов с пищевой ценностью и использованием в рецептах'
    }
    print(request)
    return render(request, 'kitchen/ingredient_list.html', context)


# kitchen/views.py

def ingredient_detail(request, ingredient_id):
    """Детальная страница ингредиента с поддержкой возврата в рецепт"""
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    # Получаем параметры возврата (как в recipe_detail)
    return_to = request.GET.get('return_to')
    return_title = request.GET.get('return_title')
    return_step = request.GET.get('return_step')
    return_context = request.GET.get('return_context')
    return_mode = request.GET.get('return_mode')
    return_meat = request.GET.get('return_meat')
    return_portions = request.GET.get('return_portions')
    ratio = request.GET.get('ratio')

    # Рецепты с этим ингредиентом
    recipe_ingredients = RecipeIngredient.objects.filter(
        ingredient=ingredient
    ).select_related('recipe').order_by('-recipe__created_at')

    # Пагинация
    paginator = Paginator(recipe_ingredients, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'ingredient': ingredient,
        'page_obj': page_obj,
        'return_to': return_to,
        'return_title': return_title,
        'return_step': return_step,
        'return_context': return_context,
        'return_mode': return_mode,
        'return_meat': return_meat,
        'return_portions': return_portions,
        'ratio': ratio,
        'title': ingredient.name,
    }
    return render(request, 'kitchen/ingredient_detail.html', context)


# ======================= УТВАРЬ =======================

def utensil_list(request):
    """Список всей утвари"""
    utensils = RecommendedUtensil.objects.annotate(
        recipes_count=Count('steps__recipe', distinct=True)
    ).order_by('name')

    query = request.GET.get('q')
    if query:
        utensils = utensils.filter(name__icontains=query)

    paginator = Paginator(utensils, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'title': 'Кухонная утварь',
        'description': 'Рекомендации по выбору и использованию кухонной утвари'
    }
    return render(request, 'kitchen/utensil_list.html', context)


def utensil_detail(request, utensil_id):
    """Детальная страница утвари"""
    utensil = get_object_or_404(RecommendedUtensil, id=utensil_id)

    # Рецепты, где используется эта утварь
    recipes = Recipe.objects.filter(
        steps__recommended_utensils=utensil
    ).distinct().order_by('-created_at')

    # Замены для этой утвари
    substitutions = utensil.substitutions.all()  # через related_name

    paginator = Paginator(recipes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'utensil': utensil,
        'page_obj': page_obj,
        'substitutions': substitutions,
        'title': utensil.name,
    }
    return render(request, 'kitchen/utensil_detail.html', context)


# ======================= МЕТОДЫ ПРИГОТОВЛЕНИЯ =======================

def cooking_method_list(request):
    """Список методов приготовления"""
    methods = CookingMethod.objects.annotate(
        recipes_count=Count('steps__recipe', distinct=True)
    ).order_by('category', 'name')

    # Группировка по категориям
    categories = {}
    for method in methods:
        cat = method.get_category_display()
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(method)

    context = {
        'categories': categories,
        'title': 'Методы приготовления',
        'description': 'Техники и приёмы приготовления блюд'
    }
    return render(request, 'kitchen/cooking_method_list.html', context)


def cooking_method_detail(request, method_id):
    """Детальная страница метода приготовления"""
    method = get_object_or_404(CookingMethod, id=method_id)

    # Рецепты, где используется этот метод
    recipes = Recipe.objects.filter(
        steps__cooking_method=method
    ).distinct().order_by('-created_at')

    # Замены для этого метода
    substitutions = method.substitutions.all()

    paginator = Paginator(recipes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'method': method,
        'page_obj': page_obj,
        'substitutions': substitutions,
        'title': method.name,
    }
    return render(request, 'kitchen/cooking_method_detail.html', context)


# ======================= ПОДГОТОВКА ПРОДУКТОВ =======================

def preparation_list(request):
    """Список способов подготовки продуктов"""
    preparations = IngredientPreparation.objects.annotate(
        recipes_count=Count('steps__recipe', distinct=True)
    ).order_by('name')

    query = request.GET.get('q')
    if query:
        preparations = preparations.filter(name__icontains=query)

    paginator = Paginator(preparations, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'title': 'Подготовка продуктов',
        'description': 'Техники нарезки, замачивания и другой подготовки ингредиентов'
    }
    return render(request, 'kitchen/preparation_list.html', context)


def preparation_detail(request, preparation_id):
    """Детальная страница способа подготовки"""
    preparation = get_object_or_404(IngredientPreparation, id=preparation_id)

    # Рецепты, где используется этот способ подготовки
    recipes = Recipe.objects.filter(
        steps__ingredient_preparation=preparation
    ).distinct().order_by('-created_at')

    paginator = Paginator(recipes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'preparation': preparation,
        'page_obj': page_obj,
        'title': preparation.name,
    }
    return render(request, 'kitchen/preparation_detail.html', context)