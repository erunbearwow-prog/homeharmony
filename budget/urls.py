from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('shopping/', views.shopping_list, name='shopping_list'),
    path('export/csv/', views.export_csv, name='export_csv'),
]