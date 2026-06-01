from django.urls import path
from kitchen import views

app_name = 'kitchen'


urlpatterns = [
    path('', views.index, name='index'),  # ← это главная страница раздела кулинарии
    path('cooking_recipe/', views.recipe_old, name='cooking_recipe'),
    path('recipe/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('api/methods/<str:method_id>/', views.get_method_details, name='get_method_details'),

]