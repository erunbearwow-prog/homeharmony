from django.urls import path
from kitchen import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cooking_recipe/', views.recipe, name='cooking_recipe')
]