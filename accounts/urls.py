from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    # Профиль
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    # Избранное
    path('favorites/', views.favorites, name='favorites'),
    path('favorites/add/<int:recipe_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/<int:recipe_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    # Задачи
    path('tasks/', views.user_tasks, name='user_tasks'),
    path('tasks/add/', views.add_task, name='add_task'),
    path('tasks/<int:task_id>/toggle/', views.toggle_task, name='toggle_task'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
]