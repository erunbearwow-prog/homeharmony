from django.urls import path
from kitchen import views

app_name = 'kitchen'

urlpatterns = [
    # API
    path('api/method/<int:method_id>/', views.get_method_details, name='get_method_details'),
    path('api/preparation/<int:preparation_id>/', views.get_preparation_details, name='get_preparation_details'),
    path('api/utensil/<int:utensil_id>/', views.get_utensil_details, name='get_utensil_details'),
    path('api/substitutions/<int:recipe_ingredient_id>/', views.get_substitutions, name='get_substitutions'),

    path('', views.index, name='index'),
    path('cooking_recipe/', views.recipe_old, name='cooking_recipe'),
    path('recipe/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),

]