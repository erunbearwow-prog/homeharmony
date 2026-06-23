# kitchen/serializers.py

from rest_framework import serializers
from .models import (
    Recipe, RecipeStep, Ingredient, Cuisine, IngredientCategory,
    AbstractIngredient, BrandedIngredient, HomeIngredient
)


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
    category_name = serializers.ReadOnlyField(source='category.name')
    has_complete_nutrients = serializers.ReadOnlyField()

    class Meta:
        model = AbstractIngredient
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'calories', 'protein', 'fat', 'carbohydrates',
            'fiber', 'sugar', 'image',
            'has_complete_nutrients', 'is_active'
        ]


class BrandedIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для брендированных продуктов"""
    abstract_name = serializers.ReadOnlyField(source='abstract.name')
    price_per_100g = serializers.ReadOnlyField()
    price_per_kg = serializers.ReadOnlyField()
    nutrients = serializers.SerializerMethodField()

    class Meta:
        model = BrandedIngredient
        fields = [
            'id', 'abstract', 'abstract_name', 'brand', 'product_name',
            'barcode', 'calories', 'protein', 'fat', 'carbohydrates',
            'price', 'weight', 'price_per_100g', 'price_per_kg',
            'store', 'store_url', 'is_available', 'nutrients'
        ]

    def get_nutrients(self, obj):
        return obj.get_nutrients()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов (в рецептах)"""
    display_name = serializers.ReadOnlyField()
    category = serializers.ReadOnlyField(source='abstract.category.name')
    abstract_name = serializers.ReadOnlyField(source='abstract.name')
    branded_name = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = [
            'id', 'name', 'display_name', 'abstract', 'abstract_name',
            'branded', 'branded_name', 'category',
            'custom_calories', 'custom_protein', 'custom_fat', 'custom_carbohydrates',
            'calories', 'protein', 'fat', 'carbohydrates',
            'is_semi_finished'
        ]

    def get_branded_name(self, obj):
        if obj.branded:
            return f"{obj.branded.brand} {obj.branded.product_name}"
        return None


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