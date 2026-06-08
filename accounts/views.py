# accounts/views.py (упрощённая версия без форм)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.http import JsonResponse

def register(request):
    """Регистрация нового пользователя (заглушка)"""
    return render(request, 'accounts/register.html', {'title': 'Регистрация'})

@login_required
def profile(request):
    """Личный кабинет пользователя"""
    return render(request, 'accounts/profile.html', {'title': 'Личный кабинет'})

@login_required
def profile_edit(request):
    """Редактирование профиля"""
    return render(request, 'accounts/profile_edit.html', {'title': 'Редактирование профиля'})

@login_required
def favorites(request):
    """Избранные рецепты"""
    return render(request, 'accounts/favorites.html', {'title': 'Избранное'})

@login_required
def add_to_favorites(request, recipe_id):
    """Добавить рецепт в избранное"""
    return JsonResponse({'status': 'ok', 'message': 'Рецепт добавлен в избранное'})

@login_required
def remove_from_favorites(request, recipe_id):
    """Удалить рецепт из избранного"""
    return JsonResponse({'status': 'ok', 'message': 'Рецепт удалён из избранного'})

@login_required
def user_tasks(request):
    """Список задач пользователя"""
    return render(request, 'accounts/tasks.html', {'title': 'Мои задачи'})

@login_required
def add_task(request):
    """Добавить новую задачу"""
    if request.method == 'POST':
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def toggle_task(request, task_id):
    """Переключить статус выполнения задачи"""
    return JsonResponse({'status': 'ok'})

@login_required
def delete_task(request, task_id):
    """Удалить задачу"""
    return JsonResponse({'status': 'ok'})