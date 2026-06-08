from django.urls import path
from . import views

app_name = 'health'

urlpatterns = [
    path('', views.index, name='index'),
    path('first-aid/', views.first_aid, name='first_aid'),
    path('care/', views.care_tips, name='care_tips'),
]