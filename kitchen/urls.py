from django.urls import path
from kitchen import views

app_name = 'kitchen'

urlpatterns = [
    # API
    path('api/method/<int:method_id>/', views.get_method_details, name='get_method_details'),
    path('api/preparation/<int:preparation_id>/', views.get_preparation_details, name='get_preparation_details'),
    path('api/utensil/<int:utensil_id>/', views.get_utensil_details, name='get_utensil_details'),
    path('api/substitutions/<int:recipe_ingredient_id>/', views.get_substitutions, name='get_substitutions'),
    path('api/ingredient/<int:pk>/', views.api_ingredient_detail, name='api_ingredient_detail'),

    path('', views.index, name='index'),
    path('cooking_recipe/', views.recipe_old, name='cooking_recipe'),
    path('recipe/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),

    # Страницы ингредиентов
    path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('ingredient/<int:pk>/', views.ingredient_detail, name='ingredient_detail'),  # /ingredient/42/
    path('ingredient/<slug:slug>/', views.ingredient_detail_by_slug, name='ingredient_detail_by_slug'),
    # /ingredient/morkov/

    # Страницы утвари
    path('utensils/', views.utensil_list, name='utensil_list'),
    path('utensil/<int:utensil_id>/', views.utensil_detail, name='utensil_detail'),

    # Страницы методов приготовления
    path('methods/', views.cooking_method_list, name='cooking_method_list'),
    path('method/<int:method_id>/', views.cooking_method_detail, name='cooking_method_detail'),

    # Страницы подготовки продуктов
    path('preparations/', views.preparation_list, name='preparation_list'),
    path('preparation/<int:preparation_id>/', views.preparation_detail, name='preparation_detail'),

    path('api/steps/<int:recipe_id>/', views.get_step_states, name='get_step_states'),

    path('api/update_progress/', views.update_component_progress, name='update_progress'),


]