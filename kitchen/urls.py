from django.urls import path
from kitchen import views

app_name = 'kitchen'


urlpatterns = [
    path('', views.home, name='home'),
    path('cooking_recipe/', views.recipe, name='cooking_recipe')
]