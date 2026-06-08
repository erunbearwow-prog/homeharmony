from django.urls import path
from . import views

app_name = 'cleaning'

urlpatterns = [
    path('', views.index, name='index'),
    path('tasks/', views.task_list, name='task_list'),
    path('checklist/', views.checklist, name='checklist'),
    path('tips/', views.tips_list, name='tips_list'),
    path('schedule/', views.schedule, name='schedule'),
]