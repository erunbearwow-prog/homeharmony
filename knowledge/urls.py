from django.urls import path
from . import views

app_name = 'knowledge'

urlpatterns = [
    path('', views.index, name='index'),
    path('encyclopedia/', views.encyclopedia, name='encyclopedia'),
    path('instructions/', views.instructions, name='instructions'),
    path('hacks/', views.hacks_list, name='hacks_list'),
]