from django.urls import path
from . import views

app_name = 'repair'

urlpatterns = [
    path('', views.index, name='index'),
    path('diy/', views.diy_list, name='diy_list'),
    path('tools/', views.tools_list, name='tools_list'),
    path('organization/', views.organization, name='organization'),
]