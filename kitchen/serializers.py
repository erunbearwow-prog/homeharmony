# kitchen/serializers.py

from rest_framework import serializers
from .models import (
    Recipe, HomeIngredient,  # ← убрали Ingredient
    RecipeStep, Cuisine, IngredientCategory,
    AbstractIngredient, BrandedIngredient
)

from kitchen.utils import build_utensil_url_map, render_description



class CuisineSerializer(serializers.ModelSerializer):
    """Сериализатор для кухонь мира"""
    parent_name = serializers.ReadOnlyField(source='parent.name')
    child_count = serializers.SerializerMethodField()

    class Meta:
        model = Cuisine
        fields = ['id', 'name', 'slug', 'parent', 'parent_name', 'region',
                  'description', 'child_count', 'created_at']

    def get_child_count(self, obj):
        return obj.children.count()


class IngredientCategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий ингредиентов"""
    parent_name = serializers.ReadOnlyField(source='parent.name')
    level = serializers.ReadOnlyField()

    class Meta:
        model = IngredientCategory
        fields = ['id', 'name', 'parent', 'parent_name', 'level', 'icon', 'sort_order']


class AbstractIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для абстрактных ингредиентов"""

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = AbstractIngredient
        fields = [
            'id',
            'name',
            'name_normalized',
            'description',
            'description_ru',
            'category',
            'category_name',
            'calories',
            'protein',
            'fat',
            'carbohydrates',
            'fiber',
            'sugar',
            'water',
            'ash',
            'starch',
            'vitamin_a',
            'beta_carotene',
            'vitamin_b1',
            'vitamin_b2',
            'vitamin_b3',
            'vitamin_b4',
            'vitamin_b5',
            'vitamin_b6',
            'vitamin_b7',
            'vitamin_b9_folate',
            'vitamin_b12',
            'vitamin_c',
            'vitamin_d',
            'vitamin_e',
            'vitamin_k',
            'potassium',
            'calcium',
            'magnesium',
            'sodium',
            'phosphorus',
            'sulfur',
            'silicon',
            'chlorine',
            'iron',
            'manganese',
            'copper',
            'selenium',
            'zinc',
            'aluminum',
            'boron',
            'vanadium',
            'iodine',
            'cobalt',
            'lithium',
            'molybdenum',
            'nickel',
            'rubidium',
            'fluorine',
            'chromium',
            'saturated_fat',
            'trans_fat',
            'cholesterol',
            'omega_3',
            'omega_6',
            'organic_acids',
            'data_source',
            'fdc_id',
            'image',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class BrandedIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для брендированных продуктов"""

    abstract_name = serializers.CharField(source='abstract.name', read_only=True)
    abstract_id = serializers.IntegerField(source='abstract.id', read_only=True)

    class Meta:
        model = BrandedIngredient
        fields = [
            'id',
            'abstract',
            'abstract_id',
            'abstract_name',
            'brand',
            'product_name',
            'barcode',
            'calories',
            'protein',
            'fat',
            'carbohydrates',
            'price',
            'weight',
            'store',
            'store_url',
            'is_available',
            'last_checked',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_nutrients(self, obj):
        return obj.get_nutrients()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов"""

    display_name = serializers.ReadOnlyField()
    branded_count = serializers.SerializerMethodField()

    class Meta:
        model = AbstractIngredient
        fields = [
            'id',
            'name',
            'display_name',
            'name_normalized',
            'description',
            'description_ru',
            'category',
            'calories',
            'protein',
            'fat',
            'carbohydrates',
            'fiber',
            'sugar',
            'saturated_fat',
            'cholesterol',
            'vitamin_c',
            'calcium',
            'iron',
            'potassium',
            'sodium',
            'image',
            'is_active',
            'created_at',
            'updated_at',
            'branded_count',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_branded_count(self, obj):
        """Количество брендированных версий"""
        return obj.branded_versions.count() if hasattr(obj, 'branded_versions') else 0


class RecipeStepSerializer(serializers.ModelSerializer):
    """Сериализатор для шагов приготовления"""
    cooking_method_name = serializers.ReadOnlyField(source='cooking_method.name')

    class Meta:
        model = RecipeStep
        fields = [
            'id', 'order', 'title', 'instruction', 'duration',
            'temperature', 'recipe_step_image', 'cooking_method',
            'cooking_method_name'
        ]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте (HomeIngredient)"""
    ingredient_name = serializers.ReadOnlyField(source='ingredient.display_name')
    ingredient_calories = serializers.ReadOnlyField(source='ingredient.calories')
    ingredient_protein = serializers.ReadOnlyField(source='ingredient.protein')
    ingredient_fat = serializers.ReadOnlyField(source='ingredient.fat')
    ingredient_carbohydrates = serializers.ReadOnlyField(source='ingredient.carbohydrates')

    class Meta:
        model = HomeIngredient
        fields = [
            'id', 'ingredient', 'ingredient_name', 'quantity', 'unit',
            'notes', 'is_scalable',
            'ingredient_calories', 'ingredient_protein',
            'ingredient_fat', 'ingredient_carbohydrates'
        ]


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов (краткая версия)"""
    cuisine_name = serializers.ReadOnlyField(source='cuisine.name')
    difficulty_display = serializers.ReadOnlyField(source='get_difficulty_display')
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'cuisine', 'cuisine_name', 'difficulty',
            'difficulty_display', 'total_time', 'servings',
            'image', 'image_url', 'calories', 'created_at'
        ]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной страницы рецепта"""
    cuisine_name = serializers.ReadOnlyField(source='cuisine.name')
    difficulty_display = serializers.ReadOnlyField(source='get_difficulty_display')
    steps = RecipeStepSerializer(many=True, read_only=True)
    home_ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    total_nutrition = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'cuisine', 'cuisine_name', 'description',
            'serving_the_dish', 'storage_conditions', 'difficulty',
            'difficulty_display', 'total_time', 'servings',
            'image', 'image_url', 'calories', 'protein', 'fat', 'carbs',
            'author', 'is_professional', 'created_at', 'updated_at',
            'steps', 'home_ingredients', 'total_nutrition'
        ]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_total_nutrition(self, obj):
        """Расчёт общего КБЖУ рецепта"""
        total = {
            'calories': 0,
            'protein': 0,
            'fat': 0,
            'carbohydrates': 0
        }

        for ri in obj.home_ingredients.all():
            ingredient = ri.ingredient
            quantity = ri.quantity or 0
            if ingredient:
                total['calories'] += (ingredient.calories or 0) * quantity / 100
                total['protein'] += (ingredient.protein or 0) * quantity / 100
                total['fat'] += (ingredient.fat or 0) * quantity / 100
                total['carbohydrates'] += (ingredient.carbohydrates or 0) * quantity / 100

        return {k: round(v, 1) for k, v in total.items()}