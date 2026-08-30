from django.urls import path
from kitchen import views

app_name = 'kitchen'

urlpatterns = [
    # ===== API =====
    path('api/method/<int:method_id>/', views.get_method_details, name='get_method_details'),
    path('api/preparation/<int:preparation_id>/', views.get_preparation_details, name='get_preparation_details'),
    path('api/utensil/<int:utensil_id>/', views.get_utensil_details, name='get_utensil_details'),
    path('api/substitutions/<int:recipe_ingredient_id>/', views.get_substitutions, name='get_substitutions'),
    path('api/ingredient/<int:pk>/', views.api_ingredient_detail, name='api_ingredient_detail'),
    path('api/recipes/', views.api_recipe_list, name='api_recipe_list'),
    path('api/recipes/<int:pk>/', views.api_recipe_detail, name='api_recipe_detail'),
path('api/recipes/<int:pk>/nutrition/', views.api_recipe_nutrition, name='api_recipe_nutrition'),
    path('api/recipes/suitable/', views.api_recipe_suitable, name='api_recipe_suitable'),
    path('api/ingredients/', views.api_ingredient_list, name='api_ingredient_list'),
    path('api/cuisines/', views.api_cuisine_list, name='api_cuisine_list'),
    path('api/categories/', views.api_category_list, name='api_category_list'),
    path('api/steps/<int:recipe_id>/', views.get_step_states, name='get_step_states'),
    path('api/update_progress/', views.update_component_progress, name='update_progress'),
    path('api/import-ingredient/', views.import_ingredient, name='import_ingredient'),

    # ===== НОВЫЕ API =====
    path('api/abstract-ingredients/', views.api_abstract_ingredient_list, name='api_abstract_ingredient_list'),
    path('api/abstract-ingredients/<int:pk>/', views.api_abstract_ingredient_detail,
         name='api_abstract_ingredient_detail'),
    path('api/branded-ingredients/', views.api_branded_ingredient_list, name='api_branded_ingredient_list'),
    path('api/branded-ingredients/<int:pk>/', views.api_branded_ingredient_detail,
         name='api_branded_ingredient_detail'),
    path('api/branded-ingredients/by-barcode/', views.api_branded_ingredient_by_barcode,
         name='api_branded_ingredient_by_barcode'),

    # ===== API ДЛЯ АДМИНКИ =====
    path('admin/api/category-children/', views.api_category_children, name='api_category_children'),

    # ===== HTML СТРАНИЦЫ =====
    path('', views.index, name='index'),
    path('cooking_recipe/', views.recipe_old, name='cooking_recipe'),
    path('recipe/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('ingredient/<int:pk>/', views.ingredient_detail, name='ingredient_detail'),
    # path('ingredient/<slug:slug>/', views.ingredient_detail_by_slug, name='ingredient_detail_by_slug'),
    path('utensils/', views.utensil_list, name='utensil_list'),
    path('utensil/<int:utensil_id>/', views.utensil_detail, name='utensil_detail'),
    path('methods/', views.cooking_method_list, name='cooking_method_list'),
    path('method/<int:method_id>/', views.cooking_method_detail, name='cooking_method_detail'),
    path('preparations/', views.preparation_list, name='preparation_list'),
    path('preparation/<int:preparation_id>/', views.preparation_detail, name='preparation_detail'),
    path('cuisine/<slug:slug>/', views.cuisine_detail, name='cuisine_detail'),
# ТТК
    path('ttk/', views.ttk_list, name='ttk_list'),
    path('ttk/<int:pk>/', views.ttk_detail, name='ttk_detail'),

# Сохраненные рецепты
    path('api/save-recipe/', views.save_recipe_variant, name='save_recipe_variant'),
    path('api/saved-recipes/', views.get_saved_recipes, name='get_saved_recipes'),
    path('api/delete-saved-recipe/', views.delete_saved_recipe, name='delete_saved_recipe'),
    path('saved-recipes/', views.saved_recipes_page, name='saved_recipes'),

]