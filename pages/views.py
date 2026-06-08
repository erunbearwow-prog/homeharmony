from django.shortcuts import render
from django.core.paginator import Paginator

def home(request):
    """Главная страница"""
    return render(request, 'pages/home.html', {'title': 'Семейные ценности'})

def about(request):
    """О проекте"""
    return render(request, 'pages/about.html', {'title': 'О проекте'})

def contacts(request):
    """Контакты"""
    return render(request, 'pages/contacts.html', {'title': 'Контакты'})

def blog_list(request):
    """Список статей блога"""
    # Временная заглушка
    posts = []
    return render(request, 'pages/blog_list.html', {'posts': posts, 'title': 'Блог'})

def blog_detail(request, slug):
    """Детальная страница статьи"""
    return render(request, 'pages/blog_detail.html', {'slug': slug, 'title': 'Статья'})

def advertising(request):
    """Реклама"""
    return render(request, 'pages/advertising.html', {'title': 'Реклама'})

def terms(request):
    """Пользовательское соглашение"""
    return render(request, 'pages/terms.html', {'title': 'Пользовательское соглашение'})

def privacy(request):
    """Политика конфиденциальности"""
    return render(request, 'pages/privacy.html', {'title': 'Политика конфиденциальности'})

def offer(request):
    """Оферта для профессионалов"""
    return render(request, 'pages/offer.html', {'title': 'Оферта'})