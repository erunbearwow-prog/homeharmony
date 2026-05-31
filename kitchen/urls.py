from django.urls import path
from kitchen import views

app_name = 'kitchen'


urlpatterns = [
    path('', views.home, name='home'),
    path('cooking_recipe/', views.recipe, name='cooking_recipe'),
    path('api/methods/<str:method_id>/', views.get_method_details, name='get_method_details'),
]