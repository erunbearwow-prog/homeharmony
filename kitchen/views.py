
from .models import (
    CookingMethod, HomeIngredient,
    RecommendedUtensil, Recipe,
    IngredientPreparation, RecipeStep,
    Cuisine, CookingMethodSubstitution,
    UtensilSubstitution, IngredientCategory, HomeIngredient,
    BrandedIngredient, Ingredient, AbstractIngredient
)
from constants.nutrients import NUTRIENTS_MAP, CATEGORY_NAMES, CATEGORY_ORDER
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.http import JsonResponse
from django.db.models import Count
from django.shortcuts import render
from django.core.paginator import Paginator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404

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


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """API для ингредиентов (только чтение)"""
    queryset = Ingredient.objects.select_related('abstract', 'branded').all()
    serializer_class = IngredientSerializer
    search_fields = ['name', 'abstract__name', 'branded__brand', 'branded__product_name']
    filterset_fields = ['abstract__category', 'is_semi_finished']


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

    print(f'recipe.is_professional = {recipe.is_professional}')

    # ======================= ПРОФЕССИОНАЛЬНЫЙ РЕЖИМ =======================
    if recipe.is_professional:
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
        ingredients = recipe.recipe_ingredients.select_related('ingredient').all()
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


# ======================= ИНГРЕДИЕНТЫ =======================
def ingredient_list(request):
    """Список всех ингредиентов с пагинацией и поиском"""
    # Используем select_related для подгрузки category через abstract
    ingredients = Ingredient.objects.select_related('abstract__category').all()

    # Поиск
    query = request.GET.get('q')
    if query:
        ingredients = ingredients.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(abstract__category__name__icontains=query)
        )

    # Фильтр по категории (через abstract)
    category_id = request.GET.get('category')
    if category_id:
        ingredients = ingredients.filter(abstract__category_id=category_id)

    # Пагинация
    paginator = Paginator(ingredients, 24)
    page_number = request.GET.get('page', 1)  # <-- добавляем default=1
    page_obj = paginator.get_page(page_number)

    # Категории для фильтра
    categories = IngredientCategory.objects.all()

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

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
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
    """Детальная страница ингредиента по ID"""
    ingredient = get_object_or_404(
        Ingredient.objects.select_related('abstract', 'branded', 'abstract__category'),
        pk=pk
    )
    return _render_ingredient_detail(request, ingredient)


def ingredient_detail_by_slug(request, slug):
    """Детальная страница ингредиента по slug"""
    ingredient = get_object_or_404(
        Ingredient.objects.select_related('abstract', 'branded', 'abstract__category'),
        slug=slug
    )
    return _render_ingredient_detail(request, ingredient)


def _render_ingredient_detail(request, ingredient):
    """Общая логика для детальной страницы ингредиента"""

    # Получаем рецепты, использующие этот ингредиент
    home_ingredients = HomeIngredient.objects.filter(
        ingredient=ingredient
    ).select_related('recipe')

    # Если нужны объекты рецептов
    recipes = [hi.recipe for hi in home_ingredients if hi.recipe]

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
    similar_ingredients = Ingredient.objects.filter(
        abstract__category=ingredient.abstract.category  # <-- исправлено
    ).exclude(id=ingredient.id)[:6] if ingredient.abstract and ingredient.abstract.category else []

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


def api_ingredient_detail(request, pk):
    """API для получения данных ингредиента в JSON (для модальных окон)"""
    try:
        ingredient = Ingredient.objects.select_related('abstract__category').get(pk=pk)
        data = {
            'id': ingredient.id,
            'name': ingredient.name,
            'description': ingredient.description,
            'calories': ingredient.calories,
            'protein': ingredient.protein,
            'fat': ingredient.fat,
            'carbohydrates': ingredient.carbohydrates,
            'fiber': ingredient.fiber,
            'sugar': ingredient.sugar,
            'saturated_fat': ingredient.saturated_fat,
            'cholesterol': ingredient.cholesterol,
            'vitamin_c': ingredient.vitamin_c,
            'calcium': ingredient.calcium,
            'iron': ingredient.iron,
            'potassium': ingredient.potassium,
            'sodium': ingredient.sodium,
            'category': ingredient.abstract.category.name if ingredient.abstract and ingredient.abstract.category else None,  # <-- исправлено
            'image_url': ingredient.image.url if ingredient.image else None,
        }
        return JsonResponse(data)
    except Ingredient.DoesNotExist:
        return JsonResponse({'error': 'Ингредиент не найден'}, status=404)


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
        model_fields = {f.name for f in Ingredient._meta.get_fields()}

        defaults = {}
        for key, value in data.items():
            # Исключаем служебные поля и проверяем существование в модели
            if key in model_fields and key not in ['id', 'created_at', 'updated_at', 'last_update']:
                defaults[key] = value

        # Обязательные поля
        defaults['name_ru'] = data.get('name_ru', name)
        defaults['data_source'] = data.get('data_source', 'pbprog.ru')

        ingredient, created = Ingredient.objects.update_or_create(
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
    ingredients = Ingredient.objects.select_related('abstract', 'branded').all()

    search = request.GET.get('search')
    if search:
        ingredients = ingredients.filter(
            Q(name__icontains=search) |
            Q(abstract__name__icontains=search) |
            Q(branded__brand__icontains=search)
        )

    category = request.GET.get('category')
    if category:
        ingredients = ingredients.filter(abstract__category_id=category)

    page = request.GET.get('page', 1)
    paginator = Paginator(ingredients, 30)
    ingredients_page = paginator.get_page(page)

    serializer = IngredientSerializer(ingredients_page, many=True)
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
