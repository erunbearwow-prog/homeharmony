from django.urls import path
from . import views

app_name = 'seasonal'

urlpatterns = [
    path('', views.index, name='index'),
    path('canning/', views.canning, name='canning'),
    path('garden/', views.garden, name='garden'),
]