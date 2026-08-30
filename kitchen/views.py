from .models import (
    CookingMethod, HomeIngredient,
    RecommendedUtensil, Recipe,
    IngredientPreparation, RecipeStep,
    Cuisine, CookingMethodSubstitution,
    UtensilSubstitution, IngredientCategory, HomeIngredient,
    BrandedIngredient, AbstractIngredient,
    Product,                    # <-- добавить
    RecipeFoodItem,             # <-- добавить
    ProfessionalIngredient      # <-- добавить
)
from constants.nutrients import NUTRIENTS_MAP, CATEGORY_NAMES, CATEGORY_ORDER
from django.db.models import Count
from django.shortcuts import render
from django.core.paginator import Paginator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .serializers import (
    RecipeListSerializer, RecipeDetailSerializer,
    IngredientSerializer, CuisineSerializer,
    IngredientCategorySerializer, AbstractIngredientSerializer,
    BrandedIngredientSerializer
)


def home(request):
    return render(request, 'kitchen/index.html')

def recipe(request):
    return render(request, 'kitchen/cooking_recipe.html')


class RecipeViewSet(viewsets.ModelViewSet):
    """API для рецептов"""
    queryset = Recipe.objects.all().order_by('-created_at')
    serializer_class = RecipeListSerializer
    filterset_fields = ['cuisine', 'difficulty', 'is_professional']
    search_fields = ['title', 'description', 'author']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RecipeDetailSerializer
        return RecipeListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтр по времени
        time_max = self.request.query_params.get('time_max')
        if time_max:
            queryset = queryset.filter(total_time__lte=int(time_max))

        # Фильтр по сложности
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        return queryset

    @action(detail=False, methods=['get'])
    def suitable(self, request):
        """
        Поиск рецептов по ингредиентам.
        Пример: /api/recipes/suitable/?ingredients=1,2,3
        """
        ingredients_ids = request.query_params.get('ingredients', '').split(',')
        if not ingredients_ids or not ingredients_ids[0]:
            return Response(
                {'error': 'Укажите ингредиенты через запятую: ?ingredients=1,2,3'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Находим рецепты, содержащие хотя бы один из указанных ингредиентов
        recipes = Recipe.objects.filter(
            home_ingredients__ingredient__id__in=ingredients_ids
        ).distinct()

        serializer = RecipeListSerializer(recipes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def nutrition(self, request, pk=None):
        """Расчёт КБЖУ для рецепта"""
        recipe = self.get_object()
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'fat': 0,
            'carbohydrates': 0
        }

        for ri in recipe.home_ingredients.all():
            ingredient = ri.ingredient
            quantity = ri.quantity or 0
            if ingredient:
                total_nutrition['calories'] += (ingredient.calories or 0) * quantity / 100
                total_nutrition['protein'] += (ingredient.protein or 0) * quantity / 100
                total_nutrition['fat'] += (ingredient.fat or 0) * quantity / 100
                total_nutrition['carbohydrates'] += (ingredient.carbohydrates or 0) * quantity / 100

        return Response({k: round(v, 1) for k, v in total_nutrition.items()})


class CuisineViewSet(viewsets.ReadOnlyModelViewSet):
    """API для кухонь мира"""
    queryset = Cuisine.objects.all()
    serializer_class = CuisineSerializer
    search_fields = ['name', 'region']


class IngredientCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API для категорий ингредиентов"""
    queryset = IngredientCategory.objects.all()
    serializer_class = IngredientCategorySerializer
    search_fields = ['name']

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Получить дочерние категории"""
        category = self.get_object()
        children = category.children.all()
        serializer = IngredientCategorySerializer(children, many=True)
        return Response(serializer.data)


class AbstractIngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """API для абстрактных ингредиентов"""
    queryset = AbstractIngredient.objects.select_related('category').all()
    serializer_class = AbstractIngredientSerializer
    search_fields = ['name', 'description']
    filterset_fields = ['category', 'is_active']


class BrandedIngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """API для брендированных продуктов"""
    queryset = BrandedIngredient.objects.select_related('abstract').all()
    serializer_class = BrandedIngredientSerializer
    search_fields = ['brand', 'product_name', 'barcode']
    filterset_fields = ['abstract', 'brand', 'store', 'is_available']

    @action(detail=False, methods=['get'])
    def by_barcode(self, request):
        """Поиск по штрих-коду"""
        barcode = request.query_params.get('barcode')
        if not barcode:
            return Response(
                {'error': 'Укажите штрих-код: ?barcode=123456789'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = BrandedIngredient.objects.get(barcode=barcode)
            serializer = self.get_serializer(product)
            return Response(serializer.data)
        except BrandedIngredient.DoesNotExist:
            return Response(
                {'error': 'Товар не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

def cuisine_detail(request, slug):
    """Детальная страница кухни мира по slug"""
    ingredient = get_object_or_404(Cuisine, slug=slug)
    return _render_quisine_detail(request, ingredient)

def _render_quisine_detail(request, cuisine):
    """Общая логика для детальной страницы ингредиента"""

    # Рецепты с этим ингредиентом
    # cuisine = cuisine.recipe_uses.select_related('recipe').order_by('-recipe__created_at')

    # Пагинация рецептов
    # paginator = Paginator(cuisine, 12)
    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)

    # Параметры возврата (для навигации)
    return_to = request.GET.get('return_to')
    return_title = request.GET.get('return_title')
    return_step = request.GET.get('return_step')
    return_context = request.GET.get('return_context')
    return_mode = request.GET.get('return_mode')
    return_meat = request.GET.get('return_meat')
    return_portions = request.GET.get('return_portions')
    ratio = request.GET.get('ratio')

    # # Похожие ингредиенты (из той же категории)
    # similar_cuisine = Cuisine.objects.filter(
    #     category=cuisine.category
    # ).exclude(id=cuisine.id)[:6]

    context = {
        'cuisine': cuisine,
        # 'page_obj': page_obj,
        # 'similar_ingredients': similar_ingredients,
        'return_to': return_to,
        'return_title': return_title,
        'return_step': return_step,
        'return_context': return_context,
        'return_mode': return_mode,
        'return_meat': return_meat,
        'return_portions': return_portions,
        'ratio': ratio,
        'title': cuisine.name,
    }
    return render(request, 'kitchen/cuisine_detail.html', context)


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
            'description': method.description,
            'scientific_background': method.scientific_background,
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
        'hero_image': 'kitchen/images/recepi_0001.jpg',
    }
    return render(request, 'kitchen/index.html', context)


def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # ========== ОТЛАДКА ==========
    print(f"=== ОТЛАДКА recipe_detail ===")
    print(f"recipe.id: {recipe.id}")
    print(f"recipe.title: {recipe.title}")
    print(f"recipe.recipe_type: {recipe.recipe_type}")
    print(f"recipe.is_professional: {recipe.is_professional}")
    print(f"recipe_type in ['ttk', 'semi_finished']: {recipe.recipe_type in ['ttk', 'semi_finished']}")
    print("=" * 50)

    print(f'recipe.recipe_type = {recipe.recipe_type}')
    print(f'recipe.is_professional = {recipe.is_professional}')

    # ======================= ПРОФЕССИОНАЛЬНЫЙ РЕЖИМ (ТТК) =======================
    # Используем recipe_type для определения режима
    if recipe.recipe_type in ['ttk', 'semi_finished'] or recipe.is_professional:
        # Получаем профессиональные ингредиенты (брутто/нетто)
        pro_ingredients = recipe.pro_ingredients.select_related('ingredient').all()

        # получаем все шаги
        all_steps = recipe.steps.all().order_by('order').select_related(
            'cooking_method',
            'ingredient_preparation',
            'subrecipe'
        ).prefetch_related(
            'recommended_utensils'
        )

        # ========== ОТЛАДКА: проверяем наличие изображений в all_steps ==========
        print(f"🔍 Проверка изображений для ТТК {recipe.id} '{recipe.title}'")
        for step in all_steps:
            if step.recipe_step_image:
                print(f"✅ Шаг {step.id} (порядок {step.order}) ИМЕЕТ изображение: {step.recipe_step_image.url}")
            else:
                print(f"❌ Шаг {step.id} (порядок {step.order}) НЕ ИМЕЕТ изображения")
        print("=" * 50)

        # ========== ФИЛЬТРАЦИЯ: только шаги с вложенными рецептами (Полуфабрикаты) ==========
        steps_with_subrecipes = all_steps.filter(subrecipe__isnull=False)

        # Шаги без subrecipe (не показываем, но можно залогировать при необходимости)
        steps_without_subrecipes = all_steps.filter(subrecipe__isnull=True)

        components = recipe.components.all()
        for c in components:
            print(f'components: {components}')

        # ======================= ПРОГРЕСС ПО ШАГАМ (для проф. режима) =======================
        total_steps = all_steps.count()
        completed_steps = 0

        for step in all_steps:
            step_key = f'step_{recipe_id}_{step.id}'
            if request.session.get(step_key, False):
                completed_steps += 1

        if total_steps > 0:
            current_recipe_progress = int((completed_steps / total_steps) * 100)
        else:
            current_recipe_progress = request.session.get(f'recipe_progress_{recipe_id}', 0)

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

        # Получаем ratio из GET параметров
        ratio = request.GET.get('ratio')
        if ratio:
            try:
                ratio = float(ratio)
            except ValueError:
                ratio = None
        else:
            ratio = None

        # ========== ОТЛАДКА ==========
        print("=== ОТЛАДКА ПАРАМЕТРОВ ВОЗВРАТА (проф. режим) ===")
        print(f"request.GET: {request.GET}")
        print(f"return_to: {return_to}")
        print(f"return_title: {return_title}")
        print(f"return_step: {return_step}")
        print(f"return_context: {return_context}")
        print(f"return_mode: {return_mode}")
        print(f"return_portions: {return_portions}")
        print("=" * 50)

        # ======================= ФОРМИРОВАНИЕ ПАРАМЕТРОВ ДЛЯ ВОЗВРАТА =======================
        return_to_params = ''
        if return_to:
            current_params = []

            if return_mode:
                current_params.append(f'mode={return_mode}')
            if return_portions:
                current_params.append(f'portions={return_portions}')
            if return_meat:
                current_params.append(f'meat={return_meat}')
            if ratio:
                current_params.append(f'ratio={ratio}')

            # Параметры для режима "По продуктам"
            base_ingredient = request.GET.get('base_ingredient')
            base_value = request.GET.get('base_value')
            if base_ingredient and base_value:
                current_params.append(f'base_ingredient={base_ingredient}')
                current_params.append(f'base_value={base_value}')

            if current_params:
                separator = '&' if '?' in return_to else '?'
                return_to_params = f"{separator}{'&'.join(current_params)}"

        if current_recipe_progress > 0 and return_to:
            if '?' in return_to:
                return_to += f'&progress={current_recipe_progress}'
            else:
                return_to += f'?progress={current_recipe_progress}'

        # Изображение основного рецепта для блока возврата
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
            'pro_ingredients': pro_ingredients,
            'steps_with_subrecipes': steps_with_subrecipes,
            'components': components,
            'components_progress': progress_data,
            'current_recipe_progress': current_recipe_progress,
            'return_to': return_to,
            'return_to_params': return_to_params,
            'return_title': return_title,
            'return_step': return_step,
            'return_context': return_context,
            'return_mode': return_mode,
            'return_meat': return_meat,
            'return_portions': return_portions,
            'ratio': ratio,
            'return_image': return_image,
        }


        return render(request, 'kitchen/recipe_pro.html', context)

    # ======================= ОБЫЧНЫЙ РЕЖИМ (любительский) =======================
    # Весь ваш существующий код для обычных рецептов

    print(f'Код обычного режима')
    food_items = recipe.food_items.select_related('ingredient', 'product').all()

    # Для обратной совместимости (если есть старые RecipeIngredient)
    # можно объединить или использовать только новый способ
    if not food_items:
        # Старый способ (для обратной совместимости)
        ingredients = recipe.home_ingredients.select_related('ingredient').all()
        # Конвертируем в формат, похожий на food_items
        food_items = []
        for ri in ingredients:
            food_items.append({
                'id': ri.id,
                'food_name': ri.ingredient.name,
                'food_type': 'ingredient',
                'quantity': ri.quantity,
                'unit': ri.unit,
                'original_id': ri.ingredient.id,
                'original_obj': ri.ingredient,
            })

    steps = recipe.steps.all().order_by('order').select_related(
        'cooking_method',
        'ingredient_preparation',
        'subrecipe'
    ).prefetch_related(
        'recommended_utensils'
    )

    # ========== ОТЛАДКА: проверяем наличие изображений в steps ==========
    print(f"🔍 Проверка изображений для рецепта {recipe.id} '{recipe.title}'")
    for step in steps:
        if step.recipe_step_image:
            print(f"✅ Шаг {step.id} (порядок {step.order}) ИМЕЕТ изображение: {step.recipe_step_image.url}")
        else:
            print(f"❌ Шаг {step.id} (порядок {step.order}) НЕ ИМЕЕТ изображения")
    print("=" * 50)

    components = recipe.components.all()

    total_steps = steps.count()
    completed_steps = 0

    for step in steps:
        step_key = f'step_{recipe_id}_{step.id}'
        if request.session.get(step_key, False):
            completed_steps += 1

    if total_steps > 0:
        current_recipe_progress = int((completed_steps / total_steps) * 100)
    else:
        current_recipe_progress = request.session.get(f'recipe_progress_{recipe_id}', 0)

    request.session[f'recipe_progress_{recipe_id}'] = current_recipe_progress

    progress_data = {}
    for component in components:
        progress_key = f'recipe_progress_{component.id}'
        progress_data[component.id] = request.session.get(progress_key, 0)

    return_to = request.GET.get('return_to')
    return_title = request.GET.get('return_title')
    return_step = request.GET.get('return_step')
    return_context = request.GET.get('return_context')
    return_mode = request.GET.get('return_mode')
    return_meat = request.GET.get('return_meat')
    return_portions = request.GET.get('return_portions')

    if current_recipe_progress > 0 and return_to:
        if '?' in return_to:
            return_to += f'&progress={current_recipe_progress}'
        else:
            return_to += f'?progress={current_recipe_progress}'

    ratio = request.GET.get('ratio')
    if ratio:
        try:
            ratio = float(ratio)
        except ValueError:
            ratio = None
    else:
        ratio = None

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
        'food_items': food_items,
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


def saved_recipes_page(request):
    return render(request, 'kitchen/saved_recipes.html')


def ttk_list(request):
    """Список всех ТТК"""
    ttks = Recipe.objects.filter(
        recipe_type__in=['ttk', 'semi_finished']
    ).order_by('ttk_code', 'title')

    query = request.GET.get('q')
    if query:
        ttks = ttks.filter(
            Q(title__icontains=query) |
            Q(ttk_code__icontains=query) |
            Q(description__icontains=query)
        )

    # Группировка по типу
    ttk_list = ttks.filter(recipe_type='ttk')
    semi_finished_list = ttks.filter(recipe_type='semi_finished')

    context = {
        'ttk_list': ttk_list,
        'semi_finished_list': semi_finished_list,
        'query': query,
        'title': 'Технико-технологические карты',
        'description': 'Сборник ТТК и полуфабрикатов для профессиональной кулинарии'
    }
    return render(request, 'kitchen/ttk_list.html', context)


def ttk_detail(request, pk):
    """Детальная страница ТТК"""
    ttk = get_object_or_404(
        Recipe.objects.filter(recipe_type__in=['ttk', 'semi_finished']),
        pk=pk
    )

    # Рецепты, где используется эта ТТК
    used_in_recipes = Recipe.objects.filter(
        steps__subrecipe=ttk
    ).distinct()

    context = {
        'ttk': ttk,
        'used_in_recipes': used_in_recipes,
        'title': f"ТТК: {ttk.title}",
    }
    return render(request, 'kitchen/ttk_detail.html', context)

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
        recipe_ingredient = HomeIngredient.objects.get(id=recipe_ingredient_id)
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
    except HomeIngredient.DoesNotExist:
        return JsonResponse({'error': 'Ингредиент не найден'}, status=404)


def get_ingredient_substitutions(request, ingredient_id):
    """
    API: получить все возможные замены для ингредиента
    """
    try:
        ingredient = get_object_or_404(AbstractIngredient, pk=ingredient_id)

        substitutions = []
        added_names = set()  # Для предотвращения дублирования

        # ===== 1. ПРИОРИТЕТ 1: РУЧНЫЕ ЗАМЕНЫ (exact) =====
        exact_rules = IngredientSubstitutionRule.objects.filter(
            original_ingredient=ingredient,
            substitution_type='exact',
            is_active=True
        ).select_related('substitute_ingredient', 'substitute_branded')

        for rule in exact_rules:
            if rule.substitute_ingredient:
                name = rule.substitute_ingredient.name
                if name not in added_names:
                    substitutions.append({
                        'id': rule.id,
                        'name': name,
                        'type': 'exact',
                        'ratio': float(rule.ratio),
                        'unit': rule.unit,
                        'priority': rule.priority + 100,  # Максимальный приоритет
                        'notes': rule.notes,
                        'is_branded': False,
                        'is_tag_based': False,
                    })
                    added_names.add(name)

            elif rule.substitute_branded:
                name = f"{rule.substitute_branded.brand} {rule.substitute_branded.product_name}"
                if name not in added_names:
                    substitutions.append({
                        'id': rule.id,
                        'name': name,
                        'type': 'branded',
                        'ratio': float(rule.ratio),
                        'unit': rule.unit,
                        'priority': rule.priority + 90,
                        'notes': rule.notes,
                        'is_branded': True,
                        'is_tag_based': False,
                        'branded_id': rule.substitute_branded.id,
                        'brand': rule.substitute_branded.brand,
                        'product_name': rule.substitute_branded.product_name,
                        'price': float(rule.substitute_branded.price) if rule.substitute_branded.price else None,
                    })
                    added_names.add(name)

        # ===== 2. ПРИОРИТЕТ 2: ГИБРИДНЫЕ ЗАМЕНЫ (hybrid) =====
        hybrid_rules = IngredientSubstitutionRule.objects.filter(
            original_ingredient=ingredient,
            substitution_type='hybrid',
            is_active=True
        )

        for rule in hybrid_rules:
            # Если есть конкретная замена — используем её
            if rule.substitute_ingredient and rule.substitute_ingredient.name not in added_names:
                substitutions.append({
                    'id': rule.id,
                    'name': rule.substitute_ingredient.name,
                    'type': 'hybrid',
                    'ratio': float(rule.ratio),
                    'unit': rule.unit,
                    'priority': rule.priority + 80,
                    'notes': f"{rule.notes} (рекомендовано по тегам)" if rule.notes else "Рекомендовано по тегам",
                    'is_branded': False,
                    'is_tag_based': True,
                    'tags': list(rule.required_tags.values_list('name', flat=True)),
                })
                added_names.add(rule.substitute_ingredient.name)

            elif rule.substitute_branded:
                name = f"{rule.substitute_branded.brand} {rule.substitute_branded.product_name}"
                if name not in added_names:
                    substitutions.append({
                        'id': rule.id,
                        'name': name,
                        'type': 'hybrid',
                        'ratio': float(rule.ratio),
                        'unit': rule.unit,
                        'priority': rule.priority + 80,
                        'notes': rule.notes,
                        'is_branded': True,
                        'is_tag_based': True,
                        'branded_id': rule.substitute_branded.id,
                        'brand': rule.substitute_branded.brand,
                        'product_name': rule.substitute_branded.product_name,
                    })
                    added_names.add(name)

        # ===== 3. ПРИОРИТЕТ 3: АВТОМАТИЧЕСКИЙ ПОДБОР ПО ТЕГАМ (tag_based) =====
        tag_rules = IngredientSubstitutionRule.objects.filter(
            original_ingredient=ingredient,
            substitution_type='tag_based',
            is_active=True
        )

        for rule in tag_rules:
            # Находим ингредиенты по тегам
            candidates = AbstractIngredient.objects.filter(is_active=True).exclude(id=ingredient.id)

            # Обязательные теги
            required = rule.required_tags.all()
            if required:
                for tag in required:
                    candidates = candidates.filter(semantic_tags=tag)

            # Запрещённые теги
            forbidden = rule.forbidden_tags.all()
            if forbidden:
                for tag in forbidden:
                    candidates = candidates.exclude(semantic_tags=tag)

            # Сортируем по количеству совпадений с optional тегами
            optional = rule.optional_tags.all()
            if optional:
                candidates = candidates.annotate(
                    match_count=Count(
                        'semantic_tags',
                        filter=Q(semantic_tags__in=optional)
                    )
                ).order_by('-match_count')

            # Добавляем топ-3 кандидатов
            for candidate in candidates[:3]:
                name = candidate.name
                if name not in added_names:
                    substitutions.append({
                        'id': rule.id,
                        'name': name,
                        'type': 'tag_based',
                        'ratio': float(rule.ratio),
                        'unit': rule.unit,
                        'priority': rule.priority + 50,
                        'notes': f"Подобрано по тегам: {', '.join([t.name for t in rule.required_tags.all()[:3]])}",
                        'is_branded': False,
                        'is_tag_based': True,
                        'match_score': candidate.match_count if optional else 0,
                    })
                    added_names.add(name)

        # ===== 4. ПРИОРИТЕТ 4: ПОХОЖИЕ ИЗ КАТЕГОРИИ (fallback) =====
        if not substitutions and ingredient.category:
            similar = AbstractIngredient.objects.filter(
                category=ingredient.category,
                is_active=True
            ).exclude(id=ingredient.id)[:10]

            for sim in similar:
                if sim.name not in added_names:
                    substitutions.append({
                        'id': None,
                        'name': sim.name,
                        'type': 'similar',
                        'ratio': 1.0,
                        'unit': 'г',
                        'priority': -1,
                        'notes': f'Из категории {ingredient.category.name}',
                        'is_branded': False,
                        'is_tag_based': False,
                    })
                    added_names.add(sim.name)

        # Сортируем по приоритету (убывание)
        substitutions.sort(key=lambda x: x['priority'], reverse=True)

        return JsonResponse({
            'original': {
                'id': ingredient.id,
                'name': ingredient.name,
                'tags': list(ingredient.semantic_tags.values_list('name', flat=True)),
                'category': ingredient.category.name if ingredient.category else None,
            },
            'substitutions': substitutions[:20],
            'total': len(substitutions)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# ======================= ИНГРЕДИЕНТЫ =======================
def ingredient_list(request):
    """Список всех ингредиентов с пагинацией и поиском"""
    # Используем select_related для подгрузки category через abstract
    ingredients = AbstractIngredient.objects.select_related('category').filter(is_active=True)

    # Поиск - ТОЛЬКО ПО НАЗВАНИЮ И СИНОНИМАМ
    query = request.GET.get('q', '').strip()
    if query:
        ingredients = ingredients.filter(
            Q(name__icontains=query) |
            Q(name_normalized__icontains=query) |
            Q(synonyms__icontains=query)  # если добавили поле
        )

    # Фильтр по категории (через abstract)
    category_id = request.GET.get('category','')
    if category_id:
        ingredients = ingredients.filter(category_id=category_id)

    # Пагинация
    paginator = Paginator(ingredients, 24)
    page_number = request.GET.get('page', 1)  # <-- добавляем default=1
    page_obj = paginator.get_page(page_number)

    # Категории для фильтра
    categories = IngredientCategory.objects.all().order_by('name')

    # ========== ФОРМИРУЕМ return_to ДЛЯ ТЕКУЩЕЙ СТРАНИЦЫ ==========
    # Это URL, на который вернется пользователь из карточки ингредиента
    list_return_to = request.get_full_path()

    # Если пользователь уже пришел с return_to (из другого места),
    # то используем его, иначе формируем текущий URL
    existing_return_to = request.GET.get('return_to')
    if existing_return_to:
        # Если пользователь пришел из рецепта или другого места
        current_return_to = existing_return_to
    else:
        # Если пользователь просто открыл список ингредиентов
        current_return_to = list_return_to

    # Параметры возврата (для передачи в детальную страницу)
    return_to = request.GET.get('return_to')
    return_title = request.GET.get('return_title')
    return_step = request.GET.get('return_step')
    return_context = request.GET.get('return_context')
    return_mode = request.GET.get('return_mode')
    return_portions = request.GET.get('return_portions')
    ratio = request.GET.get('ratio')

    # ОТЛАДКА
    print(f"🔍 [DEBUG] category_id: {category_id}")
    print(f"🔍 [DEBUG] category_id type: {type(category_id)}")
    print(f"🔍 [DEBUG] category_id repr: {repr(category_id)}")

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,

        'selected_category_type': str(type(category_id)),  # Для отладки
        'selected_category_repr': repr(category_id),  # Для отладки

        'return_to': current_return_to,  # <-- используем для навигации назад
        'return_title': return_title,
        'return_step': return_step,
        'return_context': return_context,
        'return_mode': return_mode,
        'return_portions': return_portions,
        'ratio': ratio,
        'title': 'Ингредиенты',
        'description': 'База продуктов с пищевой ценностью и использованием в рецептах'
    }
    return render(request, 'kitchen/ingredient_list.html', context)


def ingredient_detail(request, pk):
    ingredient = get_object_or_404(
        AbstractIngredient.objects.select_related('category'),
        pk=pk
    )
    return _render_ingredient_detail(request, ingredient)


# def ingredient_detail_by_slug(request, slug):
#     """Детальная страница ингредиента по slug"""
#     ingredient = get_object_or_404(
#         AbstractIngredient,  # <-- исправили с Ingredient на AbstractIngredient
#         slug=slug
#     )
#     return _render_ingredient_detail(request, ingredient)


# kitchen/views.py

def api_recipe_nutrition(request, pk):
    """API: расчёт КБЖУ для рецепта (для профессионального режима)"""
    try:
        recipe = get_object_or_404(Recipe, pk=pk)

        total_calories = 0
        total_protein = 0
        total_fat = 0
        total_carbs = 0

        # Считаем для профессиональных ингредиентов (брутто/нетто)
        for pro_ing in recipe.pro_ingredients.all():
            ingredient = pro_ing.ingredient
            if ingredient:
                weight = float(pro_ing.net_weight) if pro_ing.net_weight else float(pro_ing.gross_weight)
                factor = weight / 100
                total_calories += (ingredient.calories or 0) * factor
                total_protein += (ingredient.protein or 0) * factor
                total_fat += (ingredient.fat or 0) * factor
                total_carbs += (ingredient.carbohydrates or 0) * factor

        # Считаем для food_items (домашние ингредиенты)
        for item in recipe.food_items.all():
            if item.ingredient:
                factor = item.quantity / 100
                total_calories += (item.ingredient.calories or 0) * factor
                total_protein += (item.ingredient.protein or 0) * factor
                total_fat += (item.ingredient.fat or 0) * factor
                total_carbs += (item.ingredient.carbohydrates or 0) * factor

        servings = recipe.servings or 1

        result = {
            'calories': round(total_calories / servings),
            'protein': round(total_protein / servings, 1),
            'fat': round(total_fat / servings, 1),
            'carbohydrates': round(total_carbs / servings, 1),
        }

        print(f"📊 КБЖУ для рецепта {recipe.id} '{recipe.title}':", result)  # отладка

        return JsonResponse(result)

    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Рецепт не найден'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


def _render_ingredient_detail(request, ingredient):
    """Общая логика для детальной страницы ингредиента"""

    # Получаем рецепты, использующие этот ингредиент
    home_ingredients = HomeIngredient.objects.filter(
        ingredient=ingredient
    ).select_related('recipe')

    # Если нужны объекты рецептов
    recipes = [hi.recipe for hi in home_ingredients if hi.recipe and hi.recipe.id]

    # Если нужны объекты HomeIngredient (с количеством)
    # recipe_uses = home_ingredients

    # Пагинация рецептов
    paginator = Paginator(recipes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Параметры возврата (для навигации)
    return_to = request.GET.get('return_to')
    return_title = request.GET.get('return_title')
    return_step = request.GET.get('return_step')
    return_context = request.GET.get('return_context')
    return_mode = request.GET.get('return_mode')
    return_meat = request.GET.get('return_meat')
    return_portions = request.GET.get('return_portions')
    ratio = request.GET.get('ratio')
    return_image = request.GET.get('return_image')

    # Похожие ингредиенты (из той же категории) - через abstract
    similar_ingredients = AbstractIngredient.objects.filter(
        category=ingredient.category
    ).exclude(id=ingredient.id)[:6] if ingredient.category and ingredient.category else []

    # Подготавливаем данные о питательных веществах
    nutrients_data = []
    for field_name, info in NUTRIENTS_MAP.items():
        value = getattr(ingredient, field_name, None)

        # Проверяем, что значение существует и не равно 0
        if value not in (None, '', 0, 0.0):
            nutrients_data.append({
                'name': info['name'],
                'value': value,
                'unit': info['unit'],
                'category': info['category'],
                'icon': info.get('icon', ''),
                'field': field_name,
            })

    # Группируем по категориям с сохранением порядка
    nutrients_by_category = {}
    for nutrient in nutrients_data:
        category = nutrient['category']
        if category not in nutrients_by_category:
            nutrients_by_category[category] = []
        nutrients_by_category[category].append(nutrient)

    # Сортируем категории согласно CATEGORY_ORDER
    sorted_categories = [cat for cat in CATEGORY_ORDER if cat in nutrients_by_category]

    energy_data = nutrients_by_category.get('energy', [])
    macros_data = nutrients_by_category.get('macros', [])
    fats_detail_data = nutrients_by_category.get('fats_detail', [])
    vitamins_data = nutrients_by_category.get('vitamins', [])
    minerals_data = nutrients_by_category.get('minerals', [])
    other_data = nutrients_by_category.get('other', [])

    context = {
        'ingredient': ingredient,
        'recipes': recipes,  # или 'recipe_uses': home_ingredients
        'page_obj': page_obj,
        'similar_ingredients': similar_ingredients,
        'nutrients_data': nutrients_data,
        'energy_data': energy_data,
        'macros_data': macros_data,
        'fats_detail_data': fats_detail_data,
        'vitamins_data': vitamins_data,
        'minerals_data': minerals_data,
        'other_data': other_data,
        'category_names': CATEGORY_NAMES,
        'nutrients_by_category': nutrients_by_category,
        'sorted_categories': sorted_categories,
        'return_to': return_to,
        'return_title': return_title,
        'return_image': return_image,
        'return_step': return_step,
        'return_context': return_context,
        'return_mode': return_mode,
        'return_meat': return_meat,
        'return_portions': return_portions,
        'ratio': ratio,
        'title': ingredient.name,
    }

    # Добавьте отладочный вывод
    print(f"DEBUG: calories = {ingredient.calories}")
    print(f"DEBUG: protein = {ingredient.protein}")
    print(f"DEBUG: fat = {ingredient.fat}")
    print(f"DEBUG: carbohydrates = {ingredient.carbohydrates}")

    return render(request, 'kitchen/ingredient_detail.html', context)


# kitchen/views.py - исправить api_ingredient_detail

def api_ingredient_detail(request, pk):
    """API для получения данных ингредиента в JSON (для модальных окон)"""
    try:
        ingredient = AbstractIngredient.objects.get(pk=pk)
        data = {
            'id': ingredient.id,
            'name': ingredient.name,
            'description': ingredient.description or '',
            'calories': ingredient.calories or 0,
            'protein': ingredient.protein or 0,
            'fat': ingredient.fat or 0,
            'carbohydrates': ingredient.carbohydrates or 0,
            'fiber': ingredient.fiber or 0,
            'sugar': ingredient.sugar or 0,
            'saturated_fat': ingredient.saturated_fat or 0,
            'cholesterol': ingredient.cholesterol or 0,
            'vitamin_c': ingredient.vitamin_c or 0,
            'calcium': ingredient.calcium or 0,
            'iron': ingredient.iron or 0,
            'potassium': ingredient.potassium or 0,
            'sodium': ingredient.sodium or 0,
            'category': ingredient.category.name if ingredient.category else None,
            'image_url': ingredient.image.url if ingredient.image else None,
        }
        return JsonResponse(data)
    except AbstractIngredient.DoesNotExist:
        return JsonResponse({'error': 'Ингредиент не найден'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


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


@csrf_exempt
@require_http_methods(['POST'])
def import_ingredient(request):
    """API для импорта ингредиента из браузерного расширения"""
    try:
        data = json.loads(request.body)

        name = data.get('name')
        if not name:
            return JsonResponse({'error': 'Название ингредиента обязательно'}, status=400)

        # Автоматически получаем все поля модели
        model_fields = {f.name for f in AbstractIngredient._meta.get_fields()}

        defaults = {}
        for key, value in data.items():
            # Исключаем служебные поля и проверяем существование в модели
            if key in model_fields and key not in ['id', 'created_at', 'updated_at', 'last_update']:
                defaults[key] = value

        # Обязательные поля
        defaults['name_ru'] = data.get('name_ru', name)
        defaults['data_source'] = data.get('data_source', 'pbprog.ru')

        ingredient, created = AbstractIngredient.objects.update_or_create(
            name=name,
            defaults=defaults
        )

        return JsonResponse({
            'status': 'ok',
            'created': created,
            'ingredient_id': ingredient.id,
            'name': ingredient.name
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_child_categories(request):
    """Возвращает дочерние категории для AJAX запроса"""
    parent_id = request.GET.get('parent_id')
    if parent_id:
        categories = IngredientCategory.objects.filter(parent_id=parent_id).order_by('name').values('id', 'name')
        return JsonResponse({'categories': list(categories)})
    return JsonResponse({'categories': []})


def api_recipe_list(request):
    """API: список рецептов с фильтрацией"""
    recipes = Recipe.objects.all().order_by('-created_at')

    # Фильтры
    cuisine = request.GET.get('cuisine')
    if cuisine:
        recipes = recipes.filter(cuisine_id=cuisine)

    difficulty = request.GET.get('difficulty')
    if difficulty:
        recipes = recipes.filter(difficulty=difficulty)

    time_max = request.GET.get('time_max')
    if time_max:
        recipes = recipes.filter(total_time__lte=int(time_max))

    # Поиск
    search = request.GET.get('search')
    if search:
        recipes = recipes.filter(title__icontains=search)

    # Пагинация
    page = request.GET.get('page', 1)
    paginator = Paginator(recipes, 20)
    recipes_page = paginator.get_page(page)

    serializer = RecipeListSerializer(recipes_page, many=True)
    return JsonResponse({
        'results': serializer.data,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': int(page)
    })


def api_recipe_detail(request, pk):
    """API: детали рецепта"""
    try:
        recipe = Recipe.objects.get(pk=pk)
    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Рецепт не найден'}, status=404)

    serializer = RecipeDetailSerializer(recipe)
    return JsonResponse(serializer.data)


def api_recipe_suitable(request):
    """
    API: поиск рецептов по ингредиентам
    Пример: /api/recipes/suitable/?ingredients=1,2,3
    """
    ingredients_ids = request.GET.get('ingredients', '').split(',')
    if not ingredients_ids or not ingredients_ids[0]:
        return JsonResponse(
            {'error': 'Укажите ингредиенты через запятую: ?ingredients=1,2,3'},
            status=400
        )

    recipes = Recipe.objects.filter(
        home_ingredients__ingredient__id__in=ingredients_ids
    ).distinct()

    serializer = RecipeListSerializer(recipes, many=True)
    return JsonResponse({'results': serializer.data})


def api_ingredient_list(request):
    """API: список ингредиентов"""
    ingredients = AbstractIngredient.objects.select_related('category').all()  # <-- убрали 'abstract', 'branded'

    search = request.GET.get('search')
    if search:
        ingredients = ingredients.filter(
            Q(name__icontains=search) |
            Q(category__name__icontains=search)
        )

    category = request.GET.get('category')
    if category:
        ingredients = ingredients.filter(category_id=category)

    page = request.GET.get('page', 1)
    paginator = Paginator(ingredients, 30)
    ingredients_page = paginator.get_page(page)

    serializer = IngredientSerializer(ingredients_page, many=True)  # <-- используем IngredientSerializer
    return JsonResponse({
        'results': serializer.data,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': int(page)
    })


def api_cuisine_list(request):
    """API: список кухонь мира"""
    cuisines = Cuisine.objects.all()
    serializer = CuisineSerializer(cuisines, many=True)
    return JsonResponse({'results': serializer.data})


def api_category_list(request):
    """API: список категорий ингредиентов"""
    categories = IngredientCategory.objects.filter(parent__isnull=True)
    serializer = IngredientCategorySerializer(categories, many=True)
    return JsonResponse({'results': serializer.data})


def api_abstract_ingredient_list(request):
    """API: список абстрактных ингредиентов"""
    abstracts = AbstractIngredient.objects.select_related('category').all()

    search = request.GET.get('search')
    if search:
        abstracts = abstracts.filter(name__icontains=search)

    category = request.GET.get('category')
    if category:
        abstracts = abstracts.filter(category_id=category)

    page = request.GET.get('page', 1)
    paginator = Paginator(abstracts, 30)
    abstracts_page = paginator.get_page(page)

    serializer = AbstractIngredientSerializer(abstracts_page, many=True)
    return JsonResponse({
        'results': serializer.data,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': int(page)
    })


def api_abstract_ingredient_detail(request, pk):
    """API: детали абстрактного ингредиента"""
    try:
        abstract = AbstractIngredient.objects.select_related('category').get(pk=pk)
    except AbstractIngredient.DoesNotExist:
        return JsonResponse({'error': 'Ингредиент не найден'}, status=404)

    serializer = AbstractIngredientSerializer(abstract)
    return JsonResponse(serializer.data)


def api_branded_ingredient_list(request):
    """API: список брендированных продуктов"""
    branded = BrandedIngredient.objects.select_related('abstract').all()

    search = request.GET.get('search')
    if search:
        branded = branded.filter(
            Q(brand__icontains=search) |
            Q(product_name__icontains=search)
        )

    brand = request.GET.get('brand')
    if brand:
        branded = branded.filter(brand__icontains=brand)

    page = request.GET.get('page', 1)
    paginator = Paginator(branded, 30)
    branded_page = paginator.get_page(page)

    serializer = BrandedIngredientSerializer(branded_page, many=True)
    return JsonResponse({
        'results': serializer.data,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': int(page)
    })


def api_branded_ingredient_detail(request, pk):
    """API: детали брендированного продукта"""
    try:
        branded = BrandedIngredient.objects.select_related('abstract').get(pk=pk)
    except BrandedIngredient.DoesNotExist:
        return JsonResponse({'error': 'Продукт не найден'}, status=404)

    serializer = BrandedIngredientSerializer(branded)
    return JsonResponse(serializer.data)


def api_branded_ingredient_by_barcode(request):
    """API: поиск брендированного продукта по штрих-коду"""
    barcode = request.GET.get('barcode')
    if not barcode:
        return JsonResponse(
            {'error': 'Укажите штрих-код: ?barcode=123456789'},
            status=400
        )

    try:
        branded = BrandedIngredient.objects.get(barcode=barcode)
        serializer = BrandedIngredientSerializer(branded)
        return JsonResponse(serializer.data)
    except BrandedIngredient.DoesNotExist:
        return JsonResponse(
            {'error': 'Товар не найден'},
            status=404
        )


def api_category_children(request):
    """Возвращает дочерние категории для AJAX запроса (для админки)"""
    parent_id = request.GET.get('parent_id')
    if parent_id:
        categories = IngredientCategory.objects.filter(parent_id=parent_id).order_by('name').values('id', 'name')
        return JsonResponse({'categories': list(categories)})
    return JsonResponse({'categories': []})


@csrf_exempt
@require_http_methods(['POST'])
def save_recipe_variant(request):
    """
    Сохранить текущий вариант рецепта с заменами
    """
    try:
        data = json.loads(request.body)
        recipe_id = data.get('recipe_id')
        name = data.get('name', '')
        notes = data.get('notes', '')
        is_favorite = data.get('is_favorite', False)

        if not recipe_id:
            return JsonResponse({'error': 'ID рецепта обязателен'}, status=400)

        # Получаем замены из сессии
        session_key = f'recipe_replacements_{recipe_id}'
        replacements = request.session.get(session_key, {})

        if not replacements:
            return JsonResponse({'error': 'Нет замен для сохранения'}, status=400)

        # Получаем оригинальный рецепт
        original_recipe = get_object_or_404(Recipe, id=recipe_id)

        # Пересчитываем КБЖУ с учетом замен
        nutrition = recalculate_nutrition(recipe_id, replacements)

        # Создаем копию рецепта как сохраненный вариант
        saved_recipe = Recipe.objects.create(
            title=name or f"{original_recipe.title} (моя версия)",
            cuisine=original_recipe.cuisine,
            author=request.user.username if request.user.is_authenticated else 'Пользователь',
            description=original_recipe.description,
            difficulty=original_recipe.difficulty,
            servings=original_recipe.servings,
            is_professional=original_recipe.is_professional,
            recipe_type=original_recipe.recipe_type,
            is_saved_variant=True,
            original_recipe=original_recipe,
            saved_replacements=replacements,
            saved_by_session=request.session.session_key,
            saved_by_user=request.user if request.user.is_authenticated else None,
            saved_at=timezone.now(),
            is_favorite=is_favorite,
            saved_notes=notes,
            saved_calories=nutrition['calories'],
            saved_protein=nutrition['protein'],
            saved_fat=nutrition['fat'],
            saved_carbs=nutrition['carbs'],
            image=original_recipe.image,
            video=original_recipe.video,
            plating=original_recipe.plating,
            plating_image=original_recipe.plating_image,
            total_time=original_recipe.total_time,
            calories=nutrition['calories'],
            protein=nutrition['protein'],
            fat=nutrition['fat'],
            carbs=nutrition['carbs'],
        )

        # Копируем шаги (без изменений)
        for original_step in original_recipe.steps.all():
            RecipeStep.objects.create(
                recipe=saved_recipe,
                order=original_step.order,
                title=original_step.title,
                instruction=original_step.instruction,
                duration=original_step.duration,
                temperature=original_step.temperature,
                cooking_method=original_step.cooking_method,
                ingredient_preparation=original_step.ingredient_preparation,
                subrecipe=original_step.subrecipe,
            )
            # Добавляем many-to-many связи для утвари
            if original_step.recommended_utensils.exists():
                saved_step = saved_recipe.steps.get(order=original_step.order)
                saved_step.recommended_utensils.set(original_step.recommended_utensils.all())

        # ======================= КОПИРУЕМ ПРОФЕССИОНАЛЬНЫЕ ИНГРЕДИЕНТЫ (брутто/нетто) =======================
        for original_pro_ing in original_recipe.pro_ingredients.all():
            ProfessionalIngredient.objects.create(
                recipe=saved_recipe,
                ingredient=original_pro_ing.ingredient,
                gross_weight=original_pro_ing.gross_weight,
                net_weight=original_pro_ing.net_weight,
                unit=original_pro_ing.unit,
                loss_factor=original_pro_ing.loss_factor,
                is_base_allowed=original_pro_ing.is_base_allowed
            )

        # ======================= КОПИРУЕМ ИНГРЕДИЕНТЫ (food_items) =======================
        for original_item in original_recipe.food_items.all():
            ing_data = replacements.get(str(original_item.id))

            if ing_data:
                ingredient_id = ing_data.get('ingredient_id')
                product_id = ing_data.get('product_id')
                quantity = ing_data.get('quantity')
                unit = ing_data.get('unit')

                ingredient_obj = None
                product_obj = None

                if ingredient_id:
                    try:
                        ingredient_obj = AbstractIngredient.objects.get(id=ingredient_id)
                    except AbstractIngredient.DoesNotExist:
                        pass
                elif product_id:
                    try:
                        product_obj = Product.objects.get(id=product_id)
                    except Product.DoesNotExist:
                        pass

                RecipeFoodItem.objects.create(
                    recipe=saved_recipe,
                    ingredient=ingredient_obj,
                    product=product_obj,
                    quantity=quantity,
                    unit=unit,
                    notes=original_item.notes
                )
            else:
                RecipeFoodItem.objects.create(
                    recipe=saved_recipe,
                    ingredient=original_item.ingredient,
                    product=original_item.product,
                    quantity=original_item.quantity,
                    unit=original_item.unit,
                    notes=original_item.notes
                )

        return JsonResponse({
            'status': 'ok',
            'saved_recipe_id': saved_recipe.id,
            'saved_recipe_title': saved_recipe.title,
            'message': f'Рецепт "{saved_recipe.title}" сохранен!',
            'nutrition': nutrition
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный JSON'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

def recalculate_nutrition(recipe_id, replacements):
    """
    Пересчитать КБЖУ рецепта с учетом замен
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)

    total_calories = 0
    total_protein = 0
    total_fat = 0
    total_carbs = 0

    # ======================= ПЕРЕСЧЕТ ДЛЯ ПРОФЕССИОНАЛЬНЫХ ИНГРЕДИЕНТОВ (брутто/нетто) =======================
    for pro_ing in recipe.pro_ingredients.all():
        ingredient = pro_ing.ingredient
        if ingredient:
            # Используем нетто вес для расчета
            weight = float(pro_ing.net_weight) if pro_ing.net_weight else float(pro_ing.gross_weight)
            factor = weight / 100
            total_calories += (ingredient.calories or 0) * factor
            total_protein += (ingredient.protein or 0) * factor
            total_fat += (ingredient.fat or 0) * factor
            total_carbs += (ingredient.carbohydrates or 0) * factor

    # ======================= ПЕРЕСЧЕТ ДЛЯ FOOD_ITEMS =======================
    for original_item in recipe.food_items.all():
        ing_data = replacements.get(str(original_item.id))

        if ing_data:
            ingredient_id = ing_data.get('ingredient_id')
            product_id = ing_data.get('product_id')
            quantity = ing_data.get('quantity', 0)

            if ingredient_id:
                try:
                    ingredient = AbstractIngredient.objects.get(id=ingredient_id)
                    calories = ingredient.calories or 0
                    protein = ingredient.protein or 0
                    fat = ingredient.fat or 0
                    carbs = ingredient.carbohydrates or 0
                except AbstractIngredient.DoesNotExist:
                    calories = protein = fat = carbs = 0
            elif product_id:
                try:
                    product = Product.objects.get(id=product_id)
                    # У продуктов пока нет КБЖУ, используем 0
                    calories = protein = fat = carbs = 0
                except Product.DoesNotExist:
                    calories = protein = fat = carbs = 0
            else:
                continue
        else:
            if original_item.ingredient:
                ingredient = original_item.ingredient
                calories = ingredient.calories or 0
                protein = ingredient.protein or 0
                fat = ingredient.fat or 0
                carbs = ingredient.carbohydrates or 0
            else:
                continue
            quantity = original_item.quantity

        # Пересчитываем на 100г
        if quantity and quantity > 0:
            factor = quantity / 100
            total_calories += calories * factor
            total_protein += protein * factor
            total_fat += fat * factor
            total_carbs += carbs * factor

    return {
        'calories': round(total_calories),
        'protein': round(total_protein, 1),
        'fat': round(total_fat, 1),
        'carbs': round(total_carbs, 1),
    }

def get_saved_recipes(request):
    """
    Получить список сохраненных рецептов
    """
    # Для авторизованных пользователей
    if request.user.is_authenticated:
        saved_recipes = Recipe.objects.filter(
            is_saved_variant=True,
            saved_by_user=request.user
        ).order_by('-saved_at')
    else:
        # Для анонимных пользователей - по сессии
        session_key = request.session.session_key
        if not session_key:
            return JsonResponse({'saved_recipes': []})

        saved_recipes = Recipe.objects.filter(
            is_saved_variant=True,
            saved_by_session=session_key
        ).order_by('-saved_at')

    data = []
    for sr in saved_recipes:
        data.append({
            'id': sr.id,
            'title': sr.title,
            'original_recipe_id': sr.original_recipe.id if sr.original_recipe else None,
            'original_recipe_title': sr.original_recipe.title if sr.original_recipe else None,
            'calories': sr.saved_calories,
            'protein': sr.saved_protein,
            'fat': sr.saved_fat,
            'carbs': sr.saved_carbs,
            'saved_at': sr.saved_at.isoformat() if sr.saved_at else None,
            'is_favorite': sr.is_favorite,
            'notes': sr.saved_notes,
        })

    return JsonResponse({'saved_recipes': data})


@csrf_exempt
@require_http_methods(['POST'])
def delete_saved_recipe(request):
    """
    Удалить сохраненный рецепт
    """
    try:
        data = json.loads(request.body)
        recipe_id = data.get('recipe_id')

        if not recipe_id:
            return JsonResponse({'error': 'ID рецепта обязателен'}, status=400)

        # Проверяем, что рецепт принадлежит пользователю или сессии
        recipe = get_object_or_404(Recipe, id=recipe_id, is_saved_variant=True)

        # Проверка прав
        if request.user.is_authenticated:
            if recipe.saved_by_user != request.user:
                return JsonResponse({'error': 'Нет прав на удаление'}, status=403)
        else:
            if recipe.saved_by_session != request.session.session_key:
                return JsonResponse({'error': 'Нет прав на удаление'}, status=403)

        recipe.delete()

        return JsonResponse({'status': 'ok', 'message': 'Рецепт удален'})

    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Рецепт не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
